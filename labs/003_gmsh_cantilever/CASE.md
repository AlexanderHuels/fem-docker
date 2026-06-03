# Lab 003 — Gmsh Cantilever Shell Workflow

This lab uses the same physical cantilever shell benchmark as Lab 001 and Lab 002, but generates the shell mesh with Gmsh.

## Unit system

- Force: N
- Length: mm
- Stress: MPa = N/mm²

## Geometry

- Beam length: L = 1000 mm
- Beam height: b = 100 mm
- Shell thickness: s = 20 mm

The shell mid-surface is modeled as a rectangular surface in the global X-Z plane.

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

## Mesh

Initial planned mesh:

    nx = 40
    nz = 5

The mesh is generated through Gmsh CLI in the Docker container.

## Analytical reference

Euler-Bernoulli tip displacement:

    delta = 2.816901 mm

Expected CalculiX result should be close to the Lab 001 / Lab 002 nx=40 result:

    U3 ≈ 2.830 mm
