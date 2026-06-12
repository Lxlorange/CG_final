from __future__ import annotations

import time

import numpy as np
from sklearn.kernel_approximation import RBFSampler
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import DATASET, OUTPUTS, ensure_dir, image_metrics, load_json, load_rgb, make_rays, save_json, save_rgb, write_metrics


OUT = OUTPUTS / "neural_ray_field"


def pixel_grid(width, height):
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    x = (xs + 0.5) / width * 2.0 - 1.0
    y = (ys + 0.5) / height * 2.0 - 1.0
    return x.reshape(-1, 1), y.reshape(-1, 1)


def view_features(angle_degrees, count):
    a = np.deg2rad(angle_degrees)
    return np.tile(np.array([[np.sin(a), np.cos(a)]], dtype=np.float32), (count, 1))


def collect_training_samples(meta, max_samples=60000, seed=7):
    rng = np.random.default_rng(seed)
    xs = []
    ys = []
    width = meta["width"]
    height = meta["height"]
    fov = meta["fov_degrees"]
    for item in meta["train"]:
        rgb = load_rgb(DATASET / "train" / item["rgb"])
        camera = {k: np.asarray(v, dtype=np.float32) for k, v in item["camera"].items()}
        origins, dirs = make_rays(camera, width, height, fov)
        px, py = pixel_grid(width, height)
        angle = view_features(item["angle_degrees"], width * height)
        feat = np.concatenate([origins.reshape(-1, 3), dirs.reshape(-1, 3), px, py, angle], axis=1)
        xs.append(feat)
        ys.append(rgb.reshape(-1, 3))
    x = np.concatenate(xs, axis=0)
    y = np.concatenate(ys, axis=0)
    if x.shape[0] > max_samples:
        idx = rng.choice(x.shape[0], size=max_samples, replace=False)
        x = x[idx]
        y = y[idx]
    return x, y


def ray_features(camera, width, height, fov, angle_degrees):
    origins, dirs = make_rays(camera, width, height, fov)
    px, py = pixel_grid(width, height)
    angle = view_features(angle_degrees, width * height)
    return np.concatenate([origins.reshape(-1, 3), dirs.reshape(-1, 3), px, py, angle], axis=1)


def main():
    ensure_dir(OUT)
    meta = load_json(DATASET / "metadata.json")
    x_train, y_train = collect_training_samples(meta)

    model = make_pipeline(
        StandardScaler(),
        RBFSampler(gamma=1.2, n_components=1024, random_state=3),
        Ridge(alpha=5e-4, solver="lsqr"),
    )
    t0 = time.perf_counter()
    model.fit(x_train, y_train)
    train_seconds = time.perf_counter() - t0

    rows = []
    render_times = []
    for i, item in enumerate(meta["test"]):
        camera = {k: np.asarray(v, dtype=np.float32) for k, v in item["camera"].items()}
        gt = load_rgb(DATASET / "test" / item["rgb"])
        x_test = ray_features(camera, meta["width"], meta["height"], meta["fov_degrees"], item["angle_degrees"])
        t1 = time.perf_counter()
        pred = model.predict(x_test).reshape(meta["height"], meta["width"], 3)
        render_seconds = time.perf_counter() - t1
        render_times.append(render_seconds)
        pred = np.clip(pred, 0.0, 1.0)
        save_rgb(OUT / f"pred_{i:03d}.png", pred)
        row = {"method": "neural_ray_field", "view": i, "render_seconds": render_seconds}
        row.update(image_metrics(pred, gt))
        rows.append(row)

    write_metrics(OUT / "metrics.json", rows)
    summary = {
        "method": "neural_ray_field",
        "training_samples": int(x_train.shape[0]),
        "feature_components": 1024,
        "train_seconds": train_seconds,
        "mean_render_seconds": float(np.mean(render_times)),
        "mean_psnr": float(np.mean([r["psnr"] for r in rows])),
        "mean_ssim": float(np.mean([r["ssim"] for r in rows])),
    }
    save_json(OUT / "summary.json", summary)
    print(f"Neural ray field done: {summary}")


if __name__ == "__main__":
    main()
