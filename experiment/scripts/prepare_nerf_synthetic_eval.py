from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from common import OUTPUTS, ensure_dir, load_rgb, save_json, save_rgb


DEFAULT_ROOT = OUTPUTS / "dataset" / "nerf_synthetic"
FORMAL_ROOT = OUTPUTS / "formal"


def frame_path(scene_dir: Path, frame: dict) -> Path:
    raw = frame["file_path"]
    path = scene_dir / raw
    if path.suffix:
        return path
    return path.with_suffix(".png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare ground-truth test images for NeRF Synthetic formal evaluation.")
    parser.add_argument("--scene", default="lego", help="Scene name under experiment/outputs/dataset/nerf_synthetic.")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--split", default="test", choices=["test", "val", "train"])
    parser.add_argument("--max-views", type=int, default=20, help="Number of held-out views used for report metrics.")
    parser.add_argument("--background", default="white", choices=["white", "black"], help="Alpha compositing background.")
    parser.add_argument("--copy-mode", default="copy", choices=["copy", "composite"], help="copy keeps original PNG; composite writes RGB over the chosen background.")
    args = parser.parse_args()

    scene_dir = args.dataset_root / args.scene
    transforms_path = scene_dir / f"transforms_{args.split}.json"
    if not transforms_path.exists():
        raise FileNotFoundError(f"Missing {transforms_path}")

    transforms = json.loads(transforms_path.read_text(encoding="utf-8"))
    frames = transforms["frames"][: args.max_views]
    out_dir = FORMAL_ROOT / args.scene
    gt_dir = out_dir / "gt"
    ensure_dir(gt_dir)

    bg = (1.0, 1.0, 1.0) if args.background == "white" else (0.0, 0.0, 0.0)
    manifest = {
        "scene": args.scene,
        "source_scene_dir": str(scene_dir),
        "split": args.split,
        "max_views": args.max_views,
        "alpha_background": args.background,
        "gt_dir": str(gt_dir),
        "frames": [],
    }

    for i, frame in enumerate(frames):
        src = frame_path(scene_dir, frame)
        dst = gt_dir / f"gt_{i:03d}.png"
        if args.copy_mode == "copy":
            shutil.copyfile(src, dst)
        else:
            save_rgb(dst, load_rgb(src, alpha_background=bg))
        manifest["frames"].append({
            "index": i,
            "source_file": str(src),
            "gt_file": str(dst),
            "camera_angle_x": transforms.get("camera_angle_x"),
            "transform_matrix": frame.get("transform_matrix"),
        })

    save_json(out_dir / "eval_manifest.json", manifest)
    print(f"Prepared {len(frames)} GT frames at {gt_dir}")
    print(f"Manifest: {out_dir / 'eval_manifest.json'}")


if __name__ == "__main__":
    main()
