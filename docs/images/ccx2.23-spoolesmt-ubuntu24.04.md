# CalculiX CCX 2.23 with SPOOLES-MT on Ubuntu 24.04

This image provides a source-built CalculiX CCX 2.23 executable on Ubuntu 24.04 with source-built SPOOLES-MT support.

## Image

```bash
docker pull ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04
```

Image tag:

```text
ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04
```

Verified Docker Hub digest:

```text
sha256:922434dcb01b11ee7a631629b5fe76009804878076875da50e19a9a330d78495
```

Platform:

```text
linux/amd64
```

## Purpose

The standard `ccx2.23-ubuntu24.04` image builds CCX 2.23 against Ubuntu's system SPOOLES library.

This image is different:

- CCX 2.23 is built from upstream source.
- SPOOLES 2.2 is built from source.
- SPOOLES-MT is built via `SPOOLES.2.2/MT/src/spoolesMT.a`.
- CCX is compiled with multi-threading support.
- CCX links against the source-built SPOOLES-MT libraries instead of Ubuntu's dynamic `libspooles.so`.

This image is intended for experiments and larger models where the SPOOLES factorization step can benefit from multiple CPU cores.

## Run a CCX job

Run a CCX job from the current directory:

```bash
docker run --rm \
  -e OMP_NUM_THREADS=4 \
  -e CCX_NPROC_EQUATION_SOLVER=4 \
  -v "$PWD:/work" \
  ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 \
  ccx jobname
```

Replace `jobname` with the input file name without `.inp`.

Example:

```text
beam.inp -> ccx beam
```

## Thread control

The following environment variables can be used to control the number of CPUs used by CCX/SPOOLES-MT:

```bash
-e OMP_NUM_THREADS=4
-e CCX_NPROC_EQUATION_SOLVER=4
```

For small models, multi-threading may not improve runtime because overhead can dominate. The image is mainly useful for larger equation systems where matrix factorization time is relevant.

## Verification

### CCX version

```bash
docker run --rm ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 ccx -v
```

Expected output:

```text
This is Version 2.23
```

### Dynamic SPOOLES link check

```bash
docker run --rm ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 bash -lc '
ldd "$(command -v ccx)" | grep -i spooles || echo "OK: no dynamic libspooles linked"
ldd "$(command -v ccx)" | grep -Ei "gomp|pthread" || true
'
```

Expected output includes:

```text
OK: no dynamic libspooles linked
libgomp.so.1 => ...
```

### Solver runtime check

Using the repository smoke test:

```bash
rm -rf /tmp/ccx223-spoolesmt-dockerhub-test
mkdir -p /tmp/ccx223-spoolesmt-dockerhub-test

cp examples/ccx_smoke_test/cantilever.inp \
   /tmp/ccx223-spoolesmt-dockerhub-test/

docker run --rm \
  -e OMP_NUM_THREADS=4 \
  -e CCX_NPROC_EQUATION_SOLVER=4 \
  -v /tmp/ccx223-spoolesmt-dockerhub-test:/work \
  ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04 \
  bash -lc '
    cd /work
    ccx cantilever 2>&1 | tee ccx_spoolesmt_dockerhub_test.log
    grep -Ei "Factoring.*spooles|Using up to .*cpu.*spooles" ccx_spoolesmt_dockerhub_test.log
  '
```

Expected output:

```text
Factoring the system of equations using the symmetric spooles solver
Using up to 4 cpu(s) for spooles.
```

## Validation result

The Docker Hub image was tested successfully with:

```text
CCX version: 2.23
Dynamic libspooles link: no
OpenMP runtime: libgomp.so.1
SPOOLES-MT runtime usage: Using up to 4 cpu(s) for spooles.
```

## Related image variants

| Image tag | CCX version | Solver setup | Notes |
|---|---:|---|---|
| `ale10tech/calculix-core:ccx2.21-ubuntu24.04` | 2.21 | Ubuntu package build | Stable Ubuntu baseline |
| `ale10tech/calculix-core:ccx2.23-ubuntu24.04` | 2.23 | Source-built CCX with Ubuntu system SPOOLES | Standard CCX 2.23 image |
| `ale10tech/calculix-core:ccx2.23-spoolesmt-ubuntu24.04` | 2.23 | Source-built CCX with source-built SPOOLES-MT | Multi-threaded SPOOLES variant |
