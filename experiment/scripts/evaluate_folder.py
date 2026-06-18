from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from common import DATASET, ensure_dir, image_metrics, load_json, load_rgb, write_metrics, save_json


def make_lpips_metric(enabled: bool, device: str):
    if not enabled:
        return None
    try:
        import lpips
        import torch
    except Exception as exc:
        raise RuntimeError(
            "LPIPS requires torch and lpips. Install them in the evaluation environment, "
            "or rerun without --lpips."
        ) from exc

    loss_fn = lpips.LPIPS(net="alex").to(device)
    loss_fn.eval()

    def metric(pred: np.ndarray, gt: np.ndarray) -> float:
        pred_t = torch.from_numpy(pred).permute(2, 0, 1).unsqueeze(0).float()
        gt_t = torch.from_numpy(gt).permute(2, 0, 1).unsqueeze(0).float()
        pred_t = pred_t.to(device) * 2.0 - 1.0
        gt_t = gt_t.to(device) * 2.0 - 1.0
        with torch.no_grad():
            return float(loss_fn(pred_t, gt_t).item())

    return metric


def summarize(rows: list[dict], method: str, eval_seconds: float, has_lpips: bool, previous_summary: dict | None = None) -> dict:
    psnr_values = np.asarray([r["psnr"] for r in rows], dtype=np.float64)
    ssim_values = np.asarray([r["ssim"] for r in rows], dtype=np.float64)
    render_values = np.asarray([r["render_seconds"] for r in rows], dtype=np.float64)
    worst_psnr = min(rows, key=lambda r: r["psnr"])
    worst_ssim = min(rows, key=lambda r: r["ssim"])
    summary = dict(previous_summary or {})
    summary.update({
        "method": method,
        "num_views": len(rows),
        "eval_seconds": eval_seconds,
        "mean_psnr": float(np.mean(psnr_values)),
        "std_psnr": float(np.std(psnr_values, ddof=1)) if len(rows) > 1 else 0.0,
        "worst_psnr_view": int(worst_psnr["view"]),
        "worst_psnr": float(worst_psnr["psnr"]),
        "mean_ssim": float(np.mean(ssim_values)),
        "std_ssim": float(np.std(ssim_values, ddof=1)) if len(rows) > 1 else 0.0,
        "worst_ssim_view": int(worst_ssim["view"]),
        "worst_ssim": float(worst_ssim["ssim"]),
        "mean_render_seconds": float(np.mean(render_values)),
    })
    if has_lpips:
        lpips_values = np.asarray([r["lpips"] for r in rows], dtype=np.float64)
        worst_lpips = max(rows, key=lambda r: r["lpips"])
        summary.update({
            "mean_lpips": float(np.mean(lpips_values)),
            "std_lpips": float(np.std(lpips_values, ddof=1)) if len(rows) > 1 else 0.0,
            "worst_lpips_view": int(worst_lpips["view"]),
            "worst_lpips": float(worst_lpips["lpips"]),
        })
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred-dir", required=True, type=Path)
    parser.add_argument("--method", required=True)
    parser.add_argument("--gt-dir", type=Path, default=None, help="Optional folder containing gt_000.png, gt_001.png, ...")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--lpips", action="store_true", help="Compute LPIPS if torch and lpips are installed.")
    parser.add_argument("--lpips-device", default="cpu", help="Device used for LPIPS, e.g. cpu or cuda.")
    args = parser.parse_args()

    rows = []
    t0 = time.perf_counter()
    lpips_metric = make_lpips_metric(args.lpips, args.lpips_device)
    existing_rows = {}
    existing_metrics_path = args.pred_dir / "metrics.json"
    if existing_metrics_path.exists():
        try:
            existing_rows = {
                int(row["view"]): row
                for row in load_json(existing_metrics_path).get("results", [])
                if "view" in row
            }
        except Exception:
            existing_rows = {}
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
        previous = existing_rows.get(i, {})
        row = {
            "method": args.method,
            "view": i,
            "render_seconds": float(previous.get("render_seconds", 0.0)),
        }
        row.update(image_metrics(pred, gt))
        if lpips_metric is not None:
            row["lpips"] = lpips_metric(pred, gt)
        rows.append(row)

    ensure_dir(args.pred_dir)
    write_metrics(args.pred_dir / "metrics.json", rows)
    previous_summary = {}
    summary_path = args.pred_dir / "summary.json"
    if summary_path.exists():
        try:
            previous_summary = load_json(summary_path)
        except Exception:
            previous_summary = {}
    summary = summarize(rows, args.method, time.perf_counter() - t0, lpips_metric is not None, previous_summary)
    save_json(args.pred_dir / "summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
