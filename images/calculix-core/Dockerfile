FROM ubuntu:24.04

LABEL maintainer="Alex"
LABEL org.opencontainers.image.title="calculix-core"
LABEL org.opencontainers.image.description="Ubuntu 24.04 based CalculiX CCX/CGX FEM container with Python tooling"
LABEL org.opencontainers.image.licenses="GPL-2.0-or-later and package-specific licenses"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    git \
    build-essential \
    gfortran \
    make \
    cmake \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libopenblas-dev \
    liblapack-dev \
    libarpack2-dev \
    libspooles-dev \
    libgl1 \
    libglu1-mesa \
    libxi6 \
    libxmu6 \
    libxext6 \
    libx11-6 \
    gmsh \
    calculix-ccx \
    calculix-cgx \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    numpy \
    scipy \
    pandas \
    matplotlib \
    meshio \
    pyvista \
    jupyterlab \
    ipykernel

WORKDIR /work

CMD ["/bin/bash"]
