#!/usr/bin/env bash
set -euo pipefail

# Full overnight script for the paper experiment. Run inside WSL after activating the Nerfstudio environment.
# Recommended: run inside tmux, e.g.
#   tmux new -s nerf
#   bash /mnt/d/2026_spring/Graphics/final/experiment/wsl/run_nerfstudio_lego_full.sh

ROOT="${ROOT:-$HOME/CG}"
DATA="${DATA:-$ROOT/datasets/nerf_synthetic/lego}"
OUT="${OUT:-$ROOT/outputs}"
RENDER_ROOT="${RENDER_ROOT:-$OUT/raw_renders_formal}"
LOG_DIR="${LOG_DIR:-$OUT/logs}"
WINDOWS_PROJECT="${WINDOWS_PROJECT:-/mnt/d/2026_spring/Graphics/final}"
MAX_ITERS_NERFACTO="${MAX_ITERS_NERFACTO:-30000}"
MAX_ITERS_SPLATFACTO="${MAX_ITERS_SPLATFACTO:-30000}"
METHODS=(${METHODS:-nerfacto splatfacto})

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

max_iters_for() {
  case "$1" in
    nerfacto) echo "$MAX_ITERS_NERFACTO" ;;
    splatfacto) echo "$MAX_ITERS_SPLATFACTO" ;;
    *) echo "${MAX_ITERS_DEFAULT:-30000}" ;;
  esac
}

latest_config() {
  local method="$1"
  local experiment="$2"
  find "$OUT/$experiment/$method" -name config.yml -type f 2>/dev/null | sort | tail -n 1
}

train_and_render() {
  local method="$1"
  local iters
  iters="$(max_iters_for "$method")"
  local experiment="lego_${method}"
  local train_log="$LOG_DIR/${experiment}_train.log"
  local render_log="$LOG_DIR/${experiment}_render.log"

  echo "=== TRAIN $method for $iters iterations ==="
  echo "Log: $train_log"
  ns-train "$method" \
    --output-dir "$OUT" \
    --experiment-name "$experiment" \
    --max-num-iterations "$iters" \
    --viewer.quit-on-train-completion True \
    blender-data \
    --data "$DATA" 2>&1 | tee "$train_log"

  local config
  config="$(latest_config "$method" "$experiment")"
  if [[ -z "$config" ]]; then
    echo "Could not find config.yml for $method under $OUT/$experiment" >&2
    exit 1
  fi

  echo "=== RENDER $method test split ==="
  echo "Config: $config"
  echo "Log: $render_log"
  mkdir -p "$RENDER_ROOT/$method"
  ns-render dataset \
    --load-config "$config" \
    --split test \
    --output-path "$RENDER_ROOT/$method" 2>&1 | tee "$render_log"
}

copy_results_to_windows_project() {
  local dst="$WINDOWS_PROJECT/experiment/outputs/formal/lego/raw_renders"
  if [[ -d "$WINDOWS_PROJECT" ]]; then
    mkdir -p "$dst"
    for method in "${METHODS[@]}"; do
      if [[ -d "$RENDER_ROOT/$method" ]]; then
        rm -rf "$dst/$method"
        cp -r "$RENDER_ROOT/$method" "$dst/$method"
      fi
    done
    echo "Copied raw renders to $dst"
  else
    echo "Windows project path not found: $WINDOWS_PROJECT"
    echo "Raw renders remain at $RENDER_ROOT"
  fi
}

trap stop_keep_awake EXIT
start_keep_awake

echo "ROOT=$ROOT"
echo "DATA=$DATA"
echo "OUT=$OUT"
echo "METHODS=${METHODS[*]}"
echo "MAX_ITERS_NERFACTO=$MAX_ITERS_NERFACTO"
echo "MAX_ITERS_SPLATFACTO=$MAX_ITERS_SPLATFACTO"
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

copy_results_to_windows_project

echo "Full training finished."
echo "Next in Windows PowerShell:"
echo "  python experiment\\scripts\\prepare_nerf_synthetic_eval.py --scene lego --max-views 20 --copy-mode composite"
echo "  python experiment\\scripts\\normalize_nerfstudio_renders.py --src-dir experiment\\outputs\\formal\\lego\\raw_renders\\nerfacto --dst-dir experiment\\outputs\\formal\\lego\\nerfacto --limit 20"
echo "  python experiment\\scripts\\normalize_nerfstudio_renders.py --src-dir experiment\\outputs\\formal\\lego\\raw_renders\\splatfacto --dst-dir experiment\\outputs\\formal\\lego\\splatfacto --limit 20"
echo "  python experiment\\scripts\\evaluate_folder.py --pred-dir experiment\\outputs\\formal\\lego\\nerfacto --method nerfacto --gt-dir experiment\\outputs\\formal\\lego\\gt --limit 20"
echo "  python experiment\\scripts\\evaluate_folder.py --pred-dir experiment\\outputs\\formal\\lego\\splatfacto --method splatfacto --gt-dir experiment\\outputs\\formal\\lego\\gt --limit 20"
echo "  python experiment\\scripts\\make_formal_summary.py --scene lego --max-views 8"
