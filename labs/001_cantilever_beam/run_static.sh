#!/usr/bin/env bash
set -euo pipefail

# Lab 001 — Cantilever shell static benchmark
# Generates the CalculiX input file, runs CCX in Docker and postprocesses the .dat result.

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${LAB_DIR}/../.." && pwd)"

IMAGE="ale10tech/calculix-core:ccx2.23-ubuntu24.04"
CASE_NAME="cantilever_shell_static"

echo "== Lab 001: Cantilever Shell Static Benchmark =="
echo "Lab directory: ${LAB_DIR}"
echo "Docker image:  ${IMAGE}"
echo ""

echo "== Step 1: Generate CalculiX input file =="
python3 "${LAB_DIR}/python/generate_cantilever_shell_inp.py"
echo ""

echo "== Step 2: Prepare results directory =="
rm -f "${LAB_DIR}/results/${CASE_NAME}".*
cp "${LAB_DIR}/input/${CASE_NAME}.inp" "${LAB_DIR}/results/"
echo ""

echo "== Step 3: Run CalculiX in Docker =="
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${LAB_DIR}/results:/work" \
  -w /work \
  "${IMAGE}" \
  ccx "${CASE_NAME}"
echo ""

echo "== Step 4: Postprocess CalculiX .dat result =="
python3 "${LAB_DIR}/python/postprocess_static_dat.py"
echo ""

echo "== Done =="
echo "Summary:"
echo "${LAB_DIR}/results/${CASE_NAME}_summary.txt"
