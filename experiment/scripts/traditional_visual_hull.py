from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from common import OUTPUTS, ensure_dir, image_metrics, load_rgb, save_json, save_rgb, write_metrics


DEFAULT_DATASET_ROOT = OUTPUTS / "dataset" / "nerf_synthetic"
FORMAL_ROOT = OUTPUTS / "formal"


def load_transforms(scene_dir: Path, split: str) -> dict:
    path = scene_dir / f"transforms_{split}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def frame_image_path(scene_dir: Path, frame: dict) -> Path:
    path = scene_dir / frame["file_path"]
    return path if path.suffix else path.with_suffix(".png")


def focal_from_camera_angle(width: int, camera_angle_x: float) -> float:
    return 0.5 * width / np.tan(0.5 * camera_angle_x)


def project_points(points: np.ndarray, c2w: np.ndarray, focal: float, width: int, height: int):
    ones = np.ones((points.shape[0], 1), dtype=np.float32)
    homogeneous = np.concatenate([points, ones], axis=1)
    w2c = np.linalg.inv(c2w).astype(np.float32)
    cam = homogeneous @ w2c.T
    z = -cam[:, 2]
    u = focal * (cam[:, 0] / z) + width * 0.5
    v = -focal * (cam[:, 1] / z) + height * 0.5
    visible = z > 1e-4
    visible &= u >= 0.0
    visible &= u < width
    visible &= v >= 0.0
    visible &= v < height
    return u, v, z, visible


def make_grid(bounds: tuple[float, float], resolution: int) -> np.ndarray:
    lo, hi = bounds
    axis = np.linspace(lo, hi, resolution, dtype=np.float32)
    xx, yy, zz = np.meshgrid(axis, axis, axis, indexing="xy")
    return np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=1)


def load_rgba(path: Path) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32) / 255.0


def carve_visual_hull(
    points: np.ndarray,
    scene_dir: Path,
    transforms: dict,
    max_train_views: int,
    chunk_size: int,
    alpha_threshold: float,
) -> np.ndarray:
    frames = transforms["frames"][:max_train_views]
    sample = load_rgba(frame_image_path(scene_dir, frames[0]))
    height, width = sample.shape[:2]
    focal = focal_from_camera_angle(width, transforms["camera_angle_x"])
    occupied = np.ones(points.shape[0], dtype=bool)

    for start in range(0, points.shape[0], chunk_size):
        end = min(start + chunk_size, points.shape[0])
        chunk = points[start:end]
        keep = np.ones(chunk.shape[0], dtype=bool)
        for frame in frames:
            rgba = load_rgba(frame_image_path(scene_dir, frame))
            alpha = rgba[..., 3]
            c2w = np.asarray(frame["transform_matrix"], dtype=np.float32)
            u, v, _, visible = project_points(chunk, c2w, focal, width, height)
            inside = np.zeros(chunk.shape[0], dtype=bool)
            valid_indices = np.where(visible)[0]
            if valid_indices.size:
                uu = np.clip(np.rint(u[valid_indices]).astype(np.int32), 0, width - 1)
                vv = np.clip(np.rint(v[valid_indices]).astype(np.int32), 0, height - 1)
                inside[valid_indices] = alpha[vv, uu] > alpha_threshold
            keep &= inside
            if not keep.any():
                break
        occupied[start:end] = keep
    return occupied


def colorize_points(
    points: np.ndarray,
    scene_dir: Path,
    transforms: dict,
    max_color_views: int,
    chunk_size: int,
    alpha_threshold: float,
) -> np.ndarray:
    frames = transforms["frames"][:max_color_views]
    sample = load_rgba(frame_image_path(scene_dir, frames[0]))
    height, width = sample.shape[:2]
    focal = focal_from_camera_angle(width, transforms["camera_angle_x"])
    colors = np.zeros((points.shape[0], 3), dtype=np.float32)
    weights = np.zeros(points.shape[0], dtype=np.float32)

    for frame in frames:
        rgba = load_rgba(frame_image_path(scene_dir, frame))
        rgb = rgba[..., :3] * rgba[..., 3:4] + (1.0 - rgba[..., 3:4])
        alpha = rgba[..., 3]
        c2w = np.asarray(frame["transform_matrix"], dtype=np.float32)
        camera_origin = c2w[:3, 3]

        for start in range(0, points.shape[0], chunk_size):
            end = min(start + chunk_size, points.shape[0])
            chunk = points[start:end]
            u, v, z, visible = project_points(chunk, c2w, focal, width, height)
            valid_indices = np.where(visible)[0]
            if not valid_indices.size:
                continue
            uu = np.clip(np.rint(u[valid_indices]).astype(np.int32), 0, width - 1)
            vv = np.clip(np.rint(v[valid_indices]).astype(np.int32), 0, height - 1)
            alpha_ok = alpha[vv, uu] > alpha_threshold
            if not alpha_ok.any():
                continue
            valid_indices = valid_indices[alpha_ok]
            uu = uu[alpha_ok]
            vv = vv[alpha_ok]
            distance = np.linalg.norm(chunk[valid_indices] - camera_origin[None, :], axis=1)
            view_weight = 1.0 / np.maximum(distance, 1e-3)
            global_indices = start + valid_indices
            colors[global_indices] += rgb[vv, uu] * view_weight[:, None]
            weights[global_indices] += view_weight

    valid = weights > 0.0
    colors[valid] /= weights[valid, None]
    colors[~valid] = 1.0
    return np.clip(colors, 0.0, 1.0)


def render_points(
    points: np.ndarray,
    colors: np.ndarray,
    c2w: np.ndarray,
    focal: float,
    width: int,
    height: int,
    radius: int,
) -> np.ndarray:
    u, v, z, visible = project_points(points, c2w, focal, width, height)
    image = np.ones((height, width, 3), dtype=np.float32)
    zbuf = np.full((height, width), np.inf, dtype=np.float32)
    indices = np.where(visible)[0]
    order = indices[np.argsort(z[indices])[::-1]]

    for idx in order:
        px = int(round(u[idx]))
        py = int(round(v[idx]))
        pz = z[idx]
        color = colors[idx]
        for dy in range(-radius, radius + 1):
            yy = py + dy
            if yy < 0 or yy >= height:
                continue
            for dx in range(-radius, radius + 1):
                xx = px + dx
                if xx < 0 or xx >= width:
                    continue
                if pz < zbuf[yy, xx]:
                    zbuf[yy, xx] = pz
                    image[yy, xx] = color
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description="Traditional explicit visual-hull point splatting baseline for NeRF Synthetic.")
    parser.add_argument("--scene", default="lego")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--resolution", type=int, default=96)
    parser.add_argument("--bounds", nargs=2, type=float, default=(-1.6, 1.6))
    parser.add_argument("--max-train-views", type=int, default=32)
    parser.add_argument("--max-color-views", type=int, default=48)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--chunk-size", type=int, default=200000)
    parser.add_argument("--alpha-threshold", type=float, default=0.2)
    parser.add_argument("--radius", type=int, default=2)
    args = parser.parse_args()

    scene_dir = args.dataset_root / args.scene
    train_transforms = load_transforms(scene_dir, "train")
    test_transforms = load_transforms(scene_dir, "test")
    out_dir = FORMAL_ROOT / args.scene / "traditional_visual_hull"
    gt_dir = FORMAL_ROOT / args.scene / "gt"
    ensure_dir(out_dir)

    sample = load_rgba(frame_image_path(scene_dir, test_transforms["frames"][0]))
    height, width = sample.shape[:2]
    focal = focal_from_camera_angle(width, test_transforms["camera_angle_x"])

    t0 = time.perf_counter()
    grid = make_grid(tuple(args.bounds), args.resolution)
    occupied = carve_visual_hull(
        grid,
        scene_dir,
        train_transforms,
        args.max_train_views,
        args.chunk_size,
        args.alpha_threshold,
    )
    points = grid[occupied]
    colors = colorize_points(
        points,
        scene_dir,
        train_transforms,
        args.max_color_views,
        args.chunk_size,
        args.alpha_threshold,
    )
    build_seconds = time.perf_counter() - t0

    rows = []
    render_times = []
    for i, frame in enumerate(test_transforms["frames"][: args.limit]):
        c2w = np.asarray(frame["transform_matrix"], dtype=np.float32)
        t1 = time.perf_counter()
        pred = render_points(points, colors, c2w, focal, width, height, args.radius)
        render_seconds = time.perf_counter() - t1
        render_times.append(render_seconds)
        save_rgb(out_dir / f"pred_{i:03d}.png", pred)
        gt = load_rgb(gt_dir / f"gt_{i:03d}.png")
        row = {"method": "traditional_visual_hull", "view": i, "render_seconds": render_seconds}
        row.update(image_metrics(pred, gt))
        rows.append(row)

    write_metrics(out_dir / "metrics.json", rows)
    summary = {
        "method": "traditional_visual_hull",
        "grid_resolution": args.resolution,
        "points": int(points.shape[0]),
        "build_seconds": build_seconds,
        "mean_render_seconds": float(np.mean(render_times)),
        "mean_psnr": float(np.mean([r["psnr"] for r in rows])),
        "mean_ssim": float(np.mean([r["ssim"] for r in rows])),
    }
    save_json(out_dir / "summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
