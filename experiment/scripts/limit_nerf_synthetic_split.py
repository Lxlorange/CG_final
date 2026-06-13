from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Temporarily limit a NeRF Synthetic transforms split to the first N frames.")
    parser.add_argument("scene_dir", type=Path, help="Scene folder, e.g. ~/CG/datasets/nerf_synthetic/lego")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--restore", action="store_true", help="Restore transforms file from .full.bak.")
    args = parser.parse_args()

    path = args.scene_dir / f"transforms_{args.split}.json"
    backup = args.scene_dir / f"transforms_{args.split}.json.full.bak"

    if args.restore:
        if not backup.exists():
            raise FileNotFoundError(f"Missing backup: {backup}")
        shutil.copyfile(backup, path)
        print(f"Restored {path} from {backup}")
        return

    if not path.exists():
        raise FileNotFoundError(path)
    if not backup.exists():
        shutil.copyfile(path, backup)

    data = json.loads(path.read_text(encoding="utf-8"))
    original_count = len(data.get("frames", []))
    data["frames"] = data.get("frames", [])[: args.limit]
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    print(f"Limited {path} from {original_count} to {len(data['frames'])} frames")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
