from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


DEFAULT_IN_ROOT = Path("experiment/outputs/llm_camera/paths")
DEFAULT_OUT_ROOT = Path("experiment/outputs/llm_camera/camera_paths")


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / max(n, 1e-8)


def look_at_c2w(origin: np.ndarray, target: np.ndarray) -> np.ndarray:
    # Nerfstudio camera paths use OpenGL-style camera coordinates: camera looks along -Z.
    forward = normalize(target - origin)
    world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    right = normalize(np.cross(forward, world_up))
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    up = normalize(np.cross(right, forward))
    c2w = np.eye(4, dtype=np.float64)
    c2w[:3, 0] = right
    c2w[:3, 1] = up
    c2w[:3, 2] = -forward
    c2w[:3, 3] = origin
    return c2w


def camera_position(radius: float, azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    x = radius * math.cos(el) * math.sin(az)
    y = radius * math.sin(el)
    z = radius * math.cos(el) * math.cos(az)
    return np.array([x, y, z], dtype=np.float64)


def sanitize(params: dict) -> dict:
    out = dict(params)
    out["num_frames"] = int(clamp(float(out.get("num_frames", 60)), 2, 180))
    out["radius_start"] = clamp(float(out.get("radius_start", 4.0)), 2.5, 6.0)
    out["radius_end"] = clamp(float(out.get("radius_end", out["radius_start"])), 2.5, 6.0)
    out["elevation_start_deg"] = clamp(float(out.get("elevation_start_deg", 20.0)), -20.0, 60.0)
    out["elevation_end_deg"] = clamp(float(out.get("elevation_end_deg", out["elevation_start_deg"])), -20.0, 60.0)
    out["azimuth_start_deg"] = clamp(float(out.get("azimuth_start_deg", 0.0)), -180.0, 180.0)
    out["azimuth_end_deg"] = clamp(float(out.get("azimuth_end_deg", out["azimuth_start_deg"])), -180.0, 540.0)
    out["fov_deg"] = clamp(float(out.get("fov_deg", 50.0)), 35.0, 70.0)
    look_at = out.get("look_at", [0.0, 0.0, 0.0])
    if not isinstance(look_at, list) or len(look_at) != 3:
        look_at = [0.0, 0.0, 0.0]
    out["look_at"] = [float(x) for x in look_at]
    return out


def make_camera_path(params: dict, render_width: int, render_height: int, matrix_format: str) -> dict:
    params = sanitize(params)
    n = params["num_frames"]
    target = np.asarray(params["look_at"], dtype=np.float64)
    cameras = []
    for i in range(n):
        t = 0.0 if n == 1 else i / (n - 1)
        radius = (1.0 - t) * params["radius_start"] + t * params["radius_end"]
        azimuth = (1.0 - t) * params["azimuth_start_deg"] + t * params["azimuth_end_deg"]
        elevation = (1.0 - t) * params["elevation_start_deg"] + t * params["elevation_end_deg"]
        origin = camera_position(radius, azimuth, elevation)
        c2w = look_at_c2w(origin, target)
        if matrix_format == "flat":
            camera_to_world = c2w.reshape(-1).tolist()
        elif matrix_format == "nested":
            camera_to_world = c2w.tolist()
        else:
            raise ValueError(f"Unsupported matrix format: {matrix_format}")
        cameras.append(
            {
                "camera_to_world": camera_to_world,
                "fov": params["fov_deg"],
                "aspect": render_width / render_height,
            }
        )
    return {
        "camera_type": "perspective",
        "render_height": render_height,
        "render_width": render_width,
        "seconds": max(2.0, n / 30.0),
        "camera_path": cameras,
        "metadata": {
            "source": params.get("source", "unknown"),
            "task_id": params.get("task_id", ""),
            "trajectory_type": params.get("trajectory_type", ""),
            "motion_summary": params.get("motion_summary", ""),
            "input_text": params.get("input_text", ""),
            "look_at": params.get("look_at", [0.0, 0.0, 0.0]),
        },
    }


def convert_file(path: Path, out_dir: Path, render_width: int, render_height: int, matrix_format: str) -> Path:
    params = json.loads(path.read_text(encoding="utf-8"))
    camera_path = make_camera_path(params, render_width, render_height, matrix_format)
    source = params.get("source", path.parent.name)
    out_path = out_dir / source / f"{path.stem}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(camera_path, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert trajectory parameter JSON files to Nerfstudio camera-path JSON files.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_IN_ROOT)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--render-width", type=int, default=800)
    parser.add_argument("--render-height", type=int, default=800)
    parser.add_argument("--matrix-format", choices=("flat", "nested"), default="flat")
    args = parser.parse_args()

    paths = sorted(p for p in args.input_root.rglob("*.json") if p.name != "manifest.json")
    written = []
    for path in paths:
        written.append(convert_file(path, args.out_root, args.render_width, args.render_height, args.matrix_format))
    print(f"Wrote {len(written)} camera path files to {args.out_root}")


if __name__ == "__main__":
    main()
