from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from common import DATASET, ensure_dir, image_metrics, load_json, load_rgb, write_metrics, save_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred-dir", required=True, type=Path)
    parser.add_argument("--method", required=True)
    parser.add_argument("--gt-dir", type=Path, default=None, help="Optional folder containing gt_000.png, gt_001.png, ...")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    rows = []
    t0 = time.perf_counter()
    if args.gt_dir is not None:
        gt_paths = sorted(args.gt_dir.glob("gt_*.png"))
        if args.limit is not None:
            gt_paths = gt_paths[: args.limit]
        if not gt_paths:
            raise FileNotFoundError(f"No gt_*.png files found in {args.gt_dir}")
        items = [{"gt_path": path} for path in gt_paths]
    else:
        meta = load_json(DATASET / "metadata.json")
        items = [{"gt_path": DATASET / "test" / item["rgb"]} for item in meta["test"]]
        if args.limit is not None:
            items = items[: args.limit]

    for i, item in enumerate(items):
        pred_path = args.pred_dir / f"pred_{i:03d}.png"
        if not pred_path.exists():
            raise FileNotFoundError(f"Missing prediction: {pred_path}")
        gt = load_rgb(item["gt_path"])
        pred = load_rgb(pred_path)
        row = {"method": args.method, "view": i, "render_seconds": 0.0}
        row.update(image_metrics(pred, gt))
        rows.append(row)

    ensure_dir(args.pred_dir)
    write_metrics(args.pred_dir / "metrics.json", rows)
    summary = {
        "method": args.method,
        "eval_seconds": time.perf_counter() - t0,
        "mean_psnr": float(np.mean([r["psnr"] for r in rows])),
        "mean_ssim": float(np.mean([r["ssim"] for r in rows])),
    }
    save_json(args.pred_dir / "summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
