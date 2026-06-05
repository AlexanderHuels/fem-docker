# Lab 007 — Structured C3D8 Hex Tensile Dogbone

This lab continues the S355MC tensile specimen workflow from Lab 006 with a structured C3D8 hexahedral mesh.

The specimen remains the full dogbone geometry. The mesh is generated symmetrically about the specimen mid-planes, but no symmetry boundary conditions are applied.

## Objective

- Build a structured C3D8 hexahedral mesh for the same S355MC tensile dogbone geometry used in Lab 006.
- Run a nonlinear elastoplastic displacement-controlled tensile simulation with CalculiX.
- Compare the global force-displacement response against the Lab 006 C3D10 reference.
- Use common postprocessing scripts for force-displacement plots, PyVista field plots and animated history GIFs.

## Mesh concept

The first structured C3D8 mesh uses four element layers through the 2 mm sheet thickness, resulting in five node planes:

    z = -1.0, -0.5, 0.0, 0.5, 1.0 mm

The mesh contains explicit mid-planes:

- x = 0
- y = 0
- z = 0

These are mesh symmetry planes only. They are not model-reduction planes.

## Mesh statistics

Generated structured mesh:

- nodes: 7085
- C3D8 elements: 5184
- x stations: 109
- width stations: 13
- z stations: 5
- thickness layers: 4
- minimum edge length: 0.5 mm
- maximum edge length: 2.5 mm
- maximum rough edge-length ratio: 5.0
- orientation check: all elements positive

## CalculiX setup

The model uses:

- element type: C3D8
- material: S355MC elastoplastic material card reused from Lab 006
- load case: displacement-controlled tensile loading
- right-end displacement: 2.0 mm
- full specimen model, no symmetry boundary conditions

Boundary condition concept:

- LEFT_END, U1 = 0
- RIGHT_END, U1 = 2.0 mm
- one left-end center node fixed in U2/U3
- one additional left-end node fixed in U3

This removes rigid-body motion without reducing the specimen model.

## Requested result fields

The CalculiX input requests:

    *EL FILE
    S, E, PEEQ

In the CalculiX FRD file, the equivalent plastic strain requested as `PEEQ` is stored with the result label `PE`.

This is not the Abaqus plastic strain tensor `PE`. In this lab, the plotted scalar field `PE / PEEQ [-]` means:

    equivalent plastic strain requested as PEEQ, stored in FRD as PE

## Simulation result

Final global tensile response:

- final right-end displacement: 2.000000 mm
- final tensile force: 10833.285640 N
- initial cross-section S0: 25.000000 mm²
- engineering stress estimate: 433.331426 MPa

Reaction-force equilibrium:

- LEFT_END RF1 sum: -10833.285640 N
- RIGHT_END RF1 sum: 10833.285640 N

## Lab 006 comparison

Compared with the Lab 006 C3D10 reference, the final force is very close.

Approximate comparison:

- Lab 006 C3D10 final force: about 10.76 kN
- Lab 007 C3D8 final force: about 10.83 kN
- difference: about +0.7 %

This is plausible for a structured C3D8 reference mesh compared with the Lab 006 C3D10 tetrahedral reference.

## Common postprocessing

Lab 007 uses reusable common postprocessing scripts from:

    labs/common/python/

Common scripts introduced or used here:

- `ccx_inp_mesh.py`
- `ccx_pyvista_grid.py`
- `ccx_frd_results.py`
- `create_force_displacement_svg.py`
- `render_final_field_pyvista.py`
- `create_history_gif_pyvista.py`
- `pyvista_colormaps.py`

The PyVista renderers support:

- C3D8 and C3D10 meshes
- displacement magnitude
- von Mises stress
- PE / PEEQ equivalent plastic strain
- discrete or continuous legends
- optional mesh edges
- optional undeformed background
- manual color min/max
- optional Abaqus-like colormap

## Figures

Tracked figure outputs:

- `figures/structured_hex_mesh_preview.svg`
- `figures/generated_structured_hex_mesh_preview.svg`
- `figures/s355mc_force_displacement_curve.svg`
- `figures/s355mc_c3d8_displacement_pyvista.png`
- `figures/s355mc_c3d8_displacement_animation.gif`
- `figures/s355mc_c3d8_von_mises_abaqus.png`
- `figures/s355mc_c3d8_von_mises_abaqus_animation.gif`
- `figures/s355mc_c3d8_peeq_animation.gif`

## Reproducibility notes

Large solver output files are intentionally ignored:

- `.frd`
- `.dat`
- `.sta`
- `.cvg`
- `.12d`
- solver logs
- generated solver `.inp` files in `results/`

Small summary files, generated mesh CSV files and selected documentation figures are tracked.
