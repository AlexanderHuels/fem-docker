# CalculiX Viz Docker Image

This image extends the CalculiX core image with additional libraries for headless PyVista / VTK rendering.

Base image:

    ale10tech/calculix-core:ccx2.23-ubuntu24.04

Visualization image:

    ale10tech/calculix-viz:ccx2.23-ubuntu24.04

## Purpose

The core image is intended for solver workflows with CalculiX, Gmsh and Python.

The viz image adds the dependencies needed for PyVista / VTK postprocessing and GIF/PNG rendering in a headless Docker workflow.

## Used by

    labs/005_pyvista_vtk/

## Example

From the repository root:

    ./labs/005_pyvista_vtk/run_pyvista_vtk.sh
