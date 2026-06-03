#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${LAB_DIR}/../.." && pwd)"

IMAGE="ale10tech/calculix-viz:ccx2.23-ubuntu24.04"

echo "== Lab 005: PyVista / VTK Postprocessing =="
echo "Repository: ${REPO_DIR}"
echo "Docker image: ${IMAGE}"
echo ""

echo "== Step 1: Check Lab 004 result files =="
if [[ ! -f "${REPO_DIR}/labs/004_animated_deformation/results/cantilever_shell_animation.inp" ]]; then
  echo "Missing Lab 004 input/result file."
  echo "Run first:"
  echo "  ./labs/004_animated_deformation/run_animation.sh"
  exit 1
fi

if [[ ! -f "${REPO_DIR}/labs/004_animated_deformation/results/cantilever_shell_animation.dat" ]]; then
  echo "Missing Lab 004 displacement result file."
  echo "Run first:"
  echo "  ./labs/004_animated_deformation/run_animation.sh"
  exit 1
fi

echo "Lab 004 result files found."
echo ""

echo "== Step 2: Render PyVista PNG views =="
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${REPO_DIR}:/repo" \
  -w /repo \
  "${IMAGE}" \
  python3 labs/005_pyvista_vtk/python/render_cantilever_pyvista.py
echo ""

echo "== Step 3: Create PyVista GIF animation =="
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${REPO_DIR}:/repo" \
  -w /repo \
  "${IMAGE}" \
  python3 labs/005_pyvista_vtk/python/create_pyvista_gif.py
echo ""

echo "== Done =="
echo "Main GIF:"
echo "${LAB_DIR}/figures/cantilever_pyvista_overlay_animation.gif"
echo ""
echo "Overlay PNG:"
echo "${LAB_DIR}/figures/cantilever_pyvista_deformed_overlay_scale30.png"
