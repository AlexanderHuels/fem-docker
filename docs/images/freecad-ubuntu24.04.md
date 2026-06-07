# FreeCAD Image on Ubuntu 24.04

This document describes the first FreeCAD Docker image:

    ale10tech/freecad:ubuntu24.04

## Purpose

This image provides a FreeCAD GUI and CLI environment based on Ubuntu 24.04.

It is intended for:

    FreeCAD GUI usage
    FreeCADCmd scripting
    headless CAD automation
    FCStd generation
    STEP export
    simple CAD/FEM preprocessing workflows

## FreeCAD source

Ubuntu 24.04 did not provide a usable `freecad` APT package in the tested package configuration.

Therefore this image uses the official FreeCAD AppImage release:

    FreeCAD 1.1.1
    FreeCAD_1.1.1-Linux-x86_64-py311.AppImage

The AppImage is downloaded during the Docker build and extracted with:

    --appimage-extract

The extracted application is installed under:

    /opt/freecad

This avoids FUSE/AppImage runtime issues inside Docker.

## Installed wrappers

The image provides the following wrapper commands:

    freecad
    freecadcmd
    freecad-xvfb
    freecadcmd-xvfb

The wrappers call:

    /opt/freecad/usr/bin/freecad
    /opt/freecad/usr/bin/freecadcmd

The Xvfb wrappers use:

    xvfb-run -a -s "-screen 0 1280x1024x24"

## Runtime fixes

The image includes X11, Qt, OpenGL and font packages required for FreeCAD GUI and headless operation.

Important settings:

    LANG=C.UTF-8
    LC_ALL=C.UTF-8
    FONTCONFIG_FILE=/etc/fonts/fonts.conf
    FONTCONFIG_PATH=/etc/fonts

Important packages include:

    xvfb
    xauth
    libgl1
    libgl1-mesa-dri
    libglx-mesa0
    libegl1
    libosmesa6
    libglu1-mesa
    libopengl0
    libx11-6
    libxext6
    libxrender1
    libxi6
    libxrandr2
    libxinerama1
    libxcursor1
    libxkbcommon0
    libxkbcommon-x11-0
    libxcb-cursor0
    fontconfig
    fonts-dejavu-core

## Validation

The following checks were successful.

### FreeCADCmd version

    freecadcmd --version

Observed:

    FreeCAD 1.1.1 Revision: 20260414

### FreeCADCmd with Xvfb

    freecadcmd-xvfb --version

Observed:

    FreeCAD 1.1.1 Revision: 20260414

### FreeCAD Python module import

A Python smoke test was executed through FreeCADCmd.

Validated imports:

    FreeCAD
    Part

### Geometry creation

A simple box geometry was created with:

    Part.makeBox(10.0, 20.0, 30.0)

### File export

The smoke test successfully wrote:

    freecad_box_smoke.FCStd
    freecad_box_smoke.step

The STEP file was written as ASCII STEP:

    ISO-10303-21

### Xvfb geometry export

The same geometry/export workflow was also validated through:

    freecadcmd-xvfb

This confirms that FreeCADCmd works both directly and through Xvfb.

## GUI validation

The FreeCAD GUI was tested in two ways.

### GUI through Xvfb

The GUI executable was started through:

    timeout 15s freecad-xvfb --version

Observed:

    freecad-xvfb exit code: 124

This is acceptable for the smoke test because `timeout` terminates the GUI after 15 seconds. The important result is that no missing-library, Qt, locale, or fontconfig error remained.

### Direct GUI in the Ubuntu VM

The FreeCAD GUI was also started directly from the graphical Ubuntu VM terminal.

Required host-side setup:

    xhost +local:root

Docker command:

    docker run --rm -it \
      -e DISPLAY="$DISPLAY" \
      -e QT_QPA_PLATFORM=xcb \
      -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
      -v "$PWD:/work" \
      -w /work \
      freecad:ubuntu24.04-test \
      freecad

After the test, X access should be restricted again:

    xhost -local:root

The FreeCAD GUI opened successfully in the VM.

## Known GUI notes

Direct GUI usage depends on the host display setup.

In a PowerShell to SSH to VM workflow, `DISPLAY` is usually empty and direct GUI usage is not expected to work.

For direct GUI usage, run the Docker command from a graphical terminal inside the VM or configure X11 forwarding/noVNC separately.

## Example CLI usage

From a directory containing a FreeCAD Python script:

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/freecad:ubuntu24.04 \
      freecadcmd script.py

## Example headless/Xvfb usage

    docker run --rm -it \
      --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" \
      -w /work \
      ale10tech/freecad:ubuntu24.04 \
      freecadcmd-xvfb script.py

## Example GUI usage in graphical VM

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

## Do not regress

When modifying this image, do not remove:

    AppImage extraction approach
    freecad wrapper
    freecadcmd wrapper
    freecad-xvfb wrapper
    freecadcmd-xvfb wrapper
    UTF-8 locale settings
    fontconfig settings
    X11 / Qt / OpenGL runtime libraries

These are required for reliable FreeCAD CLI, headless, and GUI workflows in Docker.
