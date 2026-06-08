FROM ubuntu:24.04

LABEL org.opencontainers.image.title="fem-durability"
LABEL org.opencontainers.image.description="Ubuntu 24.04 based Python image for FEM durability, fatigue, rainflow, Miner damage and vibration fatigue workflows"
LABEL org.opencontainers.image.version="ubuntu24.04"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

ENV PYVISTA_OFF_SCREEN=true
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV PYVISTA_JUPYTER_BACKEND=static
ENV MPLBACKEND=Agg

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      bash \
      git \
      build-essential \
      python3 \
      python3-venv \
      python3-pip \
      python3-tk \
      python3-dev \
      libgl1 \
      libgl1-mesa-dri \
      libglx-mesa0 \
      libegl1 \
      libosmesa6 \
      libglu1-mesa \
      libx11-6 \
      libxext6 \
      libxrender1 \
      libxi6 \
      libxrandr2 \
      libxinerama1 \
      libxcursor1 \
      libxcomposite1 \
      libxdamage1 \
      libxfixes3 \
      libxss1 \
      libsm6 \
      libice6 \
      libfreetype6 \
      libfontconfig1 \
      libdbus-1-3 \
      libglib2.0-0 \
      libnss3 \
      libnspr4 \
      fontconfig \
      fonts-dejavu-core \
      fonts-liberation && \
    python3 -m venv "${VIRTUAL_ENV}" && \
    "${VIRTUAL_ENV}/bin/python" -m pip install --upgrade pip setuptools wheel && \
    "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir \
      numpy \
      scipy \
      pandas \
      matplotlib \
      meshio \
      pyvista \
      vtk \
      rainflow \
      fatpack \
      pylife \
      py-fatigue \
      FatPy \
      FatigueDS \
      FLife && \
    fc-cache -f -v >/dev/null || true && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /work

CMD ["bash"]
