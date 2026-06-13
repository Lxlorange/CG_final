#!/usr/bin/env bash
set -euo pipefail

# Ultra-small validation script. Run inside WSL after activating the Nerfstudio environment.
# It trains very briefly, renders the test split, and writes logs under ~/CG/outputs/logs.

ROOT="${ROOT:-$HOME/CG}"
DATA="${DATA:-$ROOT/datasets/nerf_synthetic/lego}"
OUT="${OUT:-$ROOT/outputs}"
RENDER_ROOT="${RENDER_ROOT:-$OUT/raw_renders_validation}"
LOG_DIR="${LOG_DIR:-$OUT/logs}"
MAX_ITERS="${MAX_ITERS:-20}"
METHODS=(${METHODS:-nerfacto splatfacto})
WINDOWS_PROJECT="${WINDOWS_PROJECT:-/mnt/d/2026_spring/Graphics/final}"
RUN_RENDER="${RUN_RENDER:-0}"

if [[ -x /usr/bin/gcc-11 && -x /usr/bin/g++-11 ]]; then
  export CC="${CC:-/usr/bin/gcc-11}"
  export CXX="${CXX:-/usr/bin/g++-11}"
  export CUDAHOSTCXX="${CUDAHOSTCXX:-/usr/bin/g++-11}"
fi
export MAX_JOBS="${MAX_JOBS:-2}"

if [[ -x /usr/bin/gcc-11 && -x /usr/bin/g++-11 ]]; then
  export CC="${CC:-/usr/bin/gcc-11}"
  export CXX="${CXX:-/usr/bin/g++-11}"
  export CUDAHOSTCXX="${CUDAHOSTCXX:-/usr/bin/g++-11}"
fi

mkdir -p "$OUT" "$RENDER_ROOT" "$LOG_DIR"

start_keep_awake() {
  if command -v powershell.exe >/dev/null 2>&1 && [[ -f "$WINDOWS_PROJECT/experiment/tools/keep_awake.ps1" ]]; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w "$WINDOWS_PROJECT/experiment/tools/keep_awake.ps1")" >/dev/null 2>&1 &
    KEEP_AWAKE_PID=$!
    echo "Started Windows keep-awake helper, pid=$KEEP_AWAKE_PID"
  else
    KEEP_AWAKE_PID=""
    echo "Warning: keep-awake helper not started. Prevent sleep manually."
  fi
}

stop_keep_awake() {
  if [[ -n "${KEEP_AWAKE_PID:-}" ]]; then
    kill "$KEEP_AWAKE_PID" >/dev/null 2>&1 || true
  fi
}

latest_config() {
  local method="$1"
  local experiment="$2"
  find "$OUT/$experiment/$method" -name config.yml -type f 2>/dev/null | sort | tail -n 1
}

train_and_render() {
  local method="$1"
  local experiment="lego_${method}_validate"
  local train_log="$LOG_DIR/${experiment}_train.log"
  local render_log="$LOG_DIR/${experiment}_render.log"

  echo "=== VALIDATE train $method for $MAX_ITERS iterations ==="
  ns-train "$method" \
    --output-dir "$OUT" \
    --experiment-name "$experiment" \
    --max-num-iterations "$MAX_ITERS" \
    --viewer.quit-on-train-completion True \
    blender-data \
    --data "$DATA" 2>&1 | tee "$train_log"

  local config
  config="$(latest_config "$method" "$experiment")"
  if [[ -z "$config" ]]; then
    echo "Could not find config.yml for $method under $OUT/$experiment" >&2
    exit 1
  fi

  if [[ "$RUN_RENDER" == "1" ]]; then
    echo "=== VALIDATE render $method with $config ==="
    mkdir -p "$RENDER_ROOT/$method"
    ns-render dataset \
      --load-config "$config" \
      --split test \
      --output-path "$RENDER_ROOT/$method" 2>&1 | tee "$render_log"
  else
    echo "Skipping validation render. Set RUN_RENDER=1 to render the full test split."
  fi
}

trap stop_keep_awake EXIT
start_keep_awake

echo "ROOT=$ROOT"
echo "DATA=$DATA"
echo "OUT=$OUT"
echo "METHODS=${METHODS[*]}"
echo "RUN_RENDER=$RUN_RENDER"
echo "CC=${CC:-unset}"
echo "CXX=${CXX:-unset}"
echo "CUDAHOSTCXX=${CUDAHOSTCXX:-unset}"
echo "MAX_JOBS=$MAX_JOBS"
echo "CC=${CC:-not set}"
echo "CXX=${CXX:-not set}"
echo "CUDAHOSTCXX=${CUDAHOSTCXX:-not set}"

for method in "${METHODS[@]}"; do
  train_and_render "$method"
done

echo "Validation finished."
echo "Raw renders: $RENDER_ROOT"
echo "Logs: $LOG_DIR"
