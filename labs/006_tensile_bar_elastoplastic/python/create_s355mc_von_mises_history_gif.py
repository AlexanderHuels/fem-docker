#!/usr/bin/env python3
"""
Create physically correlated von Mises GIF for Lab 006.

Each frame uses matching result blocks from the CalculiX FRD:
- displacement U from increment i
- stress tensor S from increment i
- von Mises stress computed from S of increment i

This is different from simply animating the final stress field.
"""

from pathlib import Path
import re
import math
import shutil
import gc
import numpy as np
from PIL import Image
import pyvista as pv
from matplotlib import colormaps
from matplotlib.colors import ListedColormap


CASE_NAME = "tensile_dogbone_iso6892_form1_c3d10_s355mc_fields"

WINDOW_SIZE = (1400, 700)
DEFORMATION_SCALE = 5.0
N_STRESS_LEVELS = 10
FRAME_DURATION_MS = 110
FINAL_FORCE_KN = 10.76
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


def finalize_block(kind, array, count, displacement_blocks, stress_blocks):
    if kind == "U" and count > 0:
        displacement_blocks.append(array)
    elif kind == "S" and count > 0:
        stress_blocks.append(array)


def parse_frd_history(frd_file: Path, id_to_idx, n_used_nodes: int):
    """
    Parse all displacement and stress result blocks.

    Returns:
    - list of U arrays, shape (n_used_nodes, 3)
    - list of von Mises arrays, shape (n_used_nodes,)
    """
    number_re = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?")

    displacement_blocks = []
    stress_blocks = []

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
                    stress_blocks,
                )
                current_kind = "U"
                current_array = np.full((n_used_nodes, 3), np.nan, dtype=float)
                current_count = 0
                continue

            if is_result_header and "STRESS" in upper:
                finalize_block(
                    current_kind,
                    current_array,
                    current_count,
                    displacement_blocks,
                    stress_blocks,
                )
                current_kind = "S"
                current_array = np.full(n_used_nodes, np.nan, dtype=float)
                current_count = 0
                continue

            if is_block_end:
                finalize_block(
                    current_kind,
                    current_array,
                    current_count,
                    displacement_blocks,
                    stress_blocks,
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

            elif current_kind == "S":
                if len(nums) < 7:
                    continue

                nid = int(float(nums[0]))
                idx = id_to_idx.get(nid)
                if idx is None:
                    continue

                vals = [float(v.replace("D", "E")) for v in nums[1:7]]
                sxx, syy, szz, sxy, syz, szx = vals

                vm = math.sqrt(
                    0.5
                    * (
                        (sxx - syy) ** 2
                        + (syy - szz) ** 2
                        + (szz - sxx) ** 2
                    )
                    + 3.0 * (sxy**2 + syz**2 + szx**2)
                )

                current_array[idx] = vm
                current_count += 1

    finalize_block(
        current_kind,
        current_array,
        current_count,
        displacement_blocks,
        stress_blocks,
    )

    if not displacement_blocks:
        raise RuntimeError("No displacement history blocks found in FRD.")
    if not stress_blocks:
        raise RuntimeError("No stress history blocks found in FRD.")

    n_frames = min(len(displacement_blocks), len(stress_blocks))
    return displacement_blocks[:n_frames], stress_blocks[:n_frames]


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


def main():
    pv.OFF_SCREEN = True
    pv.global_theme.background = "white"
    pv.global_theme.font.family = "arial"

    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"
    figures_dir = lab_dir / "figures"
    frames_dir = lab_dir / "frames_von_mises_history"

    figures_dir.mkdir(exist_ok=True)

    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(exist_ok=True)

    inp_file = results_dir / f"{CASE_NAME}.inp"
    frd_file = results_dir / f"{CASE_NAME}.frd"

    if not inp_file.exists():
        inp_file = lab_dir / "input" / f"{CASE_NAME}.inp"

    out_gif = figures_dir / "s355mc_von_mises_history_animation.gif"

    nodes, c3d10_elements = parse_inp_nodes_and_c3d10(inp_file)
    grid, used_ids, id_to_idx = build_quadratic_grid(nodes, c3d10_elements)

    print("Parsing FRD history. This may take a minute...")
    displacement_blocks, stress_blocks = parse_frd_history(
        frd_file,
        id_to_idx,
        len(used_ids),
    )

    n_available = min(len(displacement_blocks), len(stress_blocks))
    frame_indices = select_frame_indices(n_available, MAX_FRAMES)

    # Fill possible missing values and determine global color scaling.
    for i in range(n_available):
        u = displacement_blocks[i]
        if np.isnan(u).any():
            displacement_blocks[i] = np.nan_to_num(u, nan=0.0)

        vm = stress_blocks[i]
        finite = vm[np.isfinite(vm)]
        fill = float(np.nanmin(finite)) if finite.size else 0.0
        stress_blocks[i] = np.nan_to_num(vm, nan=fill)

    all_vm = np.concatenate([stress_blocks[i] for i in frame_indices])
    vm_min = float(np.min(all_vm))
    vm_max = float(np.max(all_vm))
    vm_p99 = float(np.percentile(all_vm, 99.0))

    color_max = vm_max
    if vm_max > 1.8 * vm_p99:
        color_max = vm_p99

    base = colormaps["turbo"].resampled(N_STRESS_LEVELS)
    discrete_cmap = ListedColormap(base(np.linspace(0, 1, N_STRESS_LEVELS)))

    scalar_bar_args = {
        "title": "S_vm [MPa]",
        "vertical": True,
        "position_x": 0.935,
        "position_y": 0.18,
        "height": 0.62,
        "width": 0.028,
        "title_font_size": 16,
        "label_font_size": 12,
        "fmt": "%.0f",
        "n_labels": N_STRESS_LEVELS + 1,
    }

    undeformed_surface = extract_surface_clean(grid)
    points0 = grid.points.copy()

    frame_paths = []

    for out_i, block_i in enumerate(frame_indices):
        u = displacement_blocks[block_i]
        vm = stress_blocks[block_i]

        frame_grid = grid.copy(deep=True)
        frame_grid.points = points0 + DEFORMATION_SCALE * u
        frame_grid.point_data["S_vm"] = vm

        surface = extract_surface_clean(frame_grid)

        u_max_frame = float(np.max(np.linalg.norm(u, axis=1)))
        vm_max_frame = float(np.max(vm))

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
            scalars="S_vm",
            clim=[0.0, color_max],
            cmap=discrete_cmap,
            n_colors=N_STRESS_LEVELS,
            interpolate_before_map=False,
            show_edges=False,
            smooth_shading=True,
            scalar_bar_args=scalar_bar_args,
        )

        progress = block_i / max(1, n_available - 1)

        title = (
            "Lab 006 — S355MC C3D10 tensile dogbone\n"
            f"von Mises history animation   increment {block_i + 1}/{n_available}   "
            f"load fraction {progress:.2f}\n"
            f"max U = {u_max_frame:.3f} mm   "
            f"max S_vm = {vm_max_frame:.1f} MPa   "
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

    summary_file = results_dir / "s355mc_von_mises_history_gif_summary.txt"
    summary = f"""Lab 006 — PyVista von Mises history GIF
========================================

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
Stress result blocks: {len(stress_blocks)}
Available correlated frames: {n_available}
Rendered frames: {len(frame_paths)}

von Mises over rendered frames:
min S_vm: {vm_min:.6f} MPa
max S_vm: {vm_max:.6f} MPa
p99 S_vm: {vm_p99:.6f} MPa
color max used: {color_max:.6f} MPa

Animation:
Frame duration: {FRAME_DURATION_MS} ms
Deformation scale: {DEFORMATION_SCALE}
Discrete color levels: {N_STRESS_LEVELS}

Output:
{out_gif}
"""
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
