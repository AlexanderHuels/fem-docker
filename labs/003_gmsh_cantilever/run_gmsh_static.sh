#!/usr/bin/env bash
set -euo pipefail

# Lab 003 — Gmsh cantilever shell workflow
# Generates .geo, runs Gmsh CLI in Docker, converts .msh to CalculiX .inp,
# runs CCX in Docker and postprocesses the .dat result.

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="ale10tech/calculix-core:ccx2.23-ubuntu24.04"
CASE_NAME="cantilever_shell_gmsh"

echo "== Lab 003: Gmsh Cantilever Shell Workflow =="
echo "Lab directory: ${LAB_DIR}"
echo "Docker image:  ${IMAGE}"
echo ""

echo "== Step 1: Generate Gmsh .geo file =="
python3 "${LAB_DIR}/python/generate_gmsh_geo.py"
echo ""

echo "== Step 2: Run Gmsh CLI in Docker =="
rm -f "${LAB_DIR}/mesh/${CASE_NAME}.msh"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${LAB_DIR}:/work" \
  -w /work \
  "${IMAGE}" \
  gmsh "geo/${CASE_NAME}.geo" -2 -format msh2 -o "mesh/${CASE_NAME}.msh"
echo ""

echo "== Step 3: Convert Gmsh .msh to CalculiX .inp =="
python3 "${LAB_DIR}/python/convert_msh_to_ccx_inp.py"
echo ""

echo "== Step 4: Run CalculiX in Docker =="
rm -f "${LAB_DIR}/results/${CASE_NAME}".*
rm -f "${LAB_DIR}/results/spooles.out"

cp "${LAB_DIR}/input/${CASE_NAME}.inp" "${LAB_DIR}/results/"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${LAB_DIR}/results:/work" \
  -w /work \
  "${IMAGE}" \
  ccx "${CASE_NAME}"
echo ""

echo "== Step 5: Postprocess CalculiX .dat result =="
python3 "${LAB_DIR}/python/postprocess_gmsh_static.py"
echo ""

echo "== Done =="
echo "Summary:"
echo "${LAB_DIR}/results/${CASE_NAME}_summary.txt"
