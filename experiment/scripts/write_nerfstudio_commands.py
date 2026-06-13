from __future__ import annotations

import argparse
from pathlib import Path

from common import OUTPUTS, ensure_dir


DEFAULT_DATASET_ROOT = OUTPUTS / "dataset" / "nerf_synthetic"
FORMAL_ROOT = OUTPUTS / "formal"


def posix(path: Path) -> str:
    text = str(path).replace("\\", "/")
    if len(text) >= 2 and text[1] == ":":
        drive = text[0].lower()
        return f"/mnt/{drive}{text[2:]}"
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Write WSL Nerfstudio command templates for formal experiments.")
    parser.add_argument("--scene", default="lego")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--methods", nargs="+", default=["nerfacto", "splatfacto"])
    parser.add_argument("--max-num-iterations", type=int, default=30000)
    args = parser.parse_args()

    scene_dir = args.dataset_root / args.scene
    out_dir = FORMAL_ROOT / args.scene / "nerfstudio_runs"
    render_root = FORMAL_ROOT / args.scene / "raw_renders"
    script_path = FORMAL_ROOT / args.scene / "run_nerfstudio.sh"
    ensure_dir(script_path.parent)

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Generated command template. Run this in WSL after activating the Nerfstudio environment.",
        f'DATA="{posix(scene_dir)}"',
        f'OUT="{posix(out_dir)}"',
        f'RENDER_ROOT="{posix(render_root)}"',
        f"MAX_ITERS={args.max_num_iterations}",
        "",
        "mkdir -p \"$OUT\" \"$RENDER_ROOT\"",
        "",
    ]

    for method in args.methods:
        lines.extend([
            f'echo "=== Training {method} ==="',
            f'ns-train {method} --output-dir "$OUT" --experiment-name "{args.scene}_{method}" --max-num-iterations "$MAX_ITERS" --viewer.quit-on-train-completion True blender-data --data "$DATA"',
            "",
            "# Nerfstudio creates timestamped run folders. Pick the newest config.yml for this method.",
            f'CONFIG="$(find "$OUT/{args.scene}_{method}/{method}" -name config.yml -type f | sort | tail -n 1)"',
            'echo "Using config: $CONFIG"',
            f'mkdir -p "$RENDER_ROOT/{method}"',
            f'ns-render dataset --load-config "$CONFIG" --split test --output-path "$RENDER_ROOT/{method}"',
            "",
        ])

    lines.extend([
        'echo "Training and rendering finished."',
        'echo "Back in Windows/PowerShell, run normalize_nerfstudio_renders.py and evaluate_folder.py."',
        "",
    ])

    script_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {script_path}")


if __name__ == "__main__":
    main()
