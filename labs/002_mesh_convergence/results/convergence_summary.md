# Lab 002 — Mesh Convergence Results

Cantilever shell benchmark solved with CalculiX 2.23 in Docker.

Analytical Euler-Bernoulli reference: 2.816901 mm
Finest FE reference used here: nx=80, U3=2.832489 mm

| nx | elements | element size x [mm] | mean abs(U3) [mm] | error vs analytical [%] | error vs finest [%] |
|---:|---------:|--------------------:|---------------:|------------------------:|--------------------:|
| 5 | 25 | 200.000 | 2.765670 | -1.819 | -2.359 |
| 10 | 50 | 100.000 | 2.808822 | -0.287 | -0.836 |
| 20 | 100 | 50.000 | 2.824509 | 0.270 | -0.282 |
| 40 | 200 | 25.000 | 2.830381 | 0.479 | -0.074 |
| 80 | 400 | 12.500 | 2.832489 | 0.553 | 0.000 |

Observation:

- The computed tip displacement increases with mesh refinement.
- The coarse nx=5 mesh is clearly too stiff.
- The solution is already close to the finest nx=80 reference from nx=20 onward.
- The comparison against Euler-Bernoulli theory is useful as an analytical check, but the FE shell model converges toward its own shell-model reference solution.
