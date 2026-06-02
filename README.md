# FEM Docker Images

Docker-based FEM tooling for CalculiX workflows.

This repository currently provides a first working CalculiX core image based on Ubuntu 24.04.

## Current Image

```text
calculix-core:ubuntu24.04# FEM Docker Images

Docker-based FEM tooling for CalculiX workflows.

This repository currently provides a first working CalculiX core image based on Ubuntu 24.04.

## Current Image

```text
calculix-core:ubuntu24.04
```

## Included Tools

The current image includes:

* Ubuntu 24.04
* CalculiX CCX 2.21
* CalculiX CGX 2.21
* Python 3.12
* NumPy
* SciPy
* Pandas
* Matplotlib
* meshio
* PyVista
* JupyterLab
* Gmsh

## Why Ubuntu 24.04?

An initial Ubuntu 26.04 based image was tested, but the `calculix-ccx` package from Ubuntu 26.04 failed with:

```text
Illegal instruction (core dumped)
```

The Ubuntu 24.04 package was tested successfully and is therefore used as the first stable base image.

A future image may use Ubuntu 26.04 with a manually built CalculiX version.

## Build

From the repository root:

```bash
docker build -t calculix-core:ubuntu24.04 images/calculix-core
```

## Run CCX Manually

From a directory containing a CalculiX input file, for example `cantilever.inp`:

```bash
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" \
  -w /work \
  calculix-core:ubuntu24.04 \
  ccx cantilever
```

Important: call `ccx` without the `.inp` extension.

Correct:

```bash
ccx cantilever
```

Wrong:

```bash
ccx cantilever.inp
```

## Convenience Wrapper

A wrapper script is provided:

```bash
scripts/run_ccx.sh
```

Example:

```bash
cd examples/ccx_smoke_test
run_ccx.sh cantilever
```

The wrapper runs CCX inside Docker and maps generated result files back to the current Linux user.

## Smoke Test

The repository contains a minimal CalculiX smoke test:

```text
examples/ccx_smoke_test/cantilever.inp
```

Run:

```bash
cd examples/ccx_smoke_test
run_ccx.sh cantilever
```

Expected output files:

```text
cantilever.dat
cantilever.frd
cantilever.sta
cantilever.cvg
```

The generated result files are ignored by Git.

## Verified Local Setup

Tested on:

```text
Host: Windows 11
VM: Ubuntu 26.04 in Oracle VirtualBox
Docker Engine: 29.5.2
Docker Compose: v5.1.4
Docker Buildx: v0.34.1
Container base image: Ubuntu 24.04
CalculiX CCX: 2.21
```

## Repository Status

This is an early project state. The first goal is a stable, reproducible CalculiX Docker workflow.

Additional images may be added later for:

* FreeCAD / GUI preprocessing
* ParaView / postprocessing
* FEM + ML / AI workflows
* Debian slim or Alpine experiments
* Ubuntu 26.04 with CalculiX built from source

