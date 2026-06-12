from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np

from common import DATASET, camera_frame, ensure_dir, make_rays, save_json, save_rgb


WIDTH = 128
HEIGHT = 128
FOV = 48.0
TARGET = np.array([0.0, 0.65, 0.15], dtype=np.float32)


def intersect_sphere(o, d, center, radius):
    oc = o - center
    b = np.sum(oc * d, axis=-1)
    c = np.sum(oc * oc, axis=-1) - radius * radius
    disc = b * b - c
    t = np.full(disc.shape, np.inf, dtype=np.float32)
    hit = disc > 0
    sqrt_disc = np.sqrt(np.maximum(disc, 0.0))
    t0 = -b - sqrt_disc
    t1 = -b + sqrt_disc
    cand = np.where(t0 > 1e-4, t0, t1)
    hit = hit & (cand > 1e-4)
    t[hit] = cand[hit]
    p = o + d * t[..., None]
    n = (p - center) / radius
    color = np.zeros_like(p)
    color[..., 0] = 0.86
    color[..., 1] = 0.28
    color[..., 2] = 0.18
    return t, n, color


def intersect_box(o, d, bmin, bmax):
    inv = 1.0 / np.where(np.abs(d) < 1e-8, 1e-8, d)
    t0 = (bmin - o) * inv
    t1 = (bmax - o) * inv
    tmin = np.maximum.reduce(np.minimum(t0, t1), axis=-1)
    tmax = np.minimum.reduce(np.maximum(t0, t1), axis=-1)
    hit = (tmax >= np.maximum(tmin, 1e-4))
    t = np.where(hit, tmin, np.inf).astype(np.float32)
    p = o + d * t[..., None]
    eps = 2e-3
    n = np.zeros_like(p)
    n[np.abs(p[..., 0] - bmin[0]) < eps] = [-1.0, 0.0, 0.0]
    n[np.abs(p[..., 0] - bmax[0]) < eps] = [1.0, 0.0, 0.0]
    n[np.abs(p[..., 1] - bmin[1]) < eps] = [0.0, -1.0, 0.0]
    n[np.abs(p[..., 1] - bmax[1]) < eps] = [0.0, 1.0, 0.0]
    n[np.abs(p[..., 2] - bmin[2]) < eps] = [0.0, 0.0, -1.0]
    n[np.abs(p[..., 2] - bmax[2]) < eps] = [0.0, 0.0, 1.0]
    color = np.zeros_like(p)
    color[..., 0] = 0.18
    color[..., 1] = 0.44
    color[..., 2] = 0.82
    return t, n, color


def intersect_floor(o, d):
    t = (0.0 - o[..., 1]) / np.where(np.abs(d[..., 1]) < 1e-8, 1e-8, d[..., 1])
    p = o + d * t[..., None]
    hit = (t > 1e-4) & (np.abs(p[..., 0]) < 3.0) & (np.abs(p[..., 2]) < 3.0)
    t = np.where(hit, t, np.inf).astype(np.float32)
    n = np.zeros_like(p)
    n[..., 1] = 1.0
    checker = ((np.floor((p[..., 0] + 3.0) * 2.0) + np.floor((p[..., 2] + 3.0) * 2.0)) % 2.0)
    base = np.where(checker[..., None] > 0.5, [0.72, 0.72, 0.68], [0.42, 0.42, 0.38])
    return t, n, base.astype(np.float32)


def intersect_back_wall(o, d):
    z = 2.2
    t = (z - o[..., 2]) / np.where(np.abs(d[..., 2]) < 1e-8, 1e-8, d[..., 2])
    p = o + d * t[..., None]
    hit = (t > 1e-4) & (np.abs(p[..., 0]) < 3.0) & (p[..., 1] > 0.0) & (p[..., 1] < 2.5)
    t = np.where(hit, t, np.inf).astype(np.float32)
    n = np.zeros_like(p)
    n[..., 2] = -1.0
    color = np.zeros_like(p)
    color[..., 0] = 0.74
    color[..., 1] = 0.78
    color[..., 2] = 0.70
    return t, n, color


def render(camera):
    origins, dirs = make_rays(camera, WIDTH, HEIGHT, FOV)
    candidates = []
    candidates.append(intersect_floor(origins, dirs))
    candidates.append(intersect_sphere(origins, dirs, np.array([-0.72, 0.62, 0.05], dtype=np.float32), 0.62))
    candidates.append(intersect_box(origins, dirs, np.array([0.35, 0.0, -0.45], dtype=np.float32), np.array([1.25, 1.08, 0.45], dtype=np.float32)))

    ts = np.stack([c[0] for c in candidates], axis=-1)
    idx = np.argmin(ts, axis=-1)
    t = np.take_along_axis(ts, idx[..., None], axis=-1)[..., 0]
    normal = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
    color = np.zeros_like(normal)
    for i, (_, n, c) in enumerate(candidates):
        mask = idx == i
        normal[mask] = n[mask]
        color[mask] = c[mask]

    hit = np.isfinite(t)
    light_dir = np.array([-0.45, 0.85, -0.28], dtype=np.float32)
    light_dir = light_dir / np.linalg.norm(light_dir)
    diffuse = np.maximum(np.sum(normal * light_dir[None, None, :], axis=-1), 0.0)
    view = -dirs
    half_vec = light_dir[None, None, :] + view
    half_vec = half_vec / np.maximum(np.linalg.norm(half_vec, axis=-1, keepdims=True), 1e-8)
    spec = np.maximum(np.sum(normal * half_vec, axis=-1), 0.0) ** 40
    shaded = color * (0.22 + 0.78 * diffuse[..., None]) + 0.18 * spec[..., None]

    sky = np.zeros_like(shaded)
    sky[..., 0] = 0.56 + 0.18 * np.clip(dirs[..., 1], 0.0, 1.0)
    sky[..., 1] = 0.66 + 0.14 * np.clip(dirs[..., 1], 0.0, 1.0)
    sky[..., 2] = 0.82 + 0.10 * np.clip(dirs[..., 1], 0.0, 1.0)
    image = np.where(hit[..., None], shaded, sky)
    depth = np.where(hit, t, 0.0).astype(np.float32)
    return np.clip(image, 0.0, 1.0), depth


def make_camera(angle_deg: float, radius: float = 4.0):
    a = math.radians(angle_deg)
    origin = np.array([radius * math.sin(a), 1.55, radius * math.cos(a)], dtype=np.float32)
    return camera_frame(origin, TARGET)


def camera_to_json(camera):
    return {k: v.tolist() for k, v in camera.items()}


def main():
    t0 = time.perf_counter()
    ensure_dir(DATASET)
    train_angles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
    test_angles = [15, 75, 135, 255]
    meta = {"width": WIDTH, "height": HEIGHT, "fov_degrees": FOV, "train": [], "test": []}

    for split, angles in [("train", train_angles), ("test", test_angles)]:
        split_dir = DATASET / split
        ensure_dir(split_dir)
        for i, angle in enumerate(angles):
            camera = make_camera(angle)
            image, depth = render(camera)
            rgb_name = f"rgb_{i:03d}.png"
            depth_name = f"depth_{i:03d}.npy"
            save_rgb(split_dir / rgb_name, image)
            np.save(split_dir / depth_name, depth)
            meta[split].append({"angle_degrees": angle, "rgb": rgb_name, "depth": depth_name, "camera": camera_to_json(camera)})

    meta["generation_seconds"] = time.perf_counter() - t0
    save_json(DATASET / "metadata.json", meta)
    print(f"Generated dataset at {DATASET}")


if __name__ == "__main__":
    main()
