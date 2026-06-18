from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from common import OUTPUTS, ensure_dir, load_json, load_rgb, save_json


def method_dirs(scene_root: Path):
    skip = {"gt", "raw_renders", "nerfstudio_runs", "render_timing", "summary"}
    order = {
        "traditional_visual_hull": 0,
        "traditional_point_splat": 1,
        "nerfacto": 2,
        "splatfacto": 3,
    }
    methods = [
        p for p in scene_root.iterdir()
        if p.is_dir() and p.name not in skip and (p / "metrics.json").exists()
    ]
    return sorted(methods, key=lambda p: (order.get(p.name, 99), p.name))


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

    has_lpips = any("lpips" in r for r in rows)
    fieldnames = ["method", "view", "mse", "psnr", "ssim"]
    if has_lpips:
        fieldnames.append("lpips")
    fieldnames.append("render_seconds")

    csv_path = summary_dir / "metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    means = []
    for method_dir in methods:
        method_rows = [r for r in rows if r["method"] == method_dir.name]
        psnr_values = np.asarray([r["psnr"] for r in method_rows], dtype=np.float64)
        ssim_values = np.asarray([r["ssim"] for r in method_rows], dtype=np.float64)
        render_values = np.asarray([r["render_seconds"] for r in method_rows], dtype=np.float64)
        worst_psnr = min(method_rows, key=lambda r: r["psnr"])
        worst_ssim = min(method_rows, key=lambda r: r["ssim"])
        method_summary = {
            "method": method_dir.name,
            "num_views": len(method_rows),
            "mean_psnr": float(np.mean(psnr_values)),
            "std_psnr": float(np.std(psnr_values, ddof=1)) if len(method_rows) > 1 else 0.0,
            "worst_psnr_view": int(worst_psnr["view"]),
            "worst_psnr": float(worst_psnr["psnr"]),
            "mean_ssim": float(np.mean(ssim_values)),
            "std_ssim": float(np.std(ssim_values, ddof=1)) if len(method_rows) > 1 else 0.0,
            "worst_ssim_view": int(worst_ssim["view"]),
            "worst_ssim": float(worst_ssim["ssim"]),
            "mean_render_seconds": None if np.allclose(render_values, 0.0) else float(np.mean(render_values)),
        }
        timing_path = scene_root / "render_timing" / method_dir.name / "render_time.json"
        if timing_path.exists():
            timing = load_json(timing_path)
            method_summary["mean_render_seconds"] = float(timing["seconds_per_frame"])
            method_summary["total_render_seconds"] = float(timing["total_render_seconds"])
            method_summary["timed_render_frames"] = int(timing["frames"])
        if has_lpips and all("lpips" in r for r in method_rows):
            lpips_values = np.asarray([r["lpips"] for r in method_rows], dtype=np.float64)
            worst_lpips = max(method_rows, key=lambda r: r["lpips"])
            method_summary.update({
                "mean_lpips": float(np.mean(lpips_values)),
                "std_lpips": float(np.std(lpips_values, ddof=1)) if len(method_rows) > 1 else 0.0,
                "worst_lpips_view": int(worst_lpips["view"]),
                "worst_lpips": float(worst_lpips["lpips"]),
            })
        means.append(method_summary)
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

    fig, axes = plt.subplots(2, len(methods), figsize=(3.2 * len(methods), 5.0))
    if len(methods) == 1:
        axes = axes[:, None]
    for col_idx, method_dir in enumerate(methods):
        method_rows = [r for r in rows if r["method"] == method_dir.name]
        worst = min(method_rows, key=lambda r: r["psnr"])
        view = int(worst["view"])
        gt = load_rgb(gt_dir / f"gt_{view:03d}.png")
        pred = load_rgb(method_dir / f"pred_{view:03d}.png")
        axes[0, col_idx].imshow(gt)
        axes[0, col_idx].set_title(f"{method_dir.name}\nGT view {view}", fontsize=9)
        axes[0, col_idx].axis("off")
        axes[1, col_idx].imshow(pred)
        axes[1, col_idx].set_title(f"Prediction\nPSNR {worst['psnr']:.2f}, SSIM {worst['ssim']:.3f}", fontsize=9)
        axes[1, col_idx].axis("off")
    fig.tight_layout()
    fig.savefig(summary_dir / "failure_cases.png", dpi=180)
    plt.close(fig)
    print(f"Wrote formal summary to {summary_dir}")


if __name__ == "__main__":
    main()
