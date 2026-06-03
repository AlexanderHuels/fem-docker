#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="ale10tech/calculix-core:ccx2.23-ubuntu24.04"
CASE_NAME="cantilever_shell_animation"

echo "== Step 1: Generate CalculiX input =="
python3 "$LAB_DIR/python/generate_animation_inp.py"

echo ""
echo "== Step 2: Run CalculiX in Docker =="

rm -f "$LAB_DIR/results/${CASE_NAME}."*
cp "$LAB_DIR/input/${CASE_NAME}.inp" "$LAB_DIR/results/"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$LAB_DIR/results:/work" \
  -w /work \
  "$IMAGE" \
  ccx "$CASE_NAME"

echo ""
echo "== Step 3: Create animated GIF =="
python3 "$LAB_DIR/python/create_deformation_gif.py"

echo ""
echo "== Done =="
echo "GIF:"
echo "$LAB_DIR/figures/cantilever_shell_animation_linkedin.gif"
echo ""
echo "Summary:"
echo "$LAB_DIR/results/cantilever_shell_animation_summary.txt"
