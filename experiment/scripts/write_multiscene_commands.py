from __future__ import annotations

import argparse
from pathlib import Path

from common import OUTPUTS, ensure_dir
from write_nerfstudio_commands import posix


DEFAULT_DATASET_ROOT = OUTPUTS / "dataset" / "nerf_synthetic"
WSL_ROOT = Path(__file__).resolve().parents[1] / "wsl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Write WSL commands for multi-scene Nerfstudio experiments.")
    parser.add_argument("--scenes", nargs="+", default=["lego", "materials", "drums"])
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--methods", nargs="+", default=["nerfacto", "splatfacto"])
    parser.add_argument("--max-num-iterations", type=int, default=30000)
    parser.add_argument("--test-limit", type=int, default=20)
    args = parser.parse_args()

    script_path = WSL_ROOT / "run_multiscene_nerfstudio.sh"
    ensure_dir(script_path.parent)

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Run inside WSL after activating the Nerfstudio environment.",
        "# This script trains and renders each scene/method pair.",
        f'SCENES=({" ".join(args.scenes)})',
        f'METHODS=({" ".join(args.methods)})',
        f'DATASET_ROOT="{posix(args.dataset_root)}"',
        f'PROJECT_ROOT="{posix(Path.cwd())}"',
        f"MAX_ITERS={args.max_num_iterations}",
        f"TEST_LIMIT={args.test_limit}",
        'OUT_ROOT="$PROJECT_ROOT/experiment/outputs/formal"',
        "",
        "for scene in \"${SCENES[@]}\"; do",
        '  DATA="$DATASET_ROOT/$scene"',
        '  RUN_OUT="$OUT_ROOT/$scene/nerfstudio_runs"',
        '  RENDER_ROOT="$OUT_ROOT/$scene/raw_renders"',
        "  mkdir -p \"$RUN_OUT\" \"$RENDER_ROOT\"",
        '  python "$PROJECT_ROOT/experiment/scripts/limit_nerf_synthetic_split.py" "$DATA" --split test --limit "$TEST_LIMIT"',
        "  for method in \"${METHODS[@]}\"; do",
        '    echo "=== Training $scene / $method ==="',
        '    ns-train "$method" --output-dir "$RUN_OUT" --experiment-name "${scene}_${method}" --max-num-iterations "$MAX_ITERS" --viewer.quit-on-train-completion True blender-data --data "$DATA"',
        '    CONFIG="$(find "$RUN_OUT/${scene}_${method}/$method" -name config.yml -type f | sort | tail -n 1)"',
        '    echo "Using config: $CONFIG"',
        '    mkdir -p "$RENDER_ROOT/$method"',
        '    ns-render dataset --load-config "$CONFIG" --split test --output-path "$RENDER_ROOT/$method"',
        "  done",
        '  python "$PROJECT_ROOT/experiment/scripts/limit_nerf_synthetic_split.py" "$DATA" --split test --restore || true',
        "done",
        "",
    ]

    with script_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
        f.write("\n")
    print(f"Wrote {script_path}")


if __name__ == "__main__":
    main()
