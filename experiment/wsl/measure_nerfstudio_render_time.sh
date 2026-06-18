#!/usr/bin/env bash
set -euo pipefail

# Measure Nerfstudio dataset rendering time from an existing config.yml.
# Example:
#   bash /mnt/d/2026_spring/Graphics/final/experiment/wsl/measure_nerfstudio_render_time.sh \
#     --method nerfacto \
#     --scene lego \
#     --config /home/orangelxl/CG/outputs/lego_nerfacto/nerfacto/.../config.yml

METHOD=""
SCENE="lego"
CONFIG=""
SPLIT="test"
WINDOWS_PROJECT="${WINDOWS_PROJECT:-/mnt/d/2026_spring/Graphics/final}"
OUT_ROOT="${OUT_ROOT:-$WINDOWS_PROJECT/experiment/outputs/formal}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --method) METHOD="$2"; shift 2 ;;
    --scene) SCENE="$2"; shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    --split) SPLIT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$METHOD" || -z "$CONFIG" ]]; then
  echo "Usage: $0 --method METHOD --scene SCENE --config /path/to/config.yml [--split test]" >&2
  exit 2
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing config: $CONFIG" >&2
  exit 1
fi

RUN_DIR="$OUT_ROOT/$SCENE/render_timing/$METHOD"
RAW_DIR="$RUN_DIR/raw"
JSON_PATH="$RUN_DIR/render_time.json"
rm -rf "$RAW_DIR"
mkdir -p "$RAW_DIR"

START_NS="$(date +%s%N)"
ns-render dataset \
  --load-config "$CONFIG" \
  --split "$SPLIT" \
  --output-path "$RAW_DIR"
END_NS="$(date +%s%N)"

ELAPSED="$(python - <<PY
start = int("$START_NS")
end = int("$END_NS")
print((end - start) / 1_000_000_000)
PY
)"

RGB_DIR="$RAW_DIR/$SPLIT/rgb"
if [[ -d "$RGB_DIR" ]]; then
  FRAME_COUNT="$(find "$RGB_DIR" -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) | wc -l)"
else
  FRAME_COUNT="$(find "$RAW_DIR" -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) | wc -l)"
fi

SECONDS_PER_FRAME="$(python - <<PY
elapsed = float("$ELAPSED")
frames = int("$FRAME_COUNT")
print(elapsed / frames if frames else 0.0)
PY
)"

cat > "$JSON_PATH" <<JSON
{
  "scene": "$SCENE",
  "method": "$METHOD",
  "split": "$SPLIT",
  "config": "$CONFIG",
  "frames": $FRAME_COUNT,
  "total_render_seconds": $ELAPSED,
  "seconds_per_frame": $SECONDS_PER_FRAME
}
JSON

echo "Wrote $JSON_PATH"
cat "$JSON_PATH"
