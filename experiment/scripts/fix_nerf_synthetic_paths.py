from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def strip_png_suffixes(file_path: str) -> str:
    while file_path.endswith(".png"):
        file_path = file_path[:-4]
    return file_path


def append_png_suffix(file_path: str) -> str:
    if Path(file_path).suffix:
        return file_path
    return f"{file_path}.png"


def rewrite_json_paths(transforms_path: Path, backup: bool, mode: str) -> int:
    data = json.loads(transforms_path.read_text(encoding="utf-8"))
    changed = 0
    for frame in data.get("frames", []):
        file_path = frame.get("file_path")
        if not file_path:
            continue
        new_path = strip_png_suffixes(file_path) if mode == "strip-png" else append_png_suffix(file_path)
        if new_path != file_path:
            frame["file_path"] = new_path
            changed += 1

    if changed:
        if backup:
            backup_path = transforms_path.with_suffix(transforms_path.suffix + ".bak")
            if not backup_path.exists():
                shutil.copyfile(transforms_path, backup_path)
        transforms_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    return changed


def remove_extensionless_aliases(scene_dir: Path, transforms_path: Path) -> int:
    data = json.loads(transforms_path.read_text(encoding="utf-8"))
    removed = 0
    for frame in data.get("frames", []):
        file_path = frame.get("file_path")
        if not file_path:
            continue
        rel_no_ext = Path(strip_png_suffixes(file_path))
        alias_path = scene_dir / rel_no_ext
        png_path = alias_path.with_suffix(".png")
        if not alias_path.exists() or alias_path == png_path:
            continue
        try:
            if alias_path.is_symlink():
                alias_path.unlink()
                removed += 1
            elif png_path.exists() and alias_path.is_file():
                # Only remove extensionless copied aliases when the real PNG exists.
                alias_path.unlink()
                removed += 1
        except OSError as exc:
            print(f"Warning: failed to remove {alias_path}: {exc}")
    return removed


def sample_paths(transforms_path: Path) -> list[str]:
    data = json.loads(transforms_path.read_text(encoding="utf-8"))
    return [frame.get("file_path", "") for frame in data.get("frames", [])[:3]]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix NeRF Synthetic transforms paths. Use strip-png with Nerfstudio blender-data."
    )
    parser.add_argument("scene_dir", type=Path, help="Path to a scene folder, e.g. ~/CG/datasets/nerf_synthetic/lego")
    parser.add_argument(
        "--mode",
        choices=["strip-png", "append-png"],
        default="strip-png",
        help="strip-png restores ./train/r_0 for Nerfstudio blender-data; append-png writes ./train/r_0.png.",
    )
    parser.add_argument("--cleanup-aliases", action="store_true", help="Remove extensionless symlinks/copies like train/r_0.")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    if not args.scene_dir.exists():
        raise FileNotFoundError(args.scene_dir)

    total = 0
    for split in ["train", "val", "test"]:
        path = args.scene_dir / f"transforms_{split}.json"
        if path.exists():
            before = sample_paths(path)
            changed = rewrite_json_paths(path, backup=not args.no_backup, mode=args.mode)
            if args.cleanup_aliases:
                changed += remove_extensionless_aliases(args.scene_dir, path)
            after = sample_paths(path)
            total += changed
            print(f"{path}: changed {changed} entries/files")
            print(f"  before: {before}")
            print(f"  after : {after}")
    print(f"Done. Total changes: {total}")


if __name__ == "__main__":
    main()
