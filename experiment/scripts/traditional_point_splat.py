from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from common import DATASET, OUTPUTS, ensure_dir, image_metrics, load_json, load_rgb, make_rays, save_rgb, write_metrics


OUT = OUTPUTS / "traditional_point_splat"


def backproject_point_cloud(meta, stride=1):
    points = []
    colors = []
    width = meta["width"]
    height = meta["height"]
    fov = meta["fov_degrees"]
    for item in meta["train"]:
        rgb = load_rgb(DATASET / "train" / item["rgb"])
        depth = np.load(DATASET / "train" / item["depth"])
        camera = {k: np.asarray(v, dtype=np.float32) for k, v in item["camera"].items()}
        origins, dirs = make_rays(camera, width, height, fov)
        mask = depth > 0.0
        mask[::stride, ::stride] &= True
        sample = np.zeros_like(mask)
        sample[::stride, ::stride] = True
        mask &= sample
        pts = origins[mask] + dirs[mask] * depth[mask, None]
        points.append(pts)
        colors.append(rgb[mask])
    return np.concatenate(points, axis=0), np.concatenate(colors, axis=0)


def render_points(points, colors, camera, width, height, fov, radius=1):
    f = 0.5 * width / np.tan(np.deg2rad(fov) * 0.5)
    rel = points - camera["origin"][None, :]
    x = rel @ camera["right"]
    y = rel @ camera["up"]
    z = rel @ camera["forward"]
    visible = z > 0.05
    u = (f * x / z + width * 0.5).astype(np.int32)
    v = (height * 0.5 - f * y / z).astype(np.int32)
    visible &= (u >= -radius) & (u < width + radius) & (v >= -radius) & (v < height + radius)

    order = np.argsort(z[visible])[::-1]
    uu = u[visible][order]
    vv = v[visible][order]
    zz = z[visible][order]
    cc = colors[visible][order]

    _, dirs = make_rays(camera, width, height, fov)
    image = np.zeros((height, width, 3), dtype=np.float32)
    image[..., 0] = 0.56 + 0.18 * np.clip(dirs[..., 1], 0.0, 1.0)
    image[..., 1] = 0.66 + 0.14 * np.clip(dirs[..., 1], 0.0, 1.0)
    image[..., 2] = 0.82 + 0.10 * np.clip(dirs[..., 1], 0.0, 1.0)
    zbuf = np.full((height, width), np.inf, dtype=np.float32)
    valid = np.zeros((height, width), dtype=bool)
    for px, py, pz, col in zip(uu, vv, zz, cc):
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
                    image[yy, xx] = col
                    valid[yy, xx] = True
    return image, valid


def main():
    ensure_dir(OUT)
    meta = load_json(DATASET / "metadata.json")
    t0 = time.perf_counter()
    points, colors = backproject_point_cloud(meta)
    build_seconds = time.perf_counter() - t0

    rows = []
    render_times = []
    for i, item in enumerate(meta["test"]):
        camera = {k: np.asarray(v, dtype=np.float32) for k, v in item["camera"].items()}
        gt = load_rgb(DATASET / "test" / item["rgb"])
        t1 = time.perf_counter()
        pred, valid = render_points(points, colors, camera, meta["width"], meta["height"], meta["fov_degrees"])
        render_seconds = time.perf_counter() - t1
        render_times.append(render_seconds)
        save_rgb(OUT / f"pred_{i:03d}.png", pred)
        row = {"method": "traditional_point_splat", "view": i, "render_seconds": render_seconds}
        row.update(image_metrics(pred, gt))
        rows.append(row)

    write_metrics(OUT / "metrics.json", rows)
    summary = {
        "method": "traditional_point_splat",
        "points": int(points.shape[0]),
        "build_seconds": build_seconds,
        "mean_render_seconds": float(np.mean(render_times)),
        "mean_psnr": float(np.mean([r["psnr"] for r in rows])),
        "mean_ssim": float(np.mean([r["ssim"] for r in rows])),
    }
    from common import save_json

    save_json(OUT / "summary.json", summary)
    print(f"Traditional point splat done: {summary}")


if __name__ == "__main__":
    main()
