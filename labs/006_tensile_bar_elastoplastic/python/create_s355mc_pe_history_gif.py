#!/usr/bin/env python3
"""
Create physically correlated PE history GIF for Lab 006.

Each frame uses matching result blocks from the CalculiX FRD:
- displacement U from increment i
- scalar plastic strain PE from increment i

The FRD contains:
    -4  PE          1    1

Negative numerical noise in PE is clipped to zero for plotting.
"""

from pathlib import Path
import re
import shutil
import gc
import argparse
import numpy as np
from PIL import Image
import pyvista as pv
from matplotlib import colormaps
from matplotlib.colors import ListedColormap


CASE_NAME = "tensile_dogbone_iso6892_form1_c3d10_s355mc_fields"

WINDOW_SIZE = (1400, 700)
DEFORMATION_SCALE = 5.0
N_PE_LEVELS = 10
FRAME_DURATION_MS = 110
MAX_FRAMES = 36


def parse_inp_nodes_and_c3d10(inp_file: Path):
    nodes = {}
    elements = []
    mode = None

    with inp_file.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
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
                    nodes[nid] = tuple(float(v) for v in parts[1:4])

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


def build_quadratic_grid(nodes, c3d10_elements):
    used_ids = []
    used_set = set()

    for _eid, conn in c3d10_elements:
        for nid in conn:
            if nid not in used_set:
                used_set.add(nid)
                used_ids.append(nid)

    id_to_idx = {nid: i for i, nid in enumerate(used_ids)}

    points = np.array([nodes[nid] for nid in used_ids], dtype=float)

    cells = []
    celltypes = []

    for _eid, conn in c3d10_elements:
        local = [id_to_idx[nid] for nid in conn]
        cells.extend([10] + local)
        celltypes.append(pv.CellType.QUADRATIC_TETRA)

    grid = pv.UnstructuredGrid(
        np.array(cells, dtype=np.int64),
        np.array(celltypes, dtype=np.uint8),
        points,
    )

    return grid, used_ids, id_to_idx


def finalize_block(kind, array, count, displacement_blocks, pe_blocks):
    if kind == "U" and count > 0:
        displacement_blocks.append(array)
    elif kind == "PE" and count > 0:
        pe_blocks.append(array)


def parse_frd_history(frd_file: Path, id_to_idx, n_used_nodes: int):
    """
    Parse all displacement and PE result blocks.

    Returns:
    - list of U arrays, shape (n_used_nodes, 3)
    - list of PE arrays, shape (n_used_nodes,)
    """
    number_re = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?")

    displacement_blocks = []
    pe_blocks = []

    current_kind = None
    current_array = None
    current_count = 0

    with frd_file.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            upper = raw.upper()
            stripped = raw.lstrip()

            is_result_header = stripped.startswith("-4")
            is_block_end = stripped.startswith("-3")
            is_value_line = stripped.startswith("-1")

            if is_result_header and ("DISP" in upper or "DISPLACEMENT" in upper):
                finalize_block(
                    current_kind,
                    current_array,
                    current_count,
                    displacement_blocks,
                    pe_blocks,
                )
                current_kind = "U"
                current_array = np.full((n_used_nodes, 3), np.nan, dtype=float)
                current_count = 0
                continue

            if is_result_header and " PE " in upper:
                finalize_block(
                    current_kind,
                    current_array,
                    current_count,
                    displacement_blocks,
                    pe_blocks,
                )
                current_kind = "PE"
                current_array = np.full(n_used_nodes, np.nan, dtype=float)
                current_count = 0
                continue

            if is_block_end:
                finalize_block(
                    current_kind,
                    current_array,
                    current_count,
                    displacement_blocks,
                    pe_blocks,
                )
                current_kind = None
                current_array = None
                current_count = 0
                continue

            if current_kind is None or not is_value_line:
                continue

            payload = raw[3:]
            nums = number_re.findall(payload.replace("D", "E"))

            if current_kind == "U":
                if len(nums) < 4:
                    continue

                nid = int(float(nums[0]))
                idx = id_to_idx.get(nid)
                if idx is None:
                    continue

                ux = float(nums[1].replace("D", "E"))
                uy = float(nums[2].replace("D", "E"))
                uz = float(nums[3].replace("D", "E"))

                current_array[idx, :] = (ux, uy, uz)
                current_count += 1

            elif current_kind == "PE":
                if len(nums) < 2:
                    continue

                nid = int(float(nums[0]))
                idx = id_to_idx.get(nid)
                if idx is None:
                    continue

                pe = float(nums[1].replace("D", "E"))
                current_array[idx] = pe
                current_count += 1

    finalize_block(
        current_kind,
        current_array,
        current_count,
        displacement_blocks,
        pe_blocks,
    )

    if not displacement_blocks:
        raise RuntimeError("No displacement history blocks found in FRD.")
    if not pe_blocks:
        raise RuntimeError("No PE history blocks found in FRD.")

    n_frames = min(len(displacement_blocks), len(pe_blocks))
    return displacement_blocks[:n_frames], pe_blocks[:n_frames]


def extract_surface_clean(mesh):
    try:
        return mesh.extract_surface(
            nonlinear_subdivision=2,
            algorithm="dataset_surface",
        ).triangulate().clean()
    except TypeError:
        return mesh.extract_surface(nonlinear_subdivision=2).triangulate().clean()


def select_frame_indices(n_available: int, max_frames: int):
    if n_available <= max_frames:
        return list(range(n_available))

    indices = np.linspace(0, n_available - 1, max_frames)
    return sorted(set(int(round(i)) for i in indices))


def prepare_history_arrays(displacement_blocks, pe_blocks):
    n_available = min(len(displacement_blocks), len(pe_blocks))

    for i in range(n_available):
        u = displacement_blocks[i]
        if np.isnan(u).any():
            displacement_blocks[i] = np.nan_to_num(u, nan=0.0)

        pe = pe_blocks[i]
        finite = pe[np.isfinite(pe)]
        fill = float(np.nanmin(finite)) if finite.size else 0.0
        pe = np.nan_to_num(pe, nan=fill)

        # Clip tiny negative extrapolation/numerical noise to zero.
        pe = np.maximum(pe, 0.0)
        pe_blocks[i] = pe

    return displacement_blocks[:n_available], pe_blocks[:n_available]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Parse FRD and print PE history statistics without rendering.",
    )
    args = parser.parse_args()

    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.font.family = "arial"

    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"
    figures_dir = lab_dir / "figures"
    frames_dir = lab_dir / "frames_pe_history"

    figures_dir.mkdir(exist_ok=True)

    inp_file = results_dir / f"{CASE_NAME}.inp"
    frd_file = results_dir / f"{CASE_NAME}.frd"

    if not inp_file.exists():
        inp_file = lab_dir / "input" / f"{CASE_NAME}.inp"

    out_gif = figures_dir / "s355mc_pe_history_animation.gif"

    nodes, c3d10_elements = parse_inp_nodes_and_c3d10(inp_file)
    grid, used_ids, id_to_idx = build_quadratic_grid(nodes, c3d10_elements)

    print("Parsing FRD PE history. This may take a minute...")
    displacement_blocks, pe_blocks = parse_frd_history(
        frd_file,
        id_to_idx,
        len(used_ids),
    )

    displacement_blocks, pe_blocks = prepare_history_arrays(
        displacement_blocks,
        pe_blocks,
    )

    n_available = min(len(displacement_blocks), len(pe_blocks))
    frame_indices = select_frame_indices(n_available, MAX_FRAMES)

    all_pe = np.concatenate([pe_blocks[i] for i in frame_indices])
    pe_min = float(np.min(all_pe))
    pe_max = float(np.max(all_pe))
    pe_p95 = float(np.percentile(all_pe, 95.0))
    pe_p99 = float(np.percentile(all_pe, 99.0))

    color_max = pe_max
    if pe_max > 1.8 * pe_p99:
        color_max = pe_p99

    if args.check_only:
        print()
        print("PE history check")
        print("================")
        print(f"Case: {CASE_NAME}")
        print(f"Nodes in INP: {len(nodes)}")
        print(f"C3D10 elements in INP: {len(c3d10_elements)}")
        print(f"Rendered quadratic tetra nodes: {len(used_ids)}")
        print(f"Displacement result blocks: {len(displacement_blocks)}")
        print(f"PE result blocks: {len(pe_blocks)}")
        print(f"Available correlated frames: {n_available}")
        print(f"Selected frame count: {len(frame_indices)}")
        print(f"PE min over selected frames: {pe_min:.8e}")
        print(f"PE max over selected frames: {pe_max:.8e}")
        print(f"PE p95 over selected frames: {pe_p95:.8e}")
        print(f"PE p99 over selected frames: {pe_p99:.8e}")
        print(f"Color max used: {color_max:.8e}")
        return

    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(exist_ok=True)

    base = colormaps["viridis"].resampled(N_PE_LEVELS)
    discrete_cmap = ListedColormap(base(np.linspace(0, 1, N_PE_LEVELS)))

    scalar_bar_args = {
        "title": "PE [-]",
        "vertical": True,
        "position_x": 0.935,
        "position_y": 0.18,
        "height": 0.62,
        "width": 0.028,
        "title_font_size": 16,
        "label_font_size": 12,
        "fmt": "%.3f",
        "n_labels": N_PE_LEVELS + 1,
    }

    undeformed_surface = extract_surface_clean(grid)
    points0 = grid.points.copy()

    frame_paths = []

    for out_i, block_i in enumerate(frame_indices):
        u = displacement_blocks[block_i]
        pe = pe_blocks[block_i]

        frame_grid = grid.copy(deep=True)
        frame_grid.points = points0 + DEFORMATION_SCALE * u
        frame_grid.point_data["PE"] = pe

        surface = extract_surface_clean(frame_grid)

        u_max_frame = float(np.max(np.linalg.norm(u, axis=1)))
        pe_max_frame = float(np.max(pe))

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
            scalars="PE",
            clim=[0.0, color_max],
            cmap=discrete_cmap,
            n_colors=N_PE_LEVELS,
            interpolate_before_map=False,
            show_edges=False,
            smooth_shading=True,
            scalar_bar_args=scalar_bar_args,
        )

        progress = block_i / max(1, n_available - 1)

        title = (
            "Lab 006 — S355MC C3D10 tensile dogbone\n"
            f"plastic strain history animation   increment {block_i + 1}/{n_available}   "
            f"load fraction {progress:.2f}\n"
            f"max U = {u_max_frame:.3f} mm   "
            f"max PE = {pe_max_frame:.4f}   "
            f"deformation scale x{DEFORMATION_SCALE:g}"
        )

        plotter.add_text(
            title,
            position=(20, 835),
            font_size=13,
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

        frame_file = frames_dir / f"frame_{out_i:03d}.png"
        plotter.screenshot(str(frame_file))
        plotter.close()

        frame_paths.append(frame_file)
        gc.collect()

    images = [Image.open(p).convert("P", palette=Image.ADAPTIVE) for p in frame_paths]
    images[0].save(
        out_gif,
        save_all=True,
        append_images=images[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
    )

    summary_file = results_dir / "s355mc_pe_history_gif_summary.txt"
    summary = f"""Lab 006 — PyVista PE history GIF
================================

Case:
{CASE_NAME}

Input mesh:
{inp_file}

Result file:
{frd_file}

Parsed:
Nodes in INP: {len(nodes)}
C3D10 elements in INP: {len(c3d10_elements)}
Rendered quadratic tetra nodes: {len(used_ids)}
Displacement result blocks: {len(displacement_blocks)}
PE result blocks: {len(pe_blocks)}
Available correlated frames: {n_available}
Rendered frames: {len(frame_paths)}

PE over rendered frames:
min PE: {pe_min:.8e}
max PE: {pe_max:.8e}
p95 PE: {pe_p95:.8e}
p99 PE: {pe_p99:.8e}
color max used: {color_max:.8e}

Animation:
Frame duration: {FRAME_DURATION_MS} ms
Deformation scale: {DEFORMATION_SCALE}
Discrete color levels: {N_PE_LEVELS}

Output:
{out_gif}
"""
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
