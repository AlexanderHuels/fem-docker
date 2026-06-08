# PrePoMax Wine Image for Ubuntu 24.04

## Image

Local test image:

    prepomax-wine:ubuntu24.04-test

Planned public image name, pending redistribution/licensing review:

    ale10tech/prepomax-wine:ubuntu24.04

## Purpose

This image provides an experimental Ubuntu 24.04 based Wine runtime for running the portable Windows PrePoMax release inside a Docker container.

PrePoMax itself is a Windows/.NET GUI application. Therefore this image is not a native Linux port of PrePoMax. It is an Ubuntu container with Wine, .NET Framework 4.8 and the portable PrePoMax package.

## Included components

The image contains:

* Ubuntu 24.04
* Wine 64-bit and 32-bit support
* Wine prefix under `/opt/wineprefix`
* .NET Framework 4.8 installed through winetricks
* Xvfb for headless GUI smoke tests
* PrePoMax v2.5.0 portable package
* PrePoMax executable: `/opt/prepomax/PrePoMax.exe`
* bundled Windows CalculiX solver: `/opt/prepomax/Solver/ccx_dynamic.exe`
* wrapper: `/usr/local/bin/prepomax`
* wrapper: `/usr/local/bin/prepomax-xvfb`

## Build

Build the local test image:

    docker build \
      --progress=plain \
      -f images/prepomax-wine/Dockerfile \
      -t prepomax-wine:ubuntu24.04-test \
      images/prepomax-wine 2>&1 | tee /tmp/prepomax-wine-build.log

The .NET Framework 4.8 installation through winetricks can take a long time. Build times of 30 to 60 minutes are possible.

## Validation

### Basic file validation

Command:

    docker run --rm prepomax-wine:ubuntu24.04-test bash -lc '
      echo "--- wrappers ---"
      which prepomax
      which prepomax-xvfb

      echo
      echo "--- PrePoMax ---"
      ls -lh /opt/prepomax/PrePoMax.exe

      echo
      echo "--- bundled solver ---"
      ls -lh /opt/prepomax/Solver/ccx_dynamic.exe

      echo
      echo "--- Wine prefix ---"
      ls -ld /opt/wineprefix
    '

Observed validation result:

    /usr/local/bin/prepomax
    /usr/local/bin/prepomax-xvfb
    /opt/prepomax/PrePoMax.exe
    /opt/prepomax/Solver/ccx_dynamic.exe
    /opt/wineprefix

### Xvfb start smoke

Command:

    docker run --rm prepomax-wine:ubuntu24.04-test bash -lc '
      timeout --kill-after=5s 45s prepomax-xvfb
      code=$?
      echo "exit code: $code"
    '

Observed result:

    X connection to :99 broken (explicit kill or server shutdown).
    exit code: 124

This is acceptable for the smoke test. Exit code 124 means the timeout stopped the GUI application after the configured runtime.

### Direct GUI test from graphical Ubuntu VM

Run this from a graphical Ubuntu VM terminal, not from a PowerShell SSH session:

    xhost +local:root

    docker run --rm -it \
      -e DISPLAY="$DISPLAY" \
      -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
      -v "$PWD:/work" \
      -w /work \
      prepomax-wine:ubuntu24.04-test \
      prepomax

    xhost -local:root

Observed result:

    PrePoMax GUI opens successfully.

## Recommended workflow

This image should be treated as a GUI/preprocessing environment.

For reproducible Linux solver runs, prefer exporting an input deck from PrePoMax and solving it with the dedicated CalculiX core image:

    docker run --rm \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 \
      ccx model

## Current status

Validated locally:

* Docker build
* Wine prefix
* .NET Framework 4.8 installation
* PrePoMax executable present
* bundled Windows `ccx_dynamic.exe` present
* `prepomax` wrapper
* `prepomax-xvfb` wrapper
* Xvfb start smoke
* direct GUI start from graphical Ubuntu VM

Not yet done:

* public Docker Hub push
* redistribution/licensing review for packaging PrePoMax, bundled Windows CalculiX executable and third-party DLLs
* model open/save validation
* INP export validation
* solver execution validation inside Wine

## Notes

This image is experimental.

Do not treat it as a native Linux PrePoMax port. It is a Wine-based runtime image.

The image is intentionally not pushed to Docker Hub until redistribution and licensing implications are clarified.
