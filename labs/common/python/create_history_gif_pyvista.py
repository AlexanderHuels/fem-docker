#!/usr/bin/env python3
"""
Common PyVista history GIF generator for CalculiX FRD results.

Supports:
- displacement magnitude
- von Mises stress
- PE scalar field, i.e. equivalent plastic strain requested as PEEQ and stored in FRD as PE

Works with:
- C3D8
- C3D10
"""

from pathlib import Path
import argparse
import sys
import tempfile

import numpy as np
import pyvista as pv
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pyvista_colormaps import build_colormap, available_colormaps

from ccx_inp_mesh import read_ccx_inp_mesh
from ccx_pyvista_grid import build_pyvista_grid
from ccx_frd_results import (
    parse_frd_history,
    clean_history_blocks,
    von_mises_from_stress,
)


def ensure_offscreen():
    pv.OFF_SCREEN = True


def scalar_label(field: str):
    if field == "displacement":
        return "|U| [mm]"
    if field == "von_mises":
        return "S_vm [MPa]"
    if field == "pe":
        return "PE / PEEQ [-]"
    raise ValueError(field)


def scalar_name(field: str):
    if field == "displacement":
        return "U_mag"
    if field == "von_mises":
        return "S_vm"
    if field == "pe":
        return "PE"
    raise ValueError(field)


def select_frame_indices(n_available: int, max_frames: int | None):
    if n_available <= 0:
        raise RuntimeError("No result frames available.")

    if max_frames is None or max_frames <= 0 or n_available <= max_frames:
        return list(range(n_available))

    indices = np.linspace(0, n_available - 1, max_frames, dtype=int).tolist()

    # Remove duplicates while preserving order.
    unique = []
    seen = set()
    for idx in indices:
        if idx not in seen:
            unique.append(idx)
            seen.add(idx)

    if unique[-1] != n_available - 1:
        unique.append(n_available - 1)

    return unique


def scalar_for_frame(field, u, stress, pe):
    if field == "displacement":
        return np.linalg.norm(u, axis=1)

    if field == "von_mises":
        if stress is None:
            raise RuntimeError("Stress block required for von Mises rendering.")
        return von_mises_from_stress(stress)

    if field == "pe":
        if pe is None:
            raise RuntimeError("PE block required for PE rendering.")
        return pe

    raise ValueError(field)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inp", required=True, type=Path)
    parser.add_argument("--frd", required=True, type=Path)
    parser.add_argument("--type", required=True, choices=["C3D8", "C3D10"])
    parser.add_argument("--field", required=True, choices=["displacement", "von_mises", "pe"])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--title", required=True)

    parser.add_argument("--deformation-scale", type=float, default=5.0)
    parser.add_argument("--window-width", type=int, default=1400)
    parser.add_argument("--window-height", type=int, default=700)

    mesh_group = parser.add_mutually_exclusive_group()
    mesh_group.add_argument("--show-mesh", dest="show_mesh", action="store_true")
    mesh_group.add_argument("--hide-mesh", dest="show_mesh", action="store_false")
    parser.set_defaults(show_mesh=True)

    undeformed_group = parser.add_mutually_exclusive_group()
    undeformed_group.add_argument("--show-undeformed", dest="show_undeformed", action="store_true")
    undeformed_group.add_argument("--hide-undeformed", dest="show_undeformed", action="store_false")
    parser.set_defaults(show_undeformed=False)

    scalar_bar_group = parser.add_mutually_exclusive_group()
    scalar_bar_group.add_argument("--show-scalar-bar", dest="show_scalar_bar", action="store_true")
    scalar_bar_group.add_argument("--hide-scalar-bar", dest="show_scalar_bar", action="store_false")
    parser.set_defaults(show_scalar_bar=True)

    parser.add_argument("--legend-mode", choices=["discrete", "continuous"], default="discrete")
    parser.add_argument(
        "--colormap",
        choices=available_colormaps(),
        default="turbo",
        help="Colormap to use: turbo, viridis, abaqus.",
    )
    parser.add_argument("--n-levels", type=int, default=8)
    parser.add_argument("--color-min", type=float, default=None)
    parser.add_argument("--color-max", type=float, default=None)

    parser.add_argument("--frame-duration-ms", type=int, default=90)
    parser.add_argument("--max-frames", type=int, default=40)

    args = parser.parse_args()

    if args.n_levels < 2:
        raise ValueError("--n-levels must be >= 2")

    if args.frame_duration_ms <= 0:
        raise ValueError("--frame-duration-ms must be > 0")

    ensure_offscreen()

    mesh = read_ccx_inp_mesh(args.inp, args.type)
    grid, used_node_ids, id_to_idx = build_pyvista_grid(mesh)

    displacement_blocks, stress_blocks, pe_blocks = parse_frd_history(
        args.frd,
        id_to_idx,
        len(used_node_ids),
    )

    displacement_blocks, stress_blocks, pe_blocks = clean_history_blocks(
        displacement_blocks,
        stress_blocks,
        pe_blocks,
    )

    if not displacement_blocks:
        raise RuntimeError("No displacement blocks found in FRD.")

    if args.field == "displacement":
        n_available = len(displacement_blocks)
    elif args.field == "von_mises":
        if not stress_blocks:
            raise RuntimeError("No stress blocks found in FRD.")
        n_available = min(len(displacement_blocks), len(stress_blocks))
    elif args.field == "pe":
        if not pe_blocks:
            raise RuntimeError("No PE blocks found in FRD.")
        n_available = min(len(displacement_blocks), len(pe_blocks))
    else:
        raise ValueError(args.field)

    frame_indices = select_frame_indices(n_available, args.max_frames)

    name = scalar_name(args.field)
    label = scalar_label(args.field)

    # Build scalar arrays for selected frames first, so auto color range is global over the GIF.
    selected_u = []
    selected_scalars = []

    for block_i in frame_indices:
        u = displacement_blocks[block_i]
        stress = stress_blocks[block_i] if block_i < len(stress_blocks) else None
        pe = pe_blocks[block_i] if block_i < len(pe_blocks) else None

        values = scalar_for_frame(args.field, u, stress, pe)

        selected_u.append(u)
        selected_scalars.append(values)

    all_values = np.concatenate(selected_scalars)

    scalar_min = float(np.nanmin(all_values))
    scalar_max = float(np.nanmax(all_values))
    scalar_p99 = float(np.nanpercentile(all_values, 99.0))

    color_min = scalar_min if args.color_min is None else args.color_min
    color_max = scalar_max if args.color_max is None else args.color_max

    if color_max <= color_min:
        raise ValueError(
            f"Invalid color range: color_max ({color_max}) must be larger than color_min ({color_min})"
        )

    clim = [color_min, color_max]

    if args.legend_mode == "discrete":
        n_colors = args.n_levels
        n_labels = args.n_levels + 1
    else:
        n_colors = 256
        n_labels = 8

    cmap = build_colormap(args.colormap, args.legend_mode, args.n_levels)

    scalar_bar_args = {
        "title": label,
        "vertical": True,
        "position_x": 0.86,
        "position_y": 0.18,
        "width": 0.035,
        "height": 0.62,
        "title_font_size": 15,
        "label_font_size": 12,
        "n_labels": n_labels,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)

    gif_frames = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        for frame_no, block_i in enumerate(frame_indices):
            u = selected_u[frame_no]
            values = selected_scalars[frame_no]
            u_mag = np.linalg.norm(u, axis=1)

            deformed = grid.copy()
            deformed.points = grid.points + args.deformation_scale * u
            deformed.point_data["U"] = u
            deformed.point_data["U_mag"] = u_mag
            deformed.point_data[name] = values

            surface = deformed.extract_surface(algorithm="dataset_surface")

            plotter = pv.Plotter(
                off_screen=True,
                window_size=(args.window_width, args.window_height),
            )
            plotter.set_background("white")

            if args.show_undeformed:
                undeformed_surface = grid.extract_surface(algorithm="dataset_surface")
                plotter.add_mesh(
                    undeformed_surface,
                    color="lightgray",
                    opacity=0.28,
                    show_edges=False,
                    smooth_shading=False,
                )

            plotter.add_mesh(
                surface,
                scalars=name,
                cmap=cmap,
                clim=clim,
                n_colors=n_colors,
                show_edges=args.show_mesh,
                line_width=0.35 if args.show_mesh else 0.0,
                scalar_bar_args=scalar_bar_args,
                show_scalar_bar=args.show_scalar_bar,
            )

            range_text = (
                f"{label} range = {color_min:.4g} ... {color_max:.4g}"
                if args.legend_mode == "continuous"
                else f"{label} range = {color_min:.4g} ... {color_max:.4g}, levels = {args.n_levels}"
            )

            plotter.add_text(
                args.title,
                position="upper_left",
                font_size=14,
                color="black",
            )

            plotter.add_text(
                (
                    f"frame {frame_no + 1}/{len(frame_indices)}   "
                    f"increment {block_i + 1}/{n_available}   "
                    f"max |U| = {float(np.max(u_mag)):.4f} mm\n"
                    f"deformation scale = {args.deformation_scale:g}   "
                    f"{range_text}"
                ),
                position="lower_left",
                font_size=10,
                color="black",
            )

            plotter.camera_position = "xy"
            plotter.camera.zoom(1.10)

            frame_file = tmpdir / f"frame_{frame_no:04d}.png"
            plotter.screenshot(str(frame_file))
            plotter.close()

            gif_frames.append(Image.open(frame_file).convert("P", palette=Image.ADAPTIVE))

        gif_frames[0].save(
            args.out,
            save_all=True,
            append_images=gif_frames[1:],
            duration=args.frame_duration_ms,
            loop=0,
            optimize=False,
            disposal=2,
        )

    summary = f"""Common PyVista history GIF summary
==================================

Input INP:
{args.inp}

Input FRD:
{args.frd}

Element type:
{mesh.element_type}

Field:
{args.field}

Output:
{args.out}

Mesh:
- nodes used: {len(used_node_ids)}
- cells: {grid.n_cells}
- points: {grid.n_points}

Result blocks:
- displacement blocks: {len(displacement_blocks)}
- stress blocks: {len(stress_blocks)}
- PE blocks: {len(pe_blocks)}

Frames:
- available correlated frames: {n_available}
- rendered frames: {len(frame_indices)}
- frame duration: {args.frame_duration_ms} ms
- frame indices: {frame_indices}

Rendered scalar over selected frames:
- min: {scalar_min:.8e}
- max: {scalar_max:.8e}
- p99: {scalar_p99:.8e}

Color range:
- color min: {color_min:.8e}
- color max: {color_max:.8e}

Display options:
- show mesh: {args.show_mesh}
- legend mode: {args.legend_mode}
- n levels: {args.n_levels}
- show undeformed: {args.show_undeformed}
- show scalar bar: {args.show_scalar_bar}
- colormap: {args.colormap}

Deformation scale:
{args.deformation_scale}
"""

    if args.summary:
        args.summary.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
