# Lab 005 — Case Definition

## Input source

This lab uses the cantilever shell benchmark as a simple and reproducible postprocessing case.

The geometry and load case are consistent with the previous cantilever labs.

## Technical objective

The objective is to demonstrate that:

- CalculiX results can be postprocessed with Python
- PyVista / VTK can render the FE model in a headless Docker workflow
- the setup can serve as a basis for later, more advanced engineering workflows

## First target

For the first iteration, the focus is not on advanced stress plots, but on a robust workflow:

- read mesh
- read nodal displacements
- render undeformed shape
- render deformed shape with scale factor
