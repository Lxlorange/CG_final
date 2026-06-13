from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from common import OUTPUTS, ensure_dir, load_json, load_rgb, save_json


def method_dirs(scene_root: Path):
    skip = {"gt", "raw_renders", "nerfstudio_runs", "summary"}
    return sorted(
        p for p in scene_root.iterdir()
        if p.is_dir() and p.name not in skip and (p / "metrics.json").exists()
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Make metrics table and comparison figure for formal NeRF Synthetic experiments.")
    parser.add_argument("--scene", default="lego")
    parser.add_argument("--max-views", type=int, default=8, help="Number of views shown in the comparison figure.")
    args = parser.parse_args()

    scene_root = OUTPUTS / "formal" / args.scene
    gt_dir = scene_root / "gt"
    summary_dir = scene_root / "summary"
    ensure_dir(summary_dir)

    methods = method_dirs(scene_root)
    if not methods:
        raise FileNotFoundError(f"No method metrics found under {scene_root}")

    rows = []
    for method_dir in methods:
        rows.extend(load_json(method_dir / "metrics.json")["results"])

    csv_path = summary_dir / "metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["method", "view", "mse", "psnr", "ssim", "render_seconds"])
        writer.writeheader()
        writer.writerows(rows)

    means = []
    for method_dir in methods:
        method_rows = [r for r in rows if r["method"] == method_dir.name]
        means.append({
            "method": method_dir.name,
            "mean_psnr": float(np.mean([r["psnr"] for r in method_rows])),
            "mean_ssim": float(np.mean([r["ssim"] for r in method_rows])),
            "mean_render_seconds": float(np.mean([r["render_seconds"] for r in method_rows])),
        })
    save_json(summary_dir / "summary.json", {"scene": args.scene, "methods": means})

    gt_paths = sorted(gt_dir.glob("gt_*.png"))[: args.max_views]
    if not gt_paths:
        raise FileNotFoundError(f"No GT images found under {gt_dir}")

    fig, axes = plt.subplots(1 + len(methods), len(gt_paths), figsize=(2.6 * len(gt_paths), 2.4 * (1 + len(methods))))
    if axes.ndim == 1:
        axes = axes[:, None]

    for col, gt_path in enumerate(gt_paths):
        gt = load_rgb(gt_path)
        axes[0, col].imshow(gt)
        axes[0, col].set_title(f"GT {col}")
        axes[0, col].axis("off")
        for row_idx, method_dir in enumerate(methods, start=1):
            pred = load_rgb(method_dir / f"pred_{col:03d}.png")
            axes[row_idx, col].imshow(pred)
            matched = [r for r in rows if r["method"] == method_dir.name and r["view"] == col][0]
            axes[row_idx, col].set_title(
                f"{method_dir.name}\nPSNR {matched['psnr']:.2f}, SSIM {matched['ssim']:.3f}",
                fontsize=8,
            )
            axes[row_idx, col].axis("off")

    fig.tight_layout()
    fig.savefig(summary_dir / "comparison.png", dpi=180)
    plt.close(fig)
    print(f"Wrote formal summary to {summary_dir}")


if __name__ == "__main__":
    main()
