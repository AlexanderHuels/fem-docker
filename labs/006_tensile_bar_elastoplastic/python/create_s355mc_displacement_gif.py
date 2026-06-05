#!/usr/bin/env python3
"""
Create animated GIF for Lab 006 S355MC displacement result.

Stable legend version:
- scene is built once
- no plotter.clear_actors() inside the animation loop
- scalar bar remains visible throughout the GIF
- discrete color levels
"""

from pathlib import Path
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


MAX_DEFORMATION_SCALE = 5.0
FPS = 12
N_UP = 22
N_DOWN = 22
N_HOLD_ZERO = 4
N_HOLD_MAX = 6


def mark_polydata_modified(polydata):
    """Force VTK/PyVista to notice updated coordinates and scalars."""
    try:
        polydata.GetPoints().Modified()
    except Exception:
        pass

    try:
        scalars = polydata.GetPointData().GetScalars()
        if scalars is not None:
            scalars.Modified()
    except Exception:
        pass

    try:
        polydata.Modified()
    except Exception:
        pass


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

    gif_file = figures_dir / "s355mc_displacement_animation.gif"

    nodes, c3d10_elements = parse_inp_nodes_and_c3d10(inp_file)
    displacements = extract_final_displacements_from_frd(frd_file)

    grid, _deformed, used_node_ids = build_quadratic_tet_grid(
        nodes,
        c3d10_elements,
        displacements,
    )

    undeformed_surface = extract_surface_clean(grid)
    animated_surface = extract_surface_clean(grid)

    points0 = animated_surface.points.copy()
    u_surface = animated_surface.point_data["U"].copy()
    u_mag_final = animated_surface.point_data["U_mag"].copy()

    max_u = float(u_mag_final.max())

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

    ramp_up = np.linspace(0.0, 1.0, N_UP)
    ramp_down = np.linspace(1.0, 0.0, N_DOWN)
    amplitudes = np.concatenate(
        [
            np.zeros(N_HOLD_ZERO),
            ramp_up,
            np.ones(N_HOLD_MAX),
            ramp_down[1:],
        ]
    )

    animated_surface.point_data["U_anim"] = np.zeros_like(u_mag_final)
    animated_surface.set_active_scalars("U_anim")

    plotter = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    plotter.set_background("white")

    plotter.add_mesh(
        undeformed_surface,
        color="lightgrey",
        opacity=0.25,
        show_edges=False,
        smooth_shading=True,
    )

    plotter.add_mesh(
        animated_surface,
        scalars="U_anim",
        clim=[0.0, max_u],
        cmap=discrete_cmap,
        n_colors=N_LEVELS,
        interpolate_before_map=False,
        show_edges=False,
        smooth_shading=True,
        show_scalar_bar=True,
        scalar_bar_args=scalar_bar_args,
    )

    plotter.camera_position = "xy"
    plotter.enable_parallel_projection()
    plotter.camera.zoom(1.50)

    plotter.add_axes(
        line_width=2,
        labels_off=False,
        color="black",
    )

    plotter.add_text(
        "Lab 006 — S355MC C3D10 tensile dogbone",
        position=(35, 875),
        font_size=15,
        color="black",
        name="title_line_1",
    )

    plotter.add_text(
        f"Animated deformation   max U = {max_u:.3f} mm   F = 10.76 kN",
        position=(35, 840),
        font_size=14,
        color="black",
        name="title_line_2",
    )

    plotter.open_gif(str(gif_file), fps=FPS)

    for amp in amplitudes:
        scale = amp * MAX_DEFORMATION_SCALE

        animated_surface.points = points0 + scale * u_surface
        animated_surface.point_data["U_anim"] = amp * u_mag_final
        animated_surface.set_active_scalars("U_anim")
        mark_polydata_modified(animated_surface)

        plotter.add_text(
            f"deformation scale x{scale:.2f}",
            position=(35, 805),
            font_size=13,
            color="black",
            name="scale_text",
        )

        plotter.render()
        plotter.write_frame()

    plotter.close()

    summary_file = results_dir / "s355mc_displacement_gif_summary.txt"
    summary = f"""Lab 006 — PyVista displacement GIF
==================================

Case:
{CASE_NAME}

Frames:
{len(amplitudes)}

FPS:
{FPS}

Max deformation scale:
{MAX_DEFORMATION_SCALE}

Final max |U|:
{max_u:.6f} mm

Discrete color levels:
{N_LEVELS}

Output:
{gif_file}
"""
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
