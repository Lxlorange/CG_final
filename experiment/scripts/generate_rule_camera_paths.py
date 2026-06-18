from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_TASKS = Path("experiment/llm_camera/tasks/camera_tasks.json")
DEFAULT_OUT = Path("experiment/outputs/llm_camera/paths/rule")


def make_params(task_id: str, text: str, expected_type: str = "") -> dict:
    base = {
        "scene": "lego",
        "num_frames": 60,
        "radius_start": 4.0,
        "radius_end": 4.0,
        "elevation_start_deg": 20.0,
        "elevation_end_deg": 20.0,
        "azimuth_start_deg": 0.0,
        "azimuth_end_deg": 0.0,
        "look_at": [0.0, 0.0, 0.0],
        "fov_deg": 50.0,
        "source": "rule",
        "task_id": task_id,
        "input_text": text,
    }

    if expected_type == "orbit" or "一圈" in text or "旋转" in text:
        base.update(
            {
                "trajectory_type": "orbit",
                "azimuth_start_deg": 0.0,
                "azimuth_end_deg": 360.0,
                "motion_summary": "水平环绕物体一圈并看向中心",
            }
        )
    elif expected_type == "dolly" or "推进" in text or "特写" in text:
        base.update(
            {
                "trajectory_type": "dolly",
                "radius_start": 5.2,
                "radius_end": 2.8,
                "azimuth_start_deg": 0.0,
                "azimuth_end_deg": 0.0,
                "elevation_start_deg": 15.0,
                "elevation_end_deg": 15.0,
                "motion_summary": "从远景沿正面推进到特写",
            }
        )
    elif expected_type == "pan" or "左向右" in text or "平移" in text:
        base.update(
            {
                "trajectory_type": "pan",
                "radius_start": 4.0,
                "radius_end": 4.0,
                "azimuth_start_deg": -35.0,
                "azimuth_end_deg": 35.0,
                "elevation_start_deg": 15.0,
                "elevation_end_deg": 15.0,
                "motion_summary": "从左侧移动到右侧并看向中心",
            }
        )
    elif expected_type == "tilt" or "俯视" in text or "下降" in text:
        base.update(
            {
                "trajectory_type": "tilt",
                "radius_start": 4.2,
                "radius_end": 4.2,
                "azimuth_start_deg": 20.0,
                "azimuth_end_deg": 20.0,
                "elevation_start_deg": 55.0,
                "elevation_end_deg": 5.0,
                "motion_summary": "从俯视角下降到接近平视角",
            }
        )
    elif expected_type == "orbit_dolly" or "半圈" in text or "拉远" in text:
        base.update(
            {
                "trajectory_type": "orbit_dolly",
                "radius_start": 3.2,
                "radius_end": 5.2,
                "azimuth_start_deg": -90.0,
                "azimuth_end_deg": 90.0,
                "elevation_start_deg": 20.0,
                "elevation_end_deg": 25.0,
                "motion_summary": "绕物体半圈并逐渐拉远",
            }
        )
    elif expected_type == "compound":
        if task_id == "closeup_pullback_orbit":
            base.update(
                {
                    "trajectory_type": "dolly",
                    "radius_start": 2.8,
                    "radius_end": 5.2,
                    "azimuth_start_deg": 0.0,
                    "azimuth_end_deg": 0.0,
                    "elevation_start_deg": 12.0,
                    "elevation_end_deg": 18.0,
                    "motion_summary": "规则基线只执行拉远，忽略后续环绕",
                }
            )
        elif task_id == "high_reveal_orbit":
            base.update(
                {
                    "trajectory_type": "tilt",
                    "radius_start": 5.2,
                    "radius_end": 4.0,
                    "azimuth_start_deg": -25.0,
                    "azimuth_end_deg": -25.0,
                    "elevation_start_deg": 55.0,
                    "elevation_end_deg": 18.0,
                    "motion_summary": "规则基线只执行下降揭示，忽略后续环绕",
                }
            )
        else:
            base.update(
                {
                    "trajectory_type": "pan",
                    "radius_start": 4.8,
                    "radius_end": 4.8,
                    "azimuth_start_deg": -45.0,
                    "azimuth_end_deg": 35.0,
                    "elevation_start_deg": 8.0,
                    "elevation_end_deg": 8.0,
                    "motion_summary": "规则基线只执行简单平移，忽略复合运动",
                }
            )
    else:
        base.update(
            {
                "trajectory_type": "orbit",
                "azimuth_start_deg": -45.0,
                "azimuth_end_deg": 45.0,
                "motion_summary": "默认小范围环绕",
            }
        )
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate rule-based camera trajectory JSON files.")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = json.loads(args.tasks.read_text(encoding="utf-8"))
    args.out_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for task in data["tasks"]:
        params = make_params(task["id"], task["text"], task.get("expected_type", ""))
        out_path = args.out_dir / f"{task['id']}.json"
        out_path.write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append({"task_id": task["id"], "path": str(out_path), "source": "rule"})

    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} rule trajectories to {args.out_dir}")


if __name__ == "__main__":
    main()
