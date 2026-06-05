# FEM Pre/Post Image on Ubuntu 24.04

This document describes the first `fem-prepost` Docker image:

    ale10tech/fem-prepost:ubuntu24.04

## Purpose

This image provides a pre/postprocessing environment for open-source FEM workflows.

It is intended for:

    result visualization
    batch postprocessing
    screenshot generation
    mesh conversion
    Gmsh-based preprocessing
    CGX-based CalculiX result inspection
    ParaView client/server workflows
    PyVista/VTK scripting

## Image contents

The image contains:

    Ubuntu 24.04
    ParaView 5.11.2
    pvpython
    pvbatch
    pvserver
    Gmsh 4.12.1
    CGX
    Python virtual environment
    VTK
    PyVista
    meshio
    NumPy
    SciPy
    Pandas
    Matplotlib
    imageio
    trame packages
    Xvfb
    Mesa/OpenGL/EGL/OSMesa runtime libraries

## Why this image is separate from calculix-core

The `calculix-core` image is solver-focused and intentionally small.

The `fem-prepost` image contains larger visualization and Python tooling. This keeps the solver image clean while still providing a powerful visualization and postprocessing environment.

## Headless rendering notes

The image includes the headless rendering settings that were previously validated in the older `calculix-viz` image:

    PYVISTA_OFF_SCREEN=true
    LIBGL_ALWAYS_SOFTWARE=1
    PYVISTA_JUPYTER_BACKEND=static

It also includes the required Mesa/OpenGL/X11 runtime packages:

    xvfb
    xauth
    libgl1
    libgl1-mesa-dri
    libglx-mesa0
    libegl1
    libosmesa6
    libxrender1
    libxext6
    libxi6
    libx11-6
    libsm6
    libice6

## PyVista offscreen validation

PyVista offscreen rendering was validated successfully inside the container without a host display.

Expected result:

    pyvista_offscreen_test.png: PNG image data, 1024 x 768

A warning like this can appear:

    vtkXOpenGLRenderWindow: WARN| bad X server connection. DISPLAY=

This warning is acceptable if the screenshot is still created successfully.

## ParaView pvpython rendering

Direct `pvpython` rendering without a display can fail in a pure SSH/Docker workflow because the Ubuntu ParaView package may try to use an X-based render window.

Observed failure mode:

    vtkXOpenGLRenderWindow::Render()
    vtkXRenderWindowInteractor::Initialize()
    XSync
    SIGSEGV

This is expected when both host and container have no display:

    HOST DISPLAY=
    CONTAINER DISPLAY=

For this reason, the image provides wrapper scripts:

    /usr/local/bin/pvpython-xvfb
    /usr/local/bin/pvbatch-xvfb

These wrappers run ParaView through Xvfb:

    xvfb-run -a -s "-screen 0 1024x768x24" pvpython "$@"
    xvfb-run -a -s "-screen 0 1024x768x24" pvbatch "$@"

## pvpython-xvfb validation

The wrapper was validated with a ParaView sphere screenshot.

Expected result:

    pvpython-xvfb import: OK
    pvpython-xvfb screenshot written
    pvpython_xvfb_wrapper_sphere.png: PNG image data, 1024 x 768

## pvserver validation

`pvserver` was validated successfully.

Expected output:

    Waiting for client...
    Connection URL: cs://<container-id>:11111
    Accepting connection(s): <container-id>:11111

For client/server usage, the container can be started with:

    docker run --rm \
      -p 11111:11111 \
      ale10tech/fem-prepost:ubuntu24.04 \
      pvserver --server-port=11111

From outside the container, connect the ParaView GUI client to:

    <VM-IP>:11111

or, from inside the VM:

    localhost:11111

The container-internal hostname shown in the pvserver log is not usually the address to use from the Windows host.

## Recommended usage patterns

### PyVista batch rendering

Use normal Python:

    python3 script.py

### ParaView batch rendering

Use:

    pvpython-xvfb script.py

or:

    pvbatch-xvfb script.py

### Interactive ParaView workflows

Recommended options:

    ParaView GUI directly in the graphical VM
    ParaView GUI on Windows connected to pvserver in the container
    X11 forwarding with a Windows X server
    noVNC-based GUI workflow in a future image

For the current SSH/PowerShell workflow, plain interactive GUI rendering is not expected to work without an X display.

## Validation checklist

The following tools were validated:

    paraview
    pvpython
    pvbatch
    pvserver
    gmsh
    cgx
    python3 in /opt/venv
    vtk
    pyvista
    meshio
    numpy
    scipy
    pandas
    matplotlib
    imageio

The following workflows were validated:

    PyVista offscreen screenshot
    pvpython rendering through xvfb-run
    pvpython-xvfb wrapper
    pvserver startup on port 11111

## Do not regress

When rebuilding or modifying this image, do not remove:

    xvfb
    xauth
    Mesa/OpenGL/EGL/OSMesa libraries
    PYVISTA_OFF_SCREEN=true
    LIBGL_ALWAYS_SOFTWARE=1
    pvpython-xvfb
    pvbatch-xvfb

These are required for reliable headless rendering in SSH/Docker workflows.
