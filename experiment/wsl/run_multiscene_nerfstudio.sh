#!/usr/bin/env bash
set -euo pipefail

# Run inside WSL after activating the Nerfstudio environment.
# This script trains and renders each scene/method pair.
SCENES=(lego materials drums)
METHODS=(nerfacto splatfacto)
DATASET_ROOT="/mnt/d/2026_spring/Graphics/final/experiment/outputs/dataset/nerf_synthetic"
PROJECT_ROOT="/mnt/d/2026_spring/Graphics/final"
MAX_ITERS=30000
TEST_LIMIT=20
OUT_ROOT="$PROJECT_ROOT/experiment/outputs/formal"

for scene in "${SCENES[@]}"; do
  DATA="$DATASET_ROOT/$scene"
  RUN_OUT="$OUT_ROOT/$scene/nerfstudio_runs"
  RENDER_ROOT="$OUT_ROOT/$scene/raw_renders"
  mkdir -p "$RUN_OUT" "$RENDER_ROOT"
  python "$PROJECT_ROOT/experiment/scripts/limit_nerf_synthetic_split.py" "$DATA" --split test --limit "$TEST_LIMIT"
  for method in "${METHODS[@]}"; do
    echo "=== Training $scene / $method ==="
    ns-train "$method" --output-dir "$RUN_OUT" --experiment-name "${scene}_${method}" --max-num-iterations "$MAX_ITERS" --viewer.quit-on-train-completion True blender-data --data "$DATA"
    CONFIG="$(find "$RUN_OUT/${scene}_${method}/$method" -name config.yml -type f | sort | tail -n 1)"
    echo "Using config: $CONFIG"
    mkdir -p "$RENDER_ROOT/$method"
    ns-render dataset --load-config "$CONFIG" --split test --output-path "$RENDER_ROOT/$method"
  done
  python "$PROJECT_ROOT/experiment/scripts/limit_nerf_synthetic_split.py" "$DATA" --split test --restore || true
done

