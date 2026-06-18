#!/usr/bin/env bash
set -euo pipefail

CONFIG=""
ROOT="${ROOT:-/home/orangelxl/CG}"
RENDER_CWD="${RENDER_CWD:-$ROOT}"
WIN_ROOT="${WIN_ROOT:-/mnt/d/2026_spring/Graphics/final}"
PATH_ROOT="$WIN_ROOT/experiment/outputs/llm_camera/camera_paths"
OUT_ROOT="$WIN_ROOT/experiment/outputs/llm_camera/renders"
SOURCE="llm"
LIMIT=""

if [[ -x /usr/bin/gcc-11 && -x /usr/bin/g++-11 ]]; then
  export CC="${CC:-/usr/bin/gcc-11}"
  export CXX="${CXX:-/usr/bin/g++-11}"
  export CUDAHOSTCXX="${CUDAHOSTCXX:-/usr/bin/g++-11}"
fi
export MAX_JOBS="${MAX_JOBS:-2}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --render-cwd)
      RENDER_CWD="$2"
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

if [[ ! -d "$RENDER_CWD" ]]; then
  echo "Render working directory not found: $RENDER_CWD" >&2
  exit 2
fi

SRC_DIR="$PATH_ROOT/$SOURCE"
if [[ ! -d "$SRC_DIR" ]]; then
  echo "Camera path directory not found: $SRC_DIR" >&2
  exit 2
fi

CONFIG="$(realpath "$CONFIG")"
PATH_ROOT="$(realpath "$PATH_ROOT")"
OUT_ROOT="$(realpath -m "$OUT_ROOT")"
RENDER_CWD="$(realpath "$RENDER_CWD")"

mkdir -p "$OUT_ROOT/$SOURCE"

cd "$RENDER_CWD"

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
