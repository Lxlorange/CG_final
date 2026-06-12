from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from common import DATASET, OUTPUTS, ensure_dir, load_json, load_rgb


SUMMARY = OUTPUTS / "summary"


def load_rows(path: Path):
    return load_json(path)["results"]


def main():
    ensure_dir(SUMMARY)
    method_dirs = sorted(
        p for p in OUTPUTS.iterdir()
        if p.is_dir() and p.name not in {"dataset", "summary"} and (p / "metrics.json").exists()
    )
    rows = []
    for method_dir in method_dirs:
        rows.extend(load_rows(method_dir / "metrics.json"))

    csv_path = SUMMARY / "metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["method", "view", "mse", "psnr", "ssim", "render_seconds"])
        writer.writeheader()
        writer.writerows(rows)

    methods = [p.name for p in method_dirs]
    fig, axes = plt.subplots(1 + len(methods), 4, figsize=(10, 2.4 * (1 + len(methods))))
    if axes.ndim == 1:
        axes = axes[None, :]
    for col, view in enumerate(range(4)):
        gt = load_rgb(DATASET / "test" / f"rgb_{view:03d}.png")
        axes[0, col].imshow(gt)
        axes[0, col].set_title(f"GT view {view}")
        axes[0, col].axis("off")
        for row_idx, method in enumerate(methods, start=1):
            pred = load_rgb(OUTPUTS / method / f"pred_{view:03d}.png")
            axes[row_idx, col].imshow(pred)
            matched = [r for r in rows if r["method"] == method and r["view"] == view][0]
            axes[row_idx, col].set_title(f"{method}\nPSNR {matched['psnr']:.2f}, SSIM {matched['ssim']:.3f}", fontsize=8)
            axes[row_idx, col].axis("off")
    fig.tight_layout()
    fig.savefig(SUMMARY / "comparison.png", dpi=180)
    plt.close(fig)

    means = []
    for method in methods:
        method_rows = [r for r in rows if r["method"] == method]
        means.append({
            "method": method,
            "mean_psnr": float(np.mean([r["psnr"] for r in method_rows])),
            "mean_ssim": float(np.mean([r["ssim"] for r in method_rows])),
            "mean_render_seconds": float(np.mean([r["render_seconds"] for r in method_rows])),
        })
    from common import save_json

    save_json(SUMMARY / "summary.json", {"methods": means})
    print(f"Wrote summary to {SUMMARY}")


if __name__ == "__main__":
    main()
