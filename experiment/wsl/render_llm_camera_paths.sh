#!/usr/bin/env bash
set -euo pipefail

CONFIG=""
ROOT="${ROOT:-/home/orangelxl/CG}"
WIN_ROOT="${WIN_ROOT:-/mnt/d/2026_spring/Graphics/final}"
PATH_ROOT="$WIN_ROOT/experiment/outputs/llm_camera/camera_paths"
OUT_ROOT="$WIN_ROOT/experiment/outputs/llm_camera/renders"
SOURCE="llm"
LIMIT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --path-root)
      PATH_ROOT="$2"
      shift 2
      ;;
    --out-root)
      OUT_ROOT="$2"
      shift 2
      ;;
    --source)
      SOURCE="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "Usage: bash render_llm_camera_paths.sh --config /path/to/splatfacto/config.yml [--source llm|rule] [--limit N]" >&2
  exit 2
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Config not found: $CONFIG" >&2
  exit 2
fi

SRC_DIR="$PATH_ROOT/$SOURCE"
if [[ ! -d "$SRC_DIR" ]]; then
  echo "Camera path directory not found: $SRC_DIR" >&2
  exit 2
fi

mkdir -p "$OUT_ROOT/$SOURCE"

count=0
for path in "$SRC_DIR"/*.json; do
  [[ -e "$path" ]] || continue
  name="$(basename "$path" .json)"
  if [[ -n "$LIMIT" && "$count" -ge "$LIMIT" ]]; then
    break
  fi
  echo "=== Render $SOURCE/$name ==="
  ns-render camera-path \
    --load-config "$CONFIG" \
    --camera-path-filename "$path" \
    --output-path "$OUT_ROOT/$SOURCE/$name.mp4"
  count=$((count + 1))
done

echo "Rendered $count camera paths to $OUT_ROOT/$SOURCE"
