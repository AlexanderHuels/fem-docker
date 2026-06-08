FROM ubuntu:24.04

LABEL org.opencontainers.image.title="prepomax-wine"
LABEL org.opencontainers.image.description="Experimental Ubuntu 24.04 + Wine runtime for the portable Windows PrePoMax release"
LABEL org.opencontainers.image.version="prepomax2.5.0-wine-ubuntu24.04"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

ENV WINEPREFIX=/opt/wineprefix
ENV WINEARCH=win64
ENV WINEDEBUG=-all
ENV DISPLAY=:99

ENV PREPOMAX_VERSION=2.5.0
ENV PREPOMAX_ZIP_URL="https://prepomax.fs.um.si/Files/Downloads/PrePoMax%20v2.5.0.zip"
ENV PREPOMAX_HOME=/opt/prepomax

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      wget \
      curl \
      unzip \
      file \
      bash \
      xvfb \
      xauth \
      cabextract \
      p7zip-full \
      winbind \
      wine \
      wine64 \
      wine32:i386 \
      winetricks \
      fontconfig \
      fonts-dejavu-core \
      fonts-liberation \
      libgl1 \
      libgl1-mesa-dri \
      libglx-mesa0 \
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
      libnspr4 && \
    fc-cache -f -v >/dev/null || true && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p "${WINEPREFIX}" && \
    xvfb-run -a -s "-screen 0 1280x1024x24" wineboot --init && \
    wineserver -w

RUN xvfb-run -a -s "-screen 0 1280x1024x24" winetricks -q win10 && \
    wineserver -w

RUN xvfb-run -a -s "-screen 0 1280x1024x24" winetricks -q dotnet48 && \
    wineserver -w

RUN xvfb-run -a -s "-screen 0 1280x1024x24" winecfg /v win10 && \
    wineserver -w

RUN mkdir -p /opt/prepomax-download && \
    cd /opt/prepomax-download && \
    wget -O prepomax.zip "${PREPOMAX_ZIP_URL}" && \
    unzip -q prepomax.zip && \
    mv "PrePoMax v${PREPOMAX_VERSION}" "${PREPOMAX_HOME}" && \
    rm -rf /opt/prepomax-download

RUN printf '%s\n' \
      '#!/usr/bin/env bash' \
      'set -e' \
      'export WINEPREFIX="${WINEPREFIX:-/opt/wineprefix}"' \
      'export WINEARCH="${WINEARCH:-win64}"' \
      'export WINEDEBUG="${WINEDEBUG:--all}"' \
      'cd /opt/prepomax' \
      'exec wine "/opt/prepomax/PrePoMax.exe" "$@"' \
      > /usr/local/bin/prepomax && \
    printf '%s\n' \
      '#!/usr/bin/env bash' \
      'set -e' \
      'exec xvfb-run -a -s "-screen 0 1280x1024x24" prepomax "$@"' \
      > /usr/local/bin/prepomax-xvfb && \
    chmod +x /usr/local/bin/prepomax /usr/local/bin/prepomax-xvfb

WORKDIR /work

CMD ["bash"]
