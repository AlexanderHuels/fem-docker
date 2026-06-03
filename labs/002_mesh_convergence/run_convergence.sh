#!/usr/bin/env bash
set -euo pipefail

# Lab 002 — Mesh convergence study
# Generates mesh variants, runs all CalculiX cases in Docker and postprocesses convergence results.

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="ale10tech/calculix-core:ccx2.23-ubuntu24.04"

echo "== Lab 002: Cantilever Shell Mesh Convergence Study =="
echo "Lab directory: ${LAB_DIR}"
echo "Docker image:  ${IMAGE}"
echo ""

echo "== Step 1: Generate mesh variants =="
python3 "${LAB_DIR}/python/generate_mesh_variants.py"
echo ""

echo "== Step 2: Clean previous solver result files =="
rm -f "${LAB_DIR}"/results/cantilever_shell_nx*.*
rm -f "${LAB_DIR}"/results/spooles.out
echo ""

echo "== Step 3: Run all CalculiX cases =="
tail -n +2 "${LAB_DIR}/results/mesh_variants.csv" | cut -d, -f1 | while read -r CASE_NAME; do
  echo ""
  echo "== Running ${CASE_NAME} =="

  cp "${LAB_DIR}/input/${CASE_NAME}.inp" "${LAB_DIR}/results/"

  docker run --rm \
    --user "$(id -u):$(id -g)" \
    -v "${LAB_DIR}/results:/work" \
    -w /work \
    "${IMAGE}" \
    ccx "${CASE_NAME}"
done
echo ""

echo "== Step 4: Postprocess convergence results =="
python3 "${LAB_DIR}/python/postprocess_convergence.py"
echo ""

echo "== Done =="
echo "CSV summary:"
echo "${LAB_DIR}/results/convergence_results.csv"
echo ""
echo "Markdown summary:"
echo "${LAB_DIR}/results/convergence_summary.md"
