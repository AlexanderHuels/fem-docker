# FEM Docker Images

Docker-based FEM tooling for CalculiX workflows.

This repository provides versioned Docker images for reproducible CalculiX CCX workflows based on Ubuntu 24.04.

## Current Images

```text
ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04
ale10tech/calculix-core:ccx2.23-ubuntu24.04
ale10tech/calculix-core:ccx2.21-ubuntu24.04
ale10tech/calculix-core:ubuntu24.04
ale10tech/fem-prepost:ubuntu24.04
ale10tech/freecad:ubuntu24.04
ale10tech/fem-durability:ubuntu24.04
ale10tech/openradioss-core:ubuntu24.04
```

## Docker Hub

The images are available on Docker Hub:

```text
ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04
ale10tech/calculix-core:ccx2.23-ubuntu24.04
ale10tech/calculix-core:ccx2.21-ubuntu24.04
ale10tech/calculix-core:ubuntu24.04
ale10tech/fem-prepost:ubuntu24.04
ale10tech/freecad:ubuntu24.04
ale10tech/fem-durability:ubuntu24.04
ale10tech/openradioss-core:ubuntu24.04
ale10tech/calculix-core:0.1.0
```

## CalculiX CCX 2.23 SPOOLES-MT Core Image

The recommended solver-core image is:

```text
ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04
```

This image provides:

* Ubuntu 24.04
* CalculiX CCX 2.23 built from upstream source
* source-built SPOOLES-MT support
* CGX from Ubuntu packages
* a smaller solver-focused image without Python, Gmsh, PyVista, VTK, ParaView, or JupyterLab

Build and validation notes:

* [CCX 2.23 SPOOLES-MT core image build notes](docs/images/ccx2.23-spoolesmt-core-ubuntu24.04.md)

Pull the image:

```bash
docker pull ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04
```

Example with four solver threads:

```bash
docker run --rm -it \
  -e OMP_NUM_THREADS=4 \
  --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" \
  -w /work \
  ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 \
  ccx cantilever
```

Important: call `ccx` without the `.inp` extension.

## CalculiX CCX 2.23 Source Build

The `ccx2.23-ubuntu24.04` image builds CalculiX CCX 2.23 from upstream source during the Docker build.

Reason:

* Ubuntu 24.04 apt packages provide CalculiX CCX 2.21.
* The upstream prebuilt CCX 2.23 Linux executable requires `libgfortran.so.4`, which is not available by default on Ubuntu 24.04.
* Building CCX 2.23 from source inside the container links the solver against the Ubuntu 24.04 runtime libraries.

Pull the image:

```bash
docker pull ale10tech/calculix-core:ccx2.23-ubuntu24.04
```

Run a CalculiX job from the current working directory:

```bash
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" \
  -w /work \
  ale10tech/calculix-core:ccx2.23-ubuntu24.04 \
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

## Included Tools

The image contents depend on the tag.

The current recommended solver-core image contains:

* Ubuntu 24.04
* CalculiX CCX 2.23
* SPOOLES-MT
* ARPACK
* BLAS/LAPACK
* CGX

It intentionally excludes heavier pre/postprocessing and notebook tooling such as Python virtual environments, Gmsh, PyVista, VTK, ParaView, and JupyterLab.

Version-specific notes:

* `ccx2.23-spoolesmt-ubuntu24.04` builds CCX 2.23 from upstream source with source-built SPOOLES-MT and includes CGX.
* `ccx2.23-ubuntu24.04` builds CCX 2.23 from upstream source and links against Ubuntu system SPOOLES.
* `ccx2.21-ubuntu24.04` uses Ubuntu package versions of CCX and CGX.
* Older early-stage images may still contain Python, Gmsh, PyVista, meshio, and JupyterLab. These tools will move into dedicated `fem-prepost` and `fem-lab` images.

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

## FEM Pre/Post Image

The `fem-prepost:ubuntu24.04` image provides a visualization and pre/postprocessing environment with:

* ParaView 5.11.2
* `pvpython`, `pvbatch`, and `pvserver`
* PyVista and VTK
* meshio
* Gmsh
* CGX
* Xvfb-based wrappers for headless ParaView rendering

Build and validation notes:

* [FEM pre/post image notes](docs/images/fem-prepost-ubuntu24.04.md)

Pull the image:

    docker pull ale10tech/fem-prepost:ubuntu24.04

Example PyVista or meshio workflow:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/fem-prepost:ubuntu24.04 \
      python3 postprocess.py

Example ParaView batch rendering:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/fem-prepost:ubuntu24.04 \
      pvpython-xvfb render.py

Example ParaView client/server workflow:

    docker run --rm -it \
      -p 11111:11111 \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/fem-prepost:ubuntu24.04 \
      pvserver --server-port=11111

Then connect a ParaView GUI client to `<VM-IP>:11111` or `localhost:11111` from inside the VM.

## OpenRadioss Core Image

The `openradioss-core:ubuntu24.04` image provides a minimal OpenRadioss solver environment with:

* OpenRadioss Starter
* OpenRadioss Engine
* OpenRadioss MPI Engine executable
* animation conversion via `anim_to_vtk_linux64_gf`
* time-history conversion via `th_to_csv_linux64_gf`

Build and validation notes:

* [OpenRadioss core image notes](docs/images/openradioss-core-ubuntu24.04.md)

Pull the image:

    docker pull ale10tech/openradioss-core:ubuntu24.04

Example Starter run:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/openradioss-core:ubuntu24.04 \
      starter_linux64_gf -i model_0000.rad -np 1 -nt 1

Example Engine run:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/openradioss-core:ubuntu24.04 \
      engine_linux64_gf -i model_0001.rad -nt 1

Known note: `engine_linux64_gf -help` may print help and then exit with code 139. Use `engine_linux64_gf -version` and a real Starter/Engine model run for validation.

## FreeCAD Image

The `freecad:ubuntu24.04` image provides a FreeCAD GUI and CLI environment with:

* FreeCAD 1.1.1 from the official Linux x86_64 AppImage
* `freecad`
* `freecadcmd`
* `freecad-xvfb`
* `freecadcmd-xvfb`
* FreeCADCmd scripting support
* FCStd and STEP export workflows
* Xvfb support for headless CLI/GUI smoke tests

Build and validation notes:

* [FreeCAD image notes](docs/images/freecad-ubuntu24.04.md)

Pull the image:

    docker pull ale10tech/freecad:ubuntu24.04

Example FreeCADCmd workflow:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/freecad:ubuntu24.04 \
      freecadcmd script.py

Example headless/Xvfb workflow:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/freecad:ubuntu24.04 \
      freecadcmd-xvfb script.py

Example GUI workflow from a graphical Ubuntu VM terminal:

    xhost +local:root

    docker run --rm -it \
      -e DISPLAY="$DISPLAY" \
      -e QT_QPA_PLATFORM=xcb \
      -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/freecad:ubuntu24.04 \
      freecad

    xhost -local:root

Known note: direct GUI usage requires a working host display. In a PowerShell to SSH to VM workflow, `DISPLAY` is usually empty and direct GUI usage is not expected to work.

## FEM Durability Image

The `fem-durability:ubuntu24.04` image provides a Python-based fatigue and durability analytics environment for FEM-related workflows.

It includes:

* numpy, scipy, pandas and matplotlib
* meshio, PyVista and VTK
* rainflow
* fatpack
* pyLife
* py-fatigue
* FatPy / FABER WG6 related tooling
* FatigueDS
* FLife

Build and validation notes:

* [FEM durability image notes](docs/images/fem-durability-ubuntu24.04.md)

Pull the image:

    docker pull ale10tech/fem-durability:ubuntu24.04

Example script workflow:

    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      -e MPLCONFIGDIR=/tmp/mplconfig \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/fem-durability:ubuntu24.04 \
      python script.py

Typical workflow:

    CalculiX / OpenRadioss
      -> stress, strain or force time histories
      -> fem-durability
      -> rainflow, S-N, Miner damage
      -> CSV / PNG / optional VTU output

The image was validated with a synthetic stress-time history, rainflow cycle extraction, a simple S-N curve, Miner damage accumulation, CSV export and PNG export.

