FROM ubuntu:24.04

LABEL maintainer="Alex"
LABEL org.opencontainers.image.title="fem-prepost"
LABEL org.opencontainers.image.description="Ubuntu 24.04 FEM pre/postprocessing image with ParaView, PyVista, VTK, meshio, Gmsh, CGX and headless rendering support"
LABEL org.opencontainers.image.version="ubuntu24.04"
LABEL org.opencontainers.image.licenses="GPL-2.0-or-later and package-specific licenses"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    git \
    bash \
    file \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    paraview \
    python3-paraview \
    gmsh \
    calculix-cgx \
    xvfb \
    xauth \
    libgl1 \
    libgl1-mesa-dri \
    libglx-mesa0 \
    libegl1 \
    libosmesa6 \
    libglu1-mesa \
    libxrender1 \
    libxext6 \
    libxi6 \
    libx11-6 \
    libsm6 \
    libice6 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Headless/off-screen rendering defaults for PyVista/VTK in Docker.
# These settings are inherited from the earlier calculix-viz image.
ENV PYVISTA_OFF_SCREEN=true
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV PYVISTA_JUPYTER_BACKEND=static

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    numpy \
    scipy \
    pandas \
    matplotlib \
    meshio \
    pyvista \
    imageio \
    trame \
    trame-vtk \
    trame-vuetify

RUN printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'exec xvfb-run -a -s "-screen 0 1024x768x24" pvpython "$@"' \
    > /usr/local/bin/pvpython-xvfb && \
    chmod +x /usr/local/bin/pvpython-xvfb && \
    printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'exec xvfb-run -a -s "-screen 0 1024x768x24" pvbatch "$@"' \
    > /usr/local/bin/pvbatch-xvfb && \
    chmod +x /usr/local/bin/pvbatch-xvfb

WORKDIR /work

CMD ["/bin/bash"]
