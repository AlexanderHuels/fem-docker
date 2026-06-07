FROM ubuntu:24.04

LABEL maintainer="Alex"
LABEL org.opencontainers.image.title="freecad"
LABEL org.opencontainers.image.description="Ubuntu 24.04 based FreeCAD GUI and CLI container using the official FreeCAD AppImage"
LABEL org.opencontainers.image.version="freecad1.1.1-ubuntu24.04"
LABEL org.opencontainers.image.licenses="LGPL-2.0-or-later and package-specific licenses"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV FONTCONFIG_FILE=/etc/fonts/fonts.conf
ENV FONTCONFIG_PATH=/etc/fonts
ENV FREECAD_VERSION=1.1.1
ENV FREECAD_APPIMAGE=FreeCAD_1.1.1-Linux-x86_64-py311.AppImage
ENV FREECAD_URL=https://github.com/FreeCAD/FreeCAD/releases/download/1.1.1/FreeCAD_1.1.1-Linux-x86_64-py311.AppImage
ENV FREECAD_HOME=/opt/freecad

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    file \
    bash \
    xz-utils \
    python3 \
    python3-pip \
    xvfb \
    xauth \
    libgl1 \
    libgl1-mesa-dri \
    libglx-mesa0 \
    libegl1 \
    libosmesa6 \
    libglu1-mesa \
    libopengl0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxi6 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb1 \
    libxcb-cursor0 \
    libxcb-keysyms1 \
    libxcb-image0 \
    libxcb-shm0 \
    libxcb-icccm4 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libsm6 \
    libice6 \
    libfontconfig1 \
    fontconfig \
    fonts-dejavu-core \
    libfreetype6 \
    libdbus-1-3 \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxss1 \
    && fc-cache -f -v >/dev/null || true \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/freecad-download && \
    cd /opt/freecad-download && \
    wget -O "${FREECAD_APPIMAGE}" "${FREECAD_URL}" && \
    chmod +x "${FREECAD_APPIMAGE}" && \
    "./${FREECAD_APPIMAGE}" --appimage-extract && \
    mv squashfs-root "${FREECAD_HOME}" && \
    rm -rf /opt/freecad-download

RUN printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'exec /opt/freecad/usr/bin/freecad "$@"' \
    > /usr/local/bin/freecad && \
    chmod +x /usr/local/bin/freecad && \
    printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'exec /opt/freecad/usr/bin/freecadcmd "$@"' \
    > /usr/local/bin/freecadcmd && \
    chmod +x /usr/local/bin/freecadcmd && \
    printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'exec xvfb-run -a -s "-screen 0 1280x1024x24" /opt/freecad/usr/bin/freecad "$@"' \
    > /usr/local/bin/freecad-xvfb && \
    chmod +x /usr/local/bin/freecad-xvfb && \
    printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'exec xvfb-run -a -s "-screen 0 1280x1024x24" /opt/freecad/usr/bin/freecadcmd "$@"' \
    > /usr/local/bin/freecadcmd-xvfb && \
    chmod +x /usr/local/bin/freecadcmd-xvfb

WORKDIR /work

CMD ["/bin/bash"]
