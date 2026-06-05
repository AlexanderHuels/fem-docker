# CalculiX CCX 2.23 SPOOLES-MT Core Image on Ubuntu 24.04

This document describes the build strategy and validation notes for:

    ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04

## Purpose

This image is the main CalculiX solver-core image for Ubuntu 24.04.

It contains:

    CCX 2.23
    SPOOLES-MT
    ARPACK
    BLAS/LAPACK
    CGX
    minimal runtime tools

It intentionally does not contain:

    Python virtual environment
    PyVista
    VTK
    meshio
    Gmsh
    ParaView
    JupyterLab

These tools belong to separate images such as `fem-prepost` or `fem-lab`.

## Image architecture

The image separates solver functionality from visualization and engineering analytics.

    calculix-core
      Solver-focused image
      CCX 2.23 + SPOOLES-MT + CGX

    fem-prepost
      Visualization and pre/postprocessing image
      ParaView + PyVista + VTK + meshio + Gmsh + CGX

    fem-lab
      Notebook and Python engineering workflow image

This keeps the solver image smaller, reproducible, and easier to validate.

## Why CCX is built from source

Ubuntu 24.04 provides an older `calculix-ccx` package. To use CCX 2.23, the solver is built from the upstream source archive:

    https://www.dhondt.de/ccx_2.23.src.tar.bz2

The upstream prebuilt Linux binary is not used because it may depend on older runtime libraries that are not available by default on Ubuntu 24.04.

## Why SPOOLES is built from source

The multi-threaded SPOOLES variant is built from the Netlib SPOOLES 2.2 source archive:

    https://www.netlib.org/linalg/spooles/spooles.2.2.tgz

The build creates:

    SPOOLES.2.2/spooles.a
    SPOOLES.2.2/MT/src/spoolesMT.a

CCX is then linked against these static SPOOLES libraries instead of Ubuntu's dynamic `libspooles.so`.

## Important SPOOLES patch for modern Ubuntu

The original SPOOLES 2.2 source contains old timing code in `timings.h`:

    static struct timezone TZ ;

On modern Ubuntu/glibc this can fail with an error like:

    error: storage size of 'TZ' isn't known

The Dockerfile patches this by disabling the obsolete `struct timezone` usage and replacing `&TZ` with `NULL`:

    sed -i \
        -e 's|static struct timezone TZ ;|/* static struct timezone TZ disabled for modern glibc */|' \
        -e 's|&TZ|NULL|g' \
        timings.h

This keeps `gettimeofday()` usable for timing while avoiding the obsolete timezone structure.

## Important CCX build flags

The CCX build must enable OpenMP and the multi-threaded SPOOLES path.

The relevant C flags are:

    -fcommon
    -fopenmp
    -DUSE_MT=1

The relevant Fortran flags are:

    -fallow-argument-mismatch
    -fopenmp

The Dockerfile applies these edits to the CCX Makefile:

    -e 's|-I ../../../SPOOLES.2.2|-I/tmp/calculix-build/SPOOLES.2.2|g'
    -e 's|-I ../../../ARPACK|-I/usr/include/arpack|g'
    -e 's|CFLAGS =|CFLAGS = -fcommon -fopenmp -DUSE_MT=1 |'
    -e 's|FFLAGS =|FFLAGS = -fallow-argument-mismatch -fopenmp |'

## Important include-path detail

Do not include only:

    -I/tmp/calculix-build/SPOOLES.2.2/MT/src

This is not sufficient.

CCX also needs headers from the broader SPOOLES tree. The working include path is:

    -I/tmp/calculix-build/SPOOLES.2.2

Using only the `MT/src` include path can produce errors such as:

    spooles.h: fatal error: misc.h: No such file or directory

## Important linker detail

The working CCX link setup explicitly links both the multi-threaded and base SPOOLES static libraries:

    /tmp/calculix-build/SPOOLES.2.2/MT/src/spoolesMT.a
    /tmp/calculix-build/SPOOLES.2.2/spooles.a

Together with:

    -larpack
    -llapack
    -lblas
    -lgomp
    -lpthread
    -lm

The Dockerfile appends:

    LIBS = /tmp/calculix-build/SPOOLES.2.2/MT/src/spoolesMT.a /tmp/calculix-build/SPOOLES.2.2/spooles.a -larpack -llapack -lblas -lgomp -lpthread -lm

## Why CGX is installed from Ubuntu packages

CGX is installed via:

    calculix-cgx

On Ubuntu 24.04 this installs `calculix-cgx` without pulling in the older `calculix-ccx` package.

This allows the image to provide:

    /usr/local/bin/ccx  -> source-built CCX 2.23
    /usr/bin/cgx        -> Ubuntu-packaged CGX

## Runtime thread control

The image supports the usual thread control through:

    OMP_NUM_THREADS

Example:

    docker run --rm \
      -e OMP_NUM_THREADS=4 \
      -v "$PWD":/work \
      -w /work \
      ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 \
      ccx model

For some CCX workflows, this variable can also be relevant:

    CCX_NPROC_EQUATION_SOLVER

## Validation checks

### Executables

Expected command:

    docker run --rm ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 bash -lc '
      which ccx
      which cgx
      which python3 || true
      which gmsh || true
    '

Expected result:

    /usr/local/bin/ccx
    /usr/bin/cgx

No Python virtual environment and no Gmsh should be present in the solver-core image.

### CCX version

Command:

    docker run --rm ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 ccx -v

Expected result:

    This is Version 2.23

### SPOOLES-MT runtime check

Use a small CCX input file with:

    *STATIC,SOLVER=SPOOLES

Run with:

    docker run --rm \
      -e OMP_NUM_THREADS=4 \
      -v "$PWD":/work \
      -w /work \
      ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 \
      bash -lc 'ccx mt_check && grep -Ei "spooles|cpu|thread" mt_check.dat mt_check.sta spooles.out 2>/dev/null || true'

Expected CCX output includes:

    Factoring the system of equations using the symmetric spooles solver
    Using up to 4 cpu(s) for spooles.

For very small models, `spooles.out` may still report:

    Using 1 threads

This is not necessarily an error. Very small systems may not benefit from or trigger meaningful parallel factorization.

For a larger validation model, expected output can include:

    spooles.out: Using 4 threads

## Known observation

A small benchmark with approximately 10,890 equations showed:

    OMP_NUM_THREADS=1:
      Total CalculiX Time: about 0.77 s

    OMP_NUM_THREADS=4:
      Total CalculiX Time: about 1.15 s
      spooles.out: Using 4 threads

The 4-thread run was slower for this small model because thread overhead dominated. This does not invalidate the SPOOLES-MT build.

The important validation point is that `spooles.out` confirmed real multi-threaded SPOOLES usage.

## Final image size

The cleaned solver-core image is significantly smaller than earlier mixed solver/lab images.

Observed local image size:

    ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04
      approximately 1.15 GB uncompressed
      approximately 284 MB compressed

This is expected because Python, PyVista, VTK, Gmsh, ParaView, and JupyterLab are intentionally excluded.

## Do not regress

When rebuilding this image, do not remove the following critical build details:

    timings.h patch
    -fopenmp
    -DUSE_MT=1
    -I/tmp/calculix-build/SPOOLES.2.2
    spoolesMT.a
    spooles.a
    -lgomp
    -lpthread

Removing any of these can break the SPOOLES-MT build or silently fall back to a non-MT configuration.
