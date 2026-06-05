#!/usr/bin/env python3
"""
Render Lab 006 S355MC von Mises stress result with PyVista.

Input:
- CalculiX C3D10 input mesh
- CalculiX FRD with U, S, E, PE

Output:
- PNG: deformed dogbone colored by von Mises stress

Note:
The stress field read from FRD is intended for postprocessing visualization.
"""

from pathlib import Path
import re
import math
import numpy as np
import pyvista as pv
from matplotlib import colormaps
from matplotlib.colors import ListedColormap

from render_s355mc_displacement_pyvista import (
    CASE_NAME,
    WINDOW_SIZE,
    N_LEVELS,
    parse_inp_nodes_and_c3d10,
    extract_final_displacements_from_frd,
    build_quadratic_tet_grid,
    extract_surface_clean,
)


DEFORMATION_SCALE = 5.0
FIELD_NAME = "S_von_Mises"
N_STRESS_LEVELS = 10


def extract_final_stress_from_frd(frd_file: Path):
    """
    Extract final STRESS block from CalculiX FRD.

    Expected stress components:
    Sxx, Syy, Szz, Sxy, Syz, Szx or equivalent order.
    Von Mises is independent of the ordering of the three shear components.
    """
    number_re = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?")

    stress_blocks = []
    current = None

    with frd_file.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            upper = raw.upper()
            stripped = raw.lstrip()

            # Start only at FRD result component header lines.
            if stripped.startswith("-4") and "STRESS" in upper:
                current = {}
                continue

            if current is not None:
                if raw.startswith(" -3"):
                    if current:
                        stress_blocks.append(current)
                    current = None
                    continue

                if raw.startswith(" -1"):
                    payload = raw[3:]
                    nums = number_re.findall(payload.replace("D", "E"))
                    if len(nums) >= 7:
                        nid = int(float(nums[0]))
                        values = [float(v.replace("D", "E")) for v in nums[1:7]]

                        sxx, syy, szz, sxy, syz, szx = values

                        vm = math.sqrt(
                            0.5 * (
                                (sxx - syy) ** 2
                                + (syy - szz) ** 2
                                + (szz - sxx) ** 2
                            )
                            + 3.0 * (sxy ** 2 + syz ** 2 + szx ** 2)
                        )

                        current[nid] = vm

    if not stress_blocks:
        raise RuntimeError(
            f"No STRESS block found in {frd_file}. "
            "Check whether the input contains '*EL FILE' with 'S'."
        )

    return stress_blocks[-1]


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

    out_file = figures_dir / "s355mc_von_mises_pyvista.png"

    nodes, c3d10_elements = parse_inp_nodes_and_c3d10(inp_file)
    displacements = extract_final_displacements_from_frd(frd_file)
    stress_vm_by_node = extract_final_stress_from_frd(frd_file)

    grid, deformed, used_node_ids = build_quadratic_tet_grid(
        nodes,
        c3d10_elements,
        displacements,
    )

    # Apply deformation scale for visualization.
    points0 = grid.points.copy()
    u = grid.point_data["U"]
    deformed.points = points0 + DEFORMATION_SCALE * u

    vm_values = np.full(len(used_node_ids), np.nan, dtype=float)
    missing = 0

    for i, nid in enumerate(used_node_ids):
        if nid in stress_vm_by_node:
            vm_values[i] = stress_vm_by_node[nid]
        else:
            missing += 1

    if missing:
        # Keep the plot possible, but make missing data explicit.
        finite = vm_values[np.isfinite(vm_values)]
        fill_value = float(np.nanmin(finite)) if finite.size else 0.0
        vm_values = np.nan_to_num(vm_values, nan=fill_value)

    deformed.point_data[FIELD_NAME] = vm_values

    vm_min = float(np.min(vm_values))
    vm_max = float(np.max(vm_values))
    vm_p99 = float(np.percentile(vm_values, 99.0))

    # Use full max unless there are extreme local spikes.
    color_max = vm_max
    if vm_max > 1.8 * vm_p99:
        color_max = vm_p99

    surface = extract_surface_clean(deformed)
    undeformed_surface = extract_surface_clean(grid)

    base = colormaps["turbo"].resampled(N_STRESS_LEVELS)
    discrete_cmap = ListedColormap(base(np.linspace(0, 1, N_STRESS_LEVELS)))

    scalar_bar_args = {
        "title": "S_vm [MPa]",
        "vertical": True,
        "position_x": 0.935,
        "position_y": 0.18,
        "height": 0.62,
        "width": 0.030,
        "title_font_size": 18,
        "label_font_size": 13,
        "fmt": "%.0f",
        "n_labels": N_STRESS_LEVELS + 1,
    }

    plotter = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    plotter.set_background("white")

    plotter.add_mesh(
        undeformed_surface,
        color="lightgrey",
        opacity=0.22,
        show_edges=False,
        smooth_shading=True,
    )

    plotter.add_mesh(
        surface,
        scalars=FIELD_NAME,
        clim=[0.0, color_max],
        cmap=discrete_cmap,
        n_colors=N_STRESS_LEVELS,
        interpolate_before_map=False,
        show_edges=False,
        smooth_shading=True,
        scalar_bar_args=scalar_bar_args,
    )

    title = (
        "Lab 006 — S355MC C3D10 tensile dogbone\n"
        f"von Mises stress, deformed shape x{DEFORMATION_SCALE:g}   "
        f"max S_vm = {vm_max:.1f} MPa   "
        "F = 10.76 kN"
    )

    if color_max < vm_max:
        title += f"   color max = p99 {color_max:.1f} MPa"

    plotter.add_text(
        title,
        position=(35, 845),
        font_size=14,
        color="black",
    )

    plotter.camera_position = "xy"
    plotter.enable_parallel_projection()
    plotter.camera.zoom(1.50)

    plotter.add_axes(
        line_width=2,
        labels_off=False,
        color="black",
    )

    plotter.screenshot(str(out_file))
    plotter.close()

    summary_file = results_dir / "s355mc_von_mises_pyvista_summary.txt"
    summary = f"""Lab 006 — PyVista von Mises rendering
====================================

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
Stress nodes in FRD final block: {len(stress_vm_by_node)}
Rendered quadratic tetra nodes: {len(used_node_ids)}
Rendered quadratic tetra cells: {len(c3d10_elements)}
Missing stress values on rendered nodes: {missing}

von Mises stress:
min S_vm: {vm_min:.6f} MPa
max S_vm: {vm_max:.6f} MPa
p99 S_vm: {vm_p99:.6f} MPa
color max used: {color_max:.6f} MPa

Deformation scale:
{DEFORMATION_SCALE}

Discrete color levels:
{N_STRESS_LEVELS}

Output:
{out_file}
"""
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
