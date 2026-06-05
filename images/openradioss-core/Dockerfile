FROM ubuntu:24.04

LABEL maintainer="Alex"
LABEL org.opencontainers.image.title="openradioss-core"
LABEL org.opencontainers.image.description="Ubuntu 24.04 based OpenRadioss solver container"
LABEL org.opencontainers.image.version="latest-20260520-ubuntu24.04"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later and package-specific licenses"

ENV DEBIAN_FRONTEND=noninteractive
ENV OPENRADIOSS_RELEASE=latest-20260520
ENV OPENRADIOSS_ZIP=OpenRadioss_linux64.zip
ENV OPENRADIOSS_PATH=/opt/OpenRadioss
ENV RAD_CFG_PATH=/opt/OpenRadioss/hm_cfg_files
ENV RAD_H3D_PATH=/opt/OpenRadioss/extlib/h3d/lib/linux64
ENV LD_LIBRARY_PATH=/opt/OpenRadioss/extlib/hm_reader/linux64:/opt/OpenRadioss/extlib/h3d/lib/linux64
ENV OMP_STACKSIZE=400m
ENV PATH=/opt/OpenRadioss/exec:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    unzip \
    file \
    bash \
    libgfortran5 \
    libquadmath0 \
    libgomp1 \
    libstdc++6 \
    libgcc-s1 \
    zlib1g \
    openmpi-bin \
    libopenmpi3 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/openradioss-download && \
    cd /opt/openradioss-download && \
    wget -O "${OPENRADIOSS_ZIP}" \
        "https://github.com/OpenRadioss/OpenRadioss/releases/download/${OPENRADIOSS_RELEASE}/${OPENRADIOSS_ZIP}" && \
    unzip "${OPENRADIOSS_ZIP}" -d /opt && \
    chmod +x /opt/OpenRadioss/exec/* && \
    ln -s /opt/OpenRadioss/exec/starter_linux64_gf /usr/local/bin/starter_linux64_gf && \
    ln -s /opt/OpenRadioss/exec/engine_linux64_gf /usr/local/bin/engine_linux64_gf && \
    ln -s /opt/OpenRadioss/exec/engine_linux64_gf_ompi /usr/local/bin/engine_linux64_gf_ompi && \
    ln -s /opt/OpenRadioss/exec/anim_to_vtk_linux64_gf /usr/local/bin/anim_to_vtk_linux64_gf && \
    ln -s /opt/OpenRadioss/exec/th_to_csv_linux64_gf /usr/local/bin/th_to_csv_linux64_gf && \
    rm -rf /opt/openradioss-download

WORKDIR /work

CMD ["/bin/bash"]
