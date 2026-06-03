#!/usr/bin/env python3
"""
Create a PyVista GIF animation of the cantilever shell deformation.

The animation shows:
- grey undeformed reference mesh
- colored deformed mesh
- deformation scale growing from 0 to 30 and back

Output:
- figures/cantilever_pyvista_overlay_animation.gif
- results/pyvista_gif_summary.txt
"""

from pathlib import Path
import numpy as np
import pyvista as pv

from render_cantilever_pyvista import (
    CASE_NAME,
    DEFORMATION_SCALE,
    parse_inp,
    parse_allnodes_displacements,
    build_pyvista_grid,
    setup_camera,
)

WINDOW_SIZE = (1400, 800)
N_UP = 12
N_DOWN = 10
FRAME_DURATION_MS = 90
N_BANDS = 8


def make_scale_values(max_scale: float):
    up = np.linspace(0.0, max_scale, N_UP)
    down = np.linspace(max_scale, 0.0, N_DOWN + 2)[1:-1]
    return list(up) + list(down)


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
    animated = build_pyvista_grid(nodes, elements, displacements, scale=0.0)

    base_points = undeformed.points.copy()
    u_vectors = animated.point_data["U"].copy()
    u_mag = animated.point_data["U_mag"].copy()
    max_u = float(np.max(u_mag))

    gif_file = figures_dir / "cantilever_pyvista_overlay_animation.gif"
    summary_file = results_dir / "pyvista_gif_summary.txt"

    pv.OFF_SCREEN = True
    plotter = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    plotter.set_background("white")

    # undeformed reference mesh
    plotter.add_mesh(
        undeformed,
        color="lightgray",
        show_edges=True,
        edge_color="gray",
        line_width=1,
        opacity=0.35,
        lighting=False,
    )

    # animated deformed mesh
    plotter.add_mesh(
        animated,
        scalars="U_mag",
        show_edges=True,
        edge_color="black",
        line_width=1,
        cmap="viridis",
        clim=[0.0, max_u],
        n_colors=N_BANDS,
        lighting=False,
        interpolate_before_map=False,
        scalar_bar_args={
            "title": "U [mm]",
            "fmt": "%.2f",
            "n_labels": N_BANDS + 1,
            "vertical": True,
            "position_x": 0.92,
            "position_y": 0.18,
            "height": 0.46,
            "width": 0.035,
            "title_font_size": 14,
            "label_font_size": 11,
        },
    )

    plotter.add_text(
        "Lab 005 — PyVista / VTK animated shell overlay",
        position=(35, 750),
        font_size=13,
        color="black",
    )

    plotter.add_text(
        "Grey: undeformed reference  Colored: deformed shape",
        position=(35, 715),
        font_size=10,
        color="black",
    )

    plotter.add_text(
        f"Tip displacement ≈ 2.83 mm   Max animation scale x{DEFORMATION_SCALE:.0f}",
        position=(35, 680),
        font_size=10,
        color="black",
    )

    plotter.add_axes()
    setup_camera(plotter)

    scales = make_scale_values(DEFORMATION_SCALE)

    plotter.open_gif(str(gif_file), fps=max(1, round(1000 / FRAME_DURATION_MS)))

    for scale in scales:
        scale_ratio = scale / DEFORMATION_SCALE if DEFORMATION_SCALE != 0 else 0.0
        animated.points = base_points + scale * u_vectors
        animated.point_data["U_mag"] = u_mag * scale_ratio
        plotter.write_frame()

    plotter.close()

    summary_text = "\n".join([
        "Lab 005 — PyVista GIF Animation",
        "================================",
        "",
        f"Input mesh: {inp_file}",
        f"Input displacements: {dat_file}",
        f"Nodes: {len(nodes)}",
        f"Shell elements: {len(elements)}",
        f"Max displacement magnitude: {max_u:.6f} mm",
        f"Max deformation scale: {DEFORMATION_SCALE:.1f}",
        f"Frames: {len(scales)}",
        f"Approx. frame duration: {FRAME_DURATION_MS} ms",
        "",
        f"Written: {gif_file}",
        "",
    ])

    summary_file.write_text(summary_text, encoding="utf-8")
    print(summary_text)


if __name__ == "__main__":
    main()
