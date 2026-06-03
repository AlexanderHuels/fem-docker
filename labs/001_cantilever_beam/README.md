# Lab 001 — Cantilever Shell Benchmark

This lab demonstrates a small reproducible CalculiX workflow for a cantilever shell benchmark.

The model is inspired by a classical cantilever beam benchmark and implemented with:

- CalculiX 2.23
- Docker
- Python-based input generation
- Python-based result postprocessing

## Unit system

- Force: N
- Length: mm
- Stress: MPa = N/mm²

## Model

- Beam length: 1000 mm
- Beam height: 100 mm
- Shell thickness: 20 mm
- Material: Aluminium
- Young's modulus: 71000 MPa
- Poisson's ratio: 0.3
- Total vertical load: 1000 N
- Boundary condition: left edge clamped

## Static reference result

Analytical Euler-Bernoulli tip displacement:

    delta = 2.816901 mm

CalculiX result at the two load nodes:

    mean |U3| = 2.830381 mm
    relative error = 0.479 %

## Run the lab

From the repository root:

    ./labs/001_cantilever_beam/run_static.sh

The script performs the complete workflow:

1. Generate the CalculiX .inp file
2. Run CalculiX inside Docker
3. Postprocess the .dat file
4. Write a summary file

## Important files

    CASE.md
    run_static.sh
    python/generate_cantilever_shell_inp.py
    python/postprocess_static_dat.py
    input/cantilever_shell_static.inp
    results/cantilever_shell_static_summary.txt

## Ignored files

Large or temporary CalculiX result files are intentionally ignored:

    .dat
    .frd
    .sta
    .cvg
    .12d
    spooles.out
