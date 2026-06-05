# OpenRadioss Core Image on Ubuntu 24.04

This document describes the first OpenRadioss solver-core Docker image:

    ale10tech/openradioss-core:ubuntu24.04

## Purpose

This image provides a minimal OpenRadioss solver environment based on Ubuntu 24.04.

It is intended for:

    OpenRadioss Starter runs
    OpenRadioss Engine runs
    basic MPI-capable engine availability
    animation conversion
    time-history conversion

## OpenRadioss release

The image currently uses the official OpenRadioss Linux x86_64 release:

    latest-20260520
    OpenRadioss_linux64.zip

The release archive contains:

    OpenRadioss/exec/starter_linux64_gf
    OpenRadioss/exec/engine_linux64_gf
    OpenRadioss/exec/engine_linux64_gf_ompi
    OpenRadioss/exec/engine_linux64_gf_ompi_sp
    OpenRadioss/exec/engine_linux64_gf_sp
    OpenRadioss/exec/starter_linux64_gf_sp
    OpenRadioss/exec/anim_to_vtk_linux64_gf
    OpenRadioss/exec/th_to_csv_linux64_gf

## Important runtime libraries

The first runtime smoke test showed that `libquadmath.so.0` was missing.

The image therefore explicitly installs:

    libgfortran5
    libquadmath0
    libgomp1
    libstdc++6
    libgcc-s1
    zlib1g

Without `libquadmath0`, both Starter and Engine can fail with:

    error while loading shared libraries: libquadmath.so.0:
    cannot open shared object file: No such file or directory

## Environment variables

The image sets:

    OPENRADIOSS_PATH=/opt/OpenRadioss
    RAD_CFG_PATH=/opt/OpenRadioss/hm_cfg_files
    RAD_H3D_PATH=/opt/OpenRadioss/extlib/h3d/lib/linux64
    LD_LIBRARY_PATH=/opt/OpenRadioss/extlib/hm_reader/linux64:/opt/OpenRadioss/extlib/h3d/lib/linux64
    OMP_STACKSIZE=400m

The OpenRadioss executables are also available through `PATH`.

## Installed executable links

The image creates links in `/usr/local/bin` for:

    starter_linux64_gf
    engine_linux64_gf
    engine_linux64_gf_ompi
    anim_to_vtk_linux64_gf
    th_to_csv_linux64_gf

## Version validation

The following checks were successful:

    starter_linux64_gf -version
    engine_linux64_gf -version

Observed versions:

    OpenRadioss Starter
    Platform release : linux64
    Date of build : May 20 2026

    OpenRadios Engine
    Platform release : linux64_gf
    Date of build : May 20 2026

## Known issue: engine -help

The command:

    engine_linux64_gf -help

prints the command line help but then exits with code 139 due to a segmentation fault.

Observed backtrace includes:

    execargcheck_
    radioss0_
    main

This appears to affect the `-help` argument path. It did not block normal version checks or a real model run.

Use this for validation instead:

    engine_linux64_gf -version

and preferably a real Starter/Engine smoke test.

## Smoke test model

A real OpenRadioss smoke test was performed using the official ModelExchange tensile LAW2 example:

    Components/Materials/ElastoPlasticLaw/Law002/tensile_LAW2_0000.rad
    Components/Materials/ElastoPlasticLaw/Law002/tensile_LAW2_0001.rad

The tested commands were:

    starter_linux64_gf -i tensile_LAW2_0000.rad -np 1 -nt 1
    engine_linux64_gf -i tensile_LAW2_0001.rad -nt 1

Observed result:

    tensile_LAW2_0000.out:
      NORMAL TERMINATION
      0 ERROR(S)
      0 WARNING(S)

    tensile_LAW2_0001.out:
      NORMAL TERMINATION
      STARTER+ENGINE RUNTIME = 264.61s

This confirms that the image can execute a real Starter/Engine workflow.

## Example usage

From a directory containing an OpenRadioss model:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/openradioss-core:ubuntu24.04 \
      starter_linux64_gf -i model_0000.rad -np 1 -nt 1

Then run the engine:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/openradioss-core:ubuntu24.04 \
      engine_linux64_gf -i model_0001.rad -nt 1

## Do not regress

When modifying this image, do not remove:

    libquadmath0
    RAD_CFG_PATH
    RAD_H3D_PATH
    LD_LIBRARY_PATH
    OMP_STACKSIZE
    OpenRadioss executable links

These are required for reliable Starter/Engine execution.
