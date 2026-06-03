FROM ale10tech/calculix-core:ccx2.23-ubuntu24.04

LABEL org.opencontainers.image.title="CalculiX Viz"
LABEL org.opencontainers.image.description="CalculiX 2.23 image extended for headless PyVista/VTK rendering"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    xauth \
    libgl1 \
    libgl1-mesa-dri \
    libglx-mesa0 \
    libegl1 \
    libosmesa6 \
    libxrender1 \
    libxext6 \
    libxi6 \
    libx11-6 \
    libsm6 \
    libice6 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir imageio

ENV PYVISTA_OFF_SCREEN=true
ENV LIBGL_ALWAYS_SOFTWARE=1
