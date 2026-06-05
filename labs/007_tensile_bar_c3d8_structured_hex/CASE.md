# Lab 007 — Structured C3D8 Hex Tensile Dogbone

## Objective

Build and validate a structured hexahedral C3D8 reference mesh for the same full S355MC tensile dogbone specimen used in Lab 006.

The purpose is not to convert the existing C3D10 tetrahedral mesh. Instead, this lab generates a new structured hexahedral mesh for the same full specimen geometry.

## Scope

- Full shoulder-type dogbone specimen
- Symmetric mesh topology about x = 0, y = 0 and z = 0
- No symmetry boundary conditions
- C3D8 solid elements
- Same S355MC material card concept as Lab 006
- Same displacement-controlled tensile setup
- Force-displacement postprocessing
- PyVista field rendering and history GIF generation
- Comparison against Lab 006 C3D10 results

## Mesh design decision

The first structured C3D8 version uses explicit mid-planes:

- x = 0 symmetry station is present
- y = 0 centerline nodes are present
- z = 0 mid-thickness node plane is present

Thickness setup:

- sheet thickness: 2.0 mm
- thickness element layers: 4
- thickness node planes: 5
- approximate element thickness: 0.5 mm

This gives a better structured hexahedral reference mesh than only two thickness layers while keeping the complete specimen model.

## Mesh quality

Generated mesh:

- nodes: 7085
- C3D8 elements: 5184
- all element orientation indicators positive
- no near-zero orientation indicators
- minimum edge length: 0.5 mm
- maximum edge length: 2.5 mm
- maximum rough edge-length ratio: 5.0

The mesh is suitable as a first structured C3D8 comparison model.

## Boundary and loading concept

The model is displacement-controlled:

- LEFT_END: U1 = 0
- RIGHT_END: U1 = 2.0 mm
- one left-end center node: U2 = U3 = 0
- one additional left-end node: U3 = 0

The additional constraints only suppress rigid-body motion. They are not symmetry boundary conditions.

## Result request

The CalculiX input requests:

    S, E, PEEQ

The FRD result blocks show:

    STRESS    6 components
    TOSTRAIN  6 components
    PE        1 scalar component

In CalculiX FRD output, the scalar `PE` block corresponds to the equivalent plastic strain requested as `PEEQ`.

For clarity, figures and summaries refer to this field as:

    PE / PEEQ equivalent plastic strain [-]

## Main numerical result

Final global response:

- final displacement: 2.000000 mm
- final tensile force: 10833.285640 N
- engineering stress estimate: 433.331426 MPa

Reaction-force equilibrium:

- LEFT_END RF1 sum: -10833.285640 N
- RIGHT_END RF1 sum: 10833.285640 N

## Comparison to Lab 006

The final C3D8 force is close to the Lab 006 C3D10 force level.

Approximate final-force comparison:

- C3D10 Lab 006: about 10.76 kN
- C3D8 Lab 007: about 10.83 kN
- difference: about +0.7 %

This is considered plausible for a first structured C3D8 hexahedral reference mesh.

## Common postprocessing

This lab introduced reusable common postprocessing modules under:

    labs/common/python/

The common modules separate mesh parsing, FRD result parsing, PyVista grid creation, plotting and GIF generation from lab-specific wrappers.

Supported common functionality:

- C3D8 and C3D10 mesh reading
- PyVista grid generation for HEXAHEDRON and QUADRATIC_TETRA cells
- FRD history parsing for U, STRESS and PE
- von Mises calculation from stress tensors
- force-displacement SVG plotting
- final-state PyVista PNG rendering
- history GIF rendering
- discrete or continuous legends
- optional Abaqus-like colormap
- optional mesh visibility
- optional undeformed background
- manual color limits

## Tracked outputs

Selected lightweight outputs are tracked for documentation:

- structured mesh previews
- force-displacement curve SVG
- final displacement PNG
- displacement history GIF
- von Mises PNG with Abaqus-like colormap
- von Mises history GIF with Abaqus-like colormap
- PE / PEEQ history GIF
- summary text files
- generated mesh CSV files

Large solver result files are not tracked.
