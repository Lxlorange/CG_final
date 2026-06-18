from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


DEFAULT_PARAM_ROOT = Path("experiment/outputs/llm_camera/paths")
DEFAULT_CAMERA_ROOT = Path("experiment/outputs/llm_camera/camera_paths")
DEFAULT_OUT = Path("experiment/outputs/llm_camera/summary.json")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def as_matrix(camera_to_world) -> np.ndarray:
    arr = np.asarray(camera_to_world, dtype=np.float64)
    if arr.shape == (16,):
        return arr.reshape(4, 4)
    if arr.shape == (4, 4):
        return arr
    raise ValueError(f"Unsupported camera_to_world shape: {arr.shape}")


def validate_params(params: dict) -> tuple[bool, list[str]]:
    errors = []
    if params.get("trajectory_type") not in {"orbit", "dolly", "pan", "tilt", "orbit_dolly"}:
        errors.append("invalid_trajectory_type")
    for key in ["num_frames", "radius_start", "radius_end", "elevation_start_deg", "elevation_end_deg", "azimuth_start_deg", "azimuth_end_deg", "fov_deg"]:
        if key not in params:
            errors.append(f"missing_{key}")
    try:
        n = int(params.get("num_frames", 0))
        if not 2 <= n <= 180:
            errors.append("num_frames_out_of_range")
        for key in ["radius_start", "radius_end"]:
            v = float(params.get(key, -999))
            if not 2.5 <= v <= 6.0:
                errors.append(f"{key}_out_of_range")
        for key in ["elevation_start_deg", "elevation_end_deg"]:
            v = float(params.get(key, -999))
            if not -20.0 <= v <= 60.0:
                errors.append(f"{key}_out_of_range")
        fov = float(params.get("fov_deg", -999))
        if not 35.0 <= fov <= 70.0:
            errors.append("fov_out_of_range")
    except (TypeError, ValueError):
        errors.append("numeric_parse_failed")
    look_at = params.get("look_at")
    if not isinstance(look_at, list) or len(look_at) != 3:
        errors.append("invalid_look_at")
    return not errors, errors


def camera_metrics(camera_path: dict) -> dict:
    cams = camera_path.get("camera_path", [])
    if len(cams) < 2:
        return {"trajectory_continuity": 0.0, "target_keep_score": 0.0, "max_step": None, "mean_step": None}
    mats = np.asarray([as_matrix(cam["camera_to_world"]) for cam in cams], dtype=np.float64)
    positions = mats[:, :3, 3]
    steps = np.linalg.norm(np.diff(positions, axis=0), axis=1)
    mean_step = float(np.mean(steps))
    max_step = float(np.max(steps))
    continuity = float(max(0.0, 1.0 - max_step / 1.5))

    target = np.asarray(camera_path.get("metadata", {}).get("look_at", [0.0, 0.0, 0.0]), dtype=np.float64)
    # The generated camera path stores -Z as forward.
    forward = -mats[:, :3, 2]
    to_target = target[None, :] - positions
    to_target /= np.maximum(np.linalg.norm(to_target, axis=1, keepdims=True), 1e-8)
    cos = np.sum(forward * to_target, axis=1)
    target_keep = float(np.mean(cos > 0.98))
    return {
        "trajectory_continuity": continuity,
        "target_keep_score": target_keep,
        "max_step": max_step,
        "mean_step": mean_step,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate rule/LLM camera trajectory JSON and generated camera paths.")
    parser.add_argument("--param-root", type=Path, default=DEFAULT_PARAM_ROOT)
    parser.add_argument("--camera-root", type=Path, default=DEFAULT_CAMERA_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = []
    param_files = sorted(p for p in args.param_root.rglob("*.json") if p.name != "manifest.json")
    for param_file in param_files:
        try:
            params = load_json(param_file)
            parse_ok = True
            valid, errors = validate_params(params)
        except Exception as exc:
            params = {}
            parse_ok = False
            valid = False
            errors = [type(exc).__name__]

        source = params.get("source", param_file.parent.name)
        task_id = params.get("task_id", param_file.stem)
        camera_file = args.camera_root / source / f"{param_file.stem}.json"
        camera_ok = camera_file.exists()
        metrics = {}
        if camera_ok:
            metrics = camera_metrics(load_json(camera_file))
        rows.append(
            {
                "task_id": task_id,
                "source": source,
                "param_file": str(param_file),
                "camera_file": str(camera_file) if camera_ok else None,
                "json_parse_ok": parse_ok,
                "param_valid": valid,
                "errors": errors,
                **metrics,
            }
        )

    def rate(key: str) -> float:
        return sum(1 for r in rows if r.get(key)) / max(len(rows), 1)

    by_source = {}
    for source in sorted({r["source"] for r in rows}):
        subset = [r for r in rows if r["source"] == source]
        by_source[source] = {
            "count": len(subset),
            "json_parse_rate": sum(1 for r in subset if r["json_parse_ok"]) / max(len(subset), 1),
            "param_valid_rate": sum(1 for r in subset if r["param_valid"]) / max(len(subset), 1),
            "camera_path_rate": sum(1 for r in subset if r.get("camera_file")) / max(len(subset), 1),
            "mean_continuity": float(np.mean([r.get("trajectory_continuity", 0.0) for r in subset])) if subset else 0.0,
            "mean_target_keep": float(np.mean([r.get("target_keep_score", 0.0) for r in subset])) if subset else 0.0,
        }

    summary = {
        "overall": {
            "count": len(rows),
            "json_parse_rate": rate("json_parse_ok"),
            "param_valid_rate": rate("param_valid"),
        },
        "by_source": by_source,
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
