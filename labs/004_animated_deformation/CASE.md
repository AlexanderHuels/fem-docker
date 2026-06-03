# Lab 004 — Animated Cantilever Deformation

This lab uses the same cantilever shell benchmark as the previous labs, but requests displacement output for all shell nodes.

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

## Mesh

Initial mesh:

    nx = 40
    nz = 5

## Output

Unlike Lab 001, this lab prints displacements for all shell nodes. These nodal displacements are used to draw an animated deformation GIF.

## Reference result

Expected tip displacement:

    Analytical: 2.816901 mm
    CalculiX:   about 2.830381 mm
