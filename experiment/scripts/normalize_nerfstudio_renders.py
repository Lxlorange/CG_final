from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from common import ensure_dir


IMAGE_EXTS = {".png", ".jpg", ".jpeg"}


def natural_key(path: Path):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.stem)]


def find_images(src_dir: Path):
    rgb_dir = src_dir / "test" / "rgb"
    if rgb_dir.exists():
        images = [p for p in rgb_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS]
    else:
        test_dir = src_dir / "test"
        if test_dir.exists():
            images = [p for p in test_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS and p.parent.name == "rgb"]
        else:
            images = [p for p in src_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS and p.parent.name == "rgb"]
    return sorted(images, key=natural_key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Nerfstudio rendered images to pred_000.png naming.")
    parser.add_argument("--src-dir", required=True, type=Path, help="Raw Nerfstudio render folder.")
    parser.add_argument("--dst-dir", required=True, type=Path, help="Destination method folder, e.g. experiment/outputs/formal/lego/nerfacto.")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    images = find_images(args.src_dir)
    if not images:
        raise FileNotFoundError(f"No images found under {args.src_dir}")

    ensure_dir(args.dst_dir)
    for i, src in enumerate(images[: args.limit]):
        dst = args.dst_dir / f"pred_{i:03d}.png"
        shutil.copyfile(src, dst)
    print(f"Copied {min(len(images), args.limit)} images to {args.dst_dir}")


if __name__ == "__main__":
    main()
