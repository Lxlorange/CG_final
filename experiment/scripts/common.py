from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DATASET = OUTPUTS / "dataset"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_rgb(path: Path, image: np.ndarray) -> None:
    ensure_dir(path.parent)
    image = np.clip(image, 0.0, 1.0)
    Image.fromarray((image * 255.0 + 0.5).astype(np.uint8)).save(path)


def load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def save_json(path: Path, obj: Dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(v: np.ndarray, axis: int = -1, eps: float = 1e-8) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=axis, keepdims=True), eps)


def camera_frame(origin: Iterable[float], target: Iterable[float]) -> Dict[str, np.ndarray]:
    origin = np.asarray(origin, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    forward = normalize(target - origin)
    right = normalize(np.cross(forward, world_up))
    up = normalize(np.cross(right, forward))
    return {"origin": origin, "right": right, "up": up, "forward": forward}


def make_rays(camera: Dict, width: int, height: int, fov_degrees: float) -> Tuple[np.ndarray, np.ndarray]:
    f = 0.5 * width / np.tan(np.deg2rad(fov_degrees) * 0.5)
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    x_cam = (xs + 0.5 - width * 0.5) / f
    y_cam = (height * 0.5 - ys - 0.5) / f
    dirs = (
        camera["right"][None, None, :] * x_cam[..., None]
        + camera["up"][None, None, :] * y_cam[..., None]
        + camera["forward"][None, None, :]
    )
    dirs = normalize(dirs)
    origins = np.broadcast_to(camera["origin"][None, None, :], dirs.shape).copy()
    return origins, dirs


def image_metrics(pred: np.ndarray, gt: np.ndarray) -> Dict[str, float]:
    pred = np.clip(pred, 0.0, 1.0)
    gt = np.clip(gt, 0.0, 1.0)
    mse = float(np.mean((pred - gt) ** 2))
    psnr = 99.0 if mse <= 1e-12 else float(-10.0 * np.log10(mse))
    ssim = float(structural_similarity(gt, pred, channel_axis=-1, data_range=1.0))
    return {"mse": mse, "psnr": psnr, "ssim": ssim}


def write_metrics(path: Path, rows: Iterable[Dict]) -> None:
    rows = list(rows)
    ensure_dir(path.parent)
    save_json(path, {"results": rows})
