# FEM Durability Image for Ubuntu 24.04

## Image

Local test image:

    fem-durability:ubuntu24.04-test

Planned public image name:

    ale10tech/fem-durability:ubuntu24.04

## Purpose

This image provides a Python-based durability and fatigue analytics environment for FEM-related workflows.

The image is intended for:

* stress-time history processing
* rainflow counting
* S-N / Woehler based fatigue assessment
* Miner damage accumulation
* crack propagation experiments
* vibration fatigue / fatigue damage spectrum workflows
* FEM result and mesh data exchange through meshio, PyVista and VTK
* CSV and PNG report generation

This image is not a FEM solver. It is an engineering analytics image intended to complement solver images such as CalculiX and OpenRadioss.

## Included components

Base:

* Ubuntu 24.04
* Python 3
* Python virtual environment under `/opt/venv`

Scientific stack:

* numpy
* scipy
* pandas
* matplotlib

FEM I/O and visualization stack:

* meshio
* pyvista
* vtk

Fatigue and durability packages:

* rainflow
* fatpack
* pylife
* py-fatigue
* FatPy
* FatigueDS
* FLife

System/runtime support:

* python3-tk
* OpenGL / Mesa runtime libraries
* X11 runtime libraries
* fontconfig and common fonts

## Build

Build the local test image:

    docker build \
      --progress=plain \
      -f images/fem-durability/Dockerfile \
      -t fem-durability:ubuntu24.04-test \
      images/fem-durability 2>&1 | tee /tmp/fem-durability-build.log

Observed local image size:

    fem-durability:ubuntu24.04-test
    3.11GB uncompressed
    678MB compressed

## Validation

### Package import validation

Command:

    docker run --rm -i fem-durability:ubuntu24.04-test python - <<'PY'
    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pandas", "pandas"),
        ("matplotlib", "matplotlib"),
        ("meshio", "meshio"),
        ("pyvista", "pyvista"),
        ("vtk", "vtk"),
        ("rainflow", "rainflow"),
        ("fatpack", "fatpack"),
        ("pylife", "pylife"),
        ("py-fatigue", "py_fatigue"),
        ("FatPy", "fatpy"),
        ("FatigueDS", "FatigueDS"),
        ("FLife", "FLife"),
        ("tkinter", "tkinter"),
    ]

    for label, module in packages:
        try:
            __import__(module)
            print(f"OK   {label} -> import {module}")
        except Exception as e:
            print(f"FAIL {label} -> import {module}: {type(e).__name__}: {e}")
    PY

Observed result:

    OK   numpy -> import numpy
    OK   scipy -> import scipy
    OK   pandas -> import pandas
    OK   matplotlib -> import matplotlib
    OK   meshio -> import meshio
    OK   pyvista -> import pyvista
    OK   vtk -> import vtk
    OK   rainflow -> import rainflow
    OK   fatpack -> import fatpack
    OK   pylife -> import pylife
    OK   py-fatigue -> import py_fatigue
    OK   FatPy -> import fatpy
    OK   FatigueDS -> import FatigueDS
    OK   FLife -> import FLife
    OK   tkinter -> import tkinter

### Rainflow and Miner damage smoke test

The smoke test uses a synthetic stress-time history in MPa.

Workflow:

    synthetic stress-time history
      -> rainflow cycle extraction
      -> simple S-N curve
      -> Miner damage accumulation
      -> CSV output
      -> PNG output

Observed result:

    FEM durability smoke OK
    Extracted cycles: 50
    Total Miner damage: 2.017900e-06
    Created rainflow_cycles.csv
    Created miner_summary.csv
    Created stress_time_history.png
    Created rainflow_amplitude_histogram.png

Generated files:

    miner_summary.csv
    rainflow_cycles.csv
    stress_time_history.png
    rainflow_amplitude_histogram.png

Observed summary:

    n_points: 2000
    n_cycles_extracted: 50
    miner_damage_total: 2.0178998490230897e-06
    max_stress_mpa: 234.03719281587811
    min_stress_mpa: -74.037192815878
    stress_range_global_mpa: 308.0743856317561

## Example usage

Run scripts with the current user to avoid root-owned output files:

    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e MPLCONFIGDIR=/tmp/mplconfig \
      -v "$PWD:/work" \
      -w /work \
      fem-durability:ubuntu24.04-test \
      python script.py

Expected output ownership:

    files are written as the host user, not as root

## Recommended solver workflow

This image should be used together with solver and pre/post images.

Example architecture:

    CalculiX / OpenRadioss
      -> stress, strain or force time histories
      -> fem-durability
      -> rainflow, S-N, Miner damage
      -> CSV / PNG / optional VTU output

The image is intended to complement:

    ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04
    ale10tech/openradioss-core:ubuntu24.04
    ale10tech/fem-prepost:ubuntu24.04

## Current status

Validated locally:

* Docker build
* Python package imports
* tkinter dependency for FatigueDS and FLife
* rainflow cycle extraction
* simple S-N curve
* Miner damage accumulation
* CSV output
* PNG output
* host-user output ownership through `--user`

Not yet done:

* public Docker Hub push
* README integration
* dedicated lab example under `labs/`
* FEM result mapping to node or element damage fields
* VTU damage export
