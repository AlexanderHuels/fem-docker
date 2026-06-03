# Lab 001 — Cantilever Shell Benchmark

This lab defines a CalculiX-based cantilever shell benchmark inspired by a classical computational structural engineering example.

The goal is not to reproduce book figures or text, but to build an independent open-source FEM workflow using CalculiX 2.23, Docker and Python.

## Unit system

- Force: N
- Length: mm
- Stress: MPa = N/mm²

## Geometry

- Beam length: L = 1000 mm
- Beam height: b = 100 mm
- Shell thickness: s = 20 mm

The shell mid-surface is modeled as a rectangular surface.

## Material

Aluminium:

- Young's modulus: E = 71000 MPa
- Poisson's ratio: nu = 0.3
- Shear modulus: G = 27307 MPa

## Boundary conditions

- Left end: clamped
- Right end: loaded in vertical bending/shear

## Load

- Total vertical load: F = 1000 N
- Applied as two nodal loads of 500 N each near the center of the free end

## Static reference result

The expected analytical tip displacement is approximately:

- delta = 2.82 mm

A comparable Abaqus shell model reports approximately:

- max displacement magnitude = 2.83 mm

## Buckling reference result

The theoretical critical load is approximately:

- Pcr = 23560 N

A comparable Abaqus shell model reports approximately:

- Pcr = 23150 N

## Planned CalculiX workflow

1. Generate a rectangular shell mesh
2. Apply clamped boundary conditions at the left edge
3. Apply the 1000 N vertical load at the free edge
4. Run a static CalculiX analysis
5. Compare the CalculiX displacement result with the analytical value
6. Extend the example to linear buckling
