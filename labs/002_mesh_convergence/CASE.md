# Lab 002 — Mesh Convergence Study

This lab uses the same physical cantilever shell benchmark as Lab 001, but varies the mesh density along the beam length.

## Unit system

- Force: N
- Length: mm
- Stress: MPa = N/mm²

## Geometry

- Beam length: L = 1000 mm
- Beam height: b = 100 mm
- Shell thickness: s = 20 mm

## Material

Aluminium:

- Young's modulus: E = 71000 MPa
- Poisson's ratio: nu = 0.3

## Boundary conditions

- Left edge: clamped
- Right edge: loaded in vertical bending/shear

## Load

- Total vertical load: F = 1000 N
- Applied as two nodal loads of 500 N each near the center of the free end

## Analytical reference

Euler-Bernoulli tip displacement:

    delta = F * L^3 / (3 * E * I)

with:

    I = s * b^3 / 12

Expected reference value:

    delta = 2.816901 mm

## Mesh variants

Initial planned variants:

    nx = 5, 10, 20, 40, 80
    nz = 5

where:

- nx = number of shell elements along beam length
- nz = number of shell elements over beam height

## Engineering purpose

The aim is to show that a reproducible FEM workflow should include verification steps such as mesh convergence, not only a single solver run.
