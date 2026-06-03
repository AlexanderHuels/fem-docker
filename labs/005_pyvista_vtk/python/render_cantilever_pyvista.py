#!/usr/bin/env python3
"""
Render the cantilever benchmark result with PyVista / VTK.

Output:
- undeformed reference view
- deformed overlay view with grey undeformed mesh + colored deformed mesh
"""

from pathlib import Path
import math

import numpy as np
import pyvista as pv


CASE_NAME = "cantilever_shell_animation"
DEFORMATION_SCALE = 30.0


def parse_inp(inp_file: Path):
    nodes = {}
    elements = []
    lines = inp_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    mode = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line.startswith("*"):
            upper = line.upper()
            if upper == "*NODE" or upper.startswith("*NODE,"):
                mode = "NODE"
            elif upper.startswith("*ELEMENT"):
                mode = "ELEMENT"
            else:
                mode = None
            continue

        if mode == "NODE":
            parts = [p.strip() for p in line.split(",")]
            nodes[int(parts[0])] = (float(parts[1]), float(parts[2]), float(parts[3]))

        elif mode == "ELEMENT":
            parts = [p.strip() for p in line.split(",")]
            elements.append((int(parts[0]), tuple(int(p) for p in parts[1:5])))

    if not nodes:
        raise RuntimeError(f"No nodes found in {inp_file}")
    if not elements:
        raise RuntimeError(f"No elements found in {inp_file}")

    return nodes, elements


def parse_allnodes_displacements(dat_file: Path):
    lines = dat_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    in_block = False
    values = {}

    for raw in lines:
        line = raw.strip()
        lower = raw.lower()

        if "displacements" in lower and "set allnodes" in lower:
            in_block = True
            continue

        if in_block:
            if not line:
                continue

            if ("displacements" in lower and "set allnodes" not in lower) or "stresses" in lower or "forces" in lower:
                break

            parts = line.split()
            if len(parts) == 4:
                try:
                    values[int(parts[0])] = (float(parts[1]), float(parts[2]), float(parts[3]))
                except ValueError:
                    continue

    if not values:
        raise RuntimeError(f"No ALLNODES displacement block found in {dat_file}")

    return values


def build_pyvista_grid(nodes, elements, displacements, scale=0.0):
    node_ids = sorted(nodes)
    id_to_index = {nid: idx for idx, nid in enumerate(node_ids)}

    points = []
    u_vectors = []
    u_magnitudes = []

    for nid in node_ids:
        x, y, z = nodes[nid]
        u1, u2, u3 = displacements.get(nid, (0.0, 0.0, 0.0))

        points.append([x + scale * u1, y + scale * u2, z + scale * u3])
        u_vectors.append([u1, u2, u3])
        u_magnitudes.append(math.sqrt(u1 * u1 + u2 * u2 + u3 * u3))

    cells = []
    cell_types = []

    for _eid, conn in elements:
        cells.extend([
            4,
            id_to_index[conn[0]],
            id_to_index[conn[1]],
            id_to_index[conn[2]],
            id_to_index[conn[3]],
        ])
        cell_types.append(pv.CellType.QUAD)

    grid = pv.UnstructuredGrid(
        np.array(cells, dtype=np.int64),
        np.array(cell_types, dtype=np.uint8),
        np.array(points, dtype=float),
    )

    grid.point_data["U"] = np.array(u_vectors, dtype=float)
    grid.point_data["U_mag"] = np.array(u_magnitudes, dtype=float)

    return grid


def setup_camera(plotter):
    """
    Use a clean side view onto the X-Z shell plane.
    This avoids clipping and makes the deformation easier to read.
    """
    plotter.camera_position = [
        (500.0, -2600.0, -90.0),   # camera location
        (500.0, 0.0, -90.0),       # focal point
        (0.0, 0.0, 1.0),           # view-up direction
    ]
    plotter.camera.parallel_projection = True
    plotter.camera.parallel_scale = 360.0


def render_undeformed(grid, out_file: Path):
    pv.OFF_SCREEN = True

    plotter = pv.Plotter(off_screen=True, window_size=(1400, 800))
    plotter.set_background("white")

    plotter.add_mesh(
        grid,
        color="lightgray",
        show_edges=True,
        edge_color="black",
        line_width=1,
    )

    plotter.add_text(
        "Lab 005 — PyVista / VTK undeformed shell mesh",
        position=(35, 750),
        font_size=13,
        color="black",
    )

    plotter.add_text(
        "CalculiX shell mesh | 246 nodes | 200 S4 elements",
        position=(35, 715),
        font_size=10,
        color="black",
    )

    plotter.add_axes()
    setup_camera(plotter)

    plotter.screenshot(str(out_file))
    plotter.close()


def render_overlay(undeformed_grid, deformed_grid, out_file: Path):
    pv.OFF_SCREEN = True

    plotter = pv.Plotter(off_screen=True, window_size=(1400, 800))
    plotter.set_background("white")

    # Undeformed reference mesh
    plotter.add_mesh(
        undeformed_grid,
        color="lightgray",
        show_edges=True,
        edge_color="gray",
        line_width=1,
        opacity=0.35,
    )

    # Deformed colored mesh
    plotter.add_mesh(
        deformed_grid,
        scalars="U_mag",
        show_edges=True,
        edge_color="black",
        line_width=1,
        cmap="viridis",
        scalar_bar_args={
            "title": "|U| [mm]",
            "vertical": True,
            "position_x": 0.925,
            "position_y": 0.22,
            "height": 0.46,
            "width": 0.040,
            "title_font_size": 14,
            "label_font_size": 11,
        },
    )

    plotter.add_text(
        "Lab 005 — PyVista / VTK deformed shell overlay",
        position=(35, 750),
        font_size=13,
        color="black",
    )

    plotter.add_text(
        f"Grey: undeformed reference | Colored: deformed shape, scale x{DEFORMATION_SCALE:.0f}",
        position=(35, 715),
        font_size=10,
        color="black",
    )

    plotter.add_text(
        "Tip displacement ≈ 2.83 mm",
        position=(35, 680),
        font_size=10,
        color="black",
    )

    plotter.add_axes()
    setup_camera(plotter)

    plotter.screenshot(str(out_file))
    plotter.close()


def main():
    lab_dir = Path(__file__).resolve().parents[1]
    repo_dir = lab_dir.parents[1]

    source_dir = repo_dir / "labs" / "004_animated_deformation" / "results"
    inp_file = source_dir / f"{CASE_NAME}.inp"
    dat_file = source_dir / f"{CASE_NAME}.dat"

    figures_dir = lab_dir / "figures"
    results_dir = lab_dir / "results"
    figures_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    if not inp_file.exists() or not dat_file.exists():
        raise RuntimeError(
            "Required Lab 004 result files are missing.\n"
            "Run first:\n"
            "  ./labs/004_animated_deformation/run_animation.sh"
        )

    nodes, elements = parse_inp(inp_file)
    displacements = parse_allnodes_displacements(dat_file)

    undeformed = build_pyvista_grid(nodes, elements, displacements, scale=0.0)
    deformed = build_pyvista_grid(nodes, elements, displacements, scale=DEFORMATION_SCALE)

    undeformed_png = figures_dir / "cantilever_pyvista_undeformed.png"
    overlay_png = figures_dir / "cantilever_pyvista_deformed_overlay_scale30.png"

    render_undeformed(undeformed, undeformed_png)
    render_overlay(undeformed, deformed, overlay_png)

    max_u = max(float(v) for v in deformed.point_data["U_mag"])

    summary = results_dir / "pyvista_render_summary.txt"
    summary.write_text(
        "\n".join([
            "Lab 005 — PyVista / VTK Postprocessing",
            "======================================",
            "",
            f"Input mesh: {inp_file}",
            f"Input displacements: {dat_file}",
            f"Nodes: {len(nodes)}",
            f"Shell elements: {len(elements)}",
            f"Max displacement magnitude: {max_u:.6f} mm",
            f"Deformation scale factor: {DEFORMATION_SCALE:.1f}",
            "",
            f"Written: {undeformed_png}",
            f"Written: {overlay_png}",
            "",
        ]),
        encoding="utf-8",
    )

    print(summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
