#!/usr/bin/env python3
"""
Render Lab 006 S355MC displacement result with PyVista.

Improved presentation version:
- Uses VTK quadratic tetra cells from C3D10 connectivity
- Renders a smoothed/subdivided surface
- Shows undeformed reference as light grey transparent surface
- Shows deformed shape colored by displacement magnitude
"""

from pathlib import Path
import re
import numpy as np
import pyvista as pv
from matplotlib import colormaps
from matplotlib.colors import ListedColormap


CASE_NAME = "tensile_dogbone_iso6892_form1_c3d10_s355mc_fields"

DEFORMATION_SCALE = 5.0
WINDOW_SIZE = (1800, 950)
N_LEVELS = 8


def parse_inp_nodes_and_c3d10(inp_file: Path):
    nodes = {}
    elements = []

    mode = None

    for raw in inp_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()

        if not line:
            continue

        if line.startswith("*"):
            upper = line.upper()
            if upper.startswith("*NODE"):
                mode = "NODE"
            elif upper.startswith("*ELEMENT") and "TYPE=C3D10" in upper:
                mode = "ELEMENT"
            else:
                mode = None
            continue

        if mode == "NODE":
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                nid = int(parts[0])
                nodes[nid] = (float(parts[1]), float(parts[2]), float(parts[3]))

        elif mode == "ELEMENT":
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 11:
                eid = int(parts[0])
                conn = tuple(int(v) for v in parts[1:11])
                elements.append((eid, conn))

    if not nodes:
        raise RuntimeError(f"No nodes parsed from {inp_file}")

    if not elements:
        raise RuntimeError(f"No C3D10 elements parsed from {inp_file}")

    return nodes, elements


def extract_final_displacements_from_frd(frd_file: Path):
    number_re = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?")

    displacement_blocks = []
    current = None

    with frd_file.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            upper = raw.upper()

            if "DISP" in upper or "DISPLACEMENT" in upper:
                current = {}
                continue

            if current is not None:
                if raw.startswith(" -3"):
                    if current:
                        displacement_blocks.append(current)
                    current = None
                    continue

                if raw.startswith(" -1"):
                    payload = raw[3:]
                    nums = number_re.findall(payload.replace("D", "E"))
                    if len(nums) >= 4:
                        nid = int(float(nums[0]))
                        u1 = float(nums[1].replace("D", "E"))
                        u2 = float(nums[2].replace("D", "E"))
                        u3 = float(nums[3].replace("D", "E"))
                        current[nid] = (u1, u2, u3)

    if not displacement_blocks:
        raise RuntimeError(
            f"No displacement block found in {frd_file}. "
            "Check whether the input contains '*NODE FILE' with 'U'."
        )

    return displacement_blocks[-1]


def build_quadratic_tet_grid(nodes, c3d10_elements, displacements):
    """
    Build PyVista quadratic tetra grid using all 10 C3D10 nodes.

    CalculiX C3D10 order is compatible with VTK quadratic tetra:
    1,2,3,4, 12,23,31,14,24,34
    """
    used_node_ids = sorted({nid for _eid, conn in c3d10_elements for nid in conn})

    missing_u = [nid for nid in used_node_ids if nid not in displacements]
    if missing_u:
        raise RuntimeError(
            f"Missing displacement for {len(missing_u)} used nodes. "
            f"Example: {missing_u[:5]}"
        )

    old_to_new = {nid: i for i, nid in enumerate(used_node_ids)}

    points = np.array([nodes[nid] for nid in used_node_ids], dtype=float)
    u = np.array([displacements[nid] for nid in used_node_ids], dtype=float)
    u_mag = np.linalg.norm(u, axis=1)

    cells = []
    celltypes = []

    for _eid, conn in c3d10_elements:
        local_ids = [old_to_new[nid] for nid in conn]
        cells.extend([10] + local_ids)
        celltypes.append(pv.CellType.QUADRATIC_TETRA)

    cells = np.array(cells, dtype=np.int64)
    celltypes = np.array(celltypes, dtype=np.uint8)

    grid = pv.UnstructuredGrid(cells, celltypes, points)
    grid.point_data["U"] = u
    grid.point_data["U_mag"] = u_mag

    deformed = grid.copy()
    deformed.points = points + DEFORMATION_SCALE * u
    deformed.point_data["U"] = u
    deformed.point_data["U_mag"] = u_mag

    return grid, deformed, used_node_ids


def extract_surface_clean(grid):
    try:
        return grid.extract_surface(
            nonlinear_subdivision=2,
            algorithm="dataset_surface",
        )
    except TypeError:
        return grid.extract_surface(nonlinear_subdivision=2)


def main():
    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.font.family = "arial"

    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"
    figures_dir = lab_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    inp_file = results_dir / f"{CASE_NAME}.inp"
    frd_file = results_dir / f"{CASE_NAME}.frd"

    if not inp_file.exists():
        inp_file = lab_dir / "input" / f"{CASE_NAME}.inp"

    out_file = figures_dir / "s355mc_displacement_pyvista.png"

    nodes, c3d10_elements = parse_inp_nodes_and_c3d10(inp_file)
    displacements = extract_final_displacements_from_frd(frd_file)

    grid, deformed, used_node_ids = build_quadratic_tet_grid(
        nodes,
        c3d10_elements,
        displacements,
    )

    max_u = float(deformed.point_data["U_mag"].max())
    min_u = float(deformed.point_data["U_mag"].min())

    surface = extract_surface_clean(deformed)
    undeformed_surface = extract_surface_clean(grid)

    base = colormaps["viridis"].resampled(N_LEVELS)
    discrete_cmap = ListedColormap(base(np.linspace(0, 1, N_LEVELS)))

    scalar_bar_args = {
        "title": "U [mm]",
        "vertical": True,
        "position_x": 0.935,
        "position_y": 0.18,
        "height": 0.62,
        "width": 0.030,
        "title_font_size": 18,
        "label_font_size": 13,
        "fmt": "%.2f",
        "n_labels": N_LEVELS + 1,
    }

    plotter = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    plotter.set_background("white")

    # Light undeformed reference
    plotter.add_mesh(
        undeformed_surface,
        color="lightgrey",
        opacity=0.32,
        show_edges=False,
        smooth_shading=True,
    )

    # Deformed result
    plotter.add_mesh(
        surface,
        scalars="U_mag",
        clim=[0.0, max_u],
        cmap=discrete_cmap,
        n_colors=N_LEVELS,
        interpolate_before_map=False,
        show_edges=False,
        smooth_shading=True,
        scalar_bar_args=scalar_bar_args,
    )

    title = (
        "Lab 006 — S355MC C3D10 tensile dogbone\n"
        f"Deformed shape, scale x{DEFORMATION_SCALE:g}   "
        f"max |U| = {max_u:.3f} mm   "
        "F = 10.76 kN"
    )

    plotter.add_text(
        title,
        position=(35, 845),
        font_size=15,
        color="black",
    )

    # Camera: clean top view
    plotter.camera_position = "xy"
    plotter.enable_parallel_projection()
    plotter.camera.zoom(1.50)

    # Small orientation axes only, no large bounds/grid box
    plotter.add_axes(
        line_width=2,
        labels_off=False,
        color="black",
    )

    plotter.screenshot(str(out_file))
    plotter.close()

    summary_file = results_dir / "s355mc_displacement_pyvista_summary.txt"
    summary = f"""Lab 006 — PyVista displacement rendering
=======================================

Case:
{CASE_NAME}

Input mesh:
{inp_file}

Result file:
{frd_file}

Parsed:
Nodes in INP: {len(nodes)}
C3D10 elements in INP: {len(c3d10_elements)}
Displacement nodes in FRD final block: {len(displacements)}
Rendered quadratic tetra nodes: {len(used_node_ids)}
Rendered quadratic tetra cells: {len(c3d10_elements)}

Displacement:
min |U|: {min_u:.6f} mm
max |U|: {max_u:.6f} mm

Deformation scale:
{DEFORMATION_SCALE}

Output:
{out_file}
"""
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
