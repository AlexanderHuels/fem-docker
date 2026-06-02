#!/usr/bin/env bash
set -e

if [ $# -ne 1 ]; then
    echo "Usage: run_ccx.sh <jobname_without_inp>"
    echo "Example: run_ccx.sh cantilever"
    exit 1
fi

JOBNAME="$1"

docker run --rm -it \
    --user "$(id -u):$(id -g)" \
    -v "$PWD:/work" \
    -w /work \
    calculix-core:ubuntu24.04 \
    ccx "$JOBNAME"
