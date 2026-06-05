#!/usr/bin/env python3
"""
Common CalculiX FRD result parser for FEM Docker labs.

Supported nodal FRD result blocks:
- DISP / DISPLACEMENT -> displacement vector U, shape (n_used_nodes, 3)
- STRESS              -> stress tensor components, shape (n_used_nodes, 6)
- PE                  -> scalar plastic strain, shape (n_used_nodes,)

Note:
CalculiX input may request PEEQ, but the FRD result label is commonly PE.
"""

from pathlib import Path
import argparse
import re
import sys

import numpy as np


NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?")


def _numbers_from_frd_line(line: str):
    return NUMBER_RE.findall(line.replace("D", "E"))


def _finalize_block(kind, array, displacement_blocks, stress_blocks, pe_blocks):
    if kind == "U":
        displacement_blocks.append(array)
    elif kind == "STRESS":
        stress_blocks.append(array)
    elif kind == "PE":
        pe_blocks.append(array)


def parse_frd_history(frd_file: Path, id_to_idx: dict[int, int], n_used_nodes: int):
    """
    Parse all available U, STRESS and PE blocks from a CalculiX FRD file.

    Returns:
    - displacement_blocks: list[np.ndarray], each shape (n_used_nodes, 3)
    - stress_blocks:       list[np.ndarray], each shape (n_used_nodes, 6)
    - pe_blocks:           list[np.ndarray], each shape (n_used_nodes,)
    """
    displacement_blocks = []
    stress_blocks = []
    pe_blocks = []

    current_kind = None
    current_array = None

    with frd_file.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            upper = raw.upper()
            stripped = raw.lstrip()

            is_result_header = stripped.startswith("-4")
            is_block_end = stripped.startswith("-3")
            is_value_line = stripped.startswith("-1")

            if is_result_header:
                if current_kind is not None:
                    _finalize_block(
                        current_kind,
                        current_array,
                        displacement_blocks,
                        stress_blocks,
                        pe_blocks,
                    )

                current_kind = None
                current_array = None

                if "DISP" in upper or "DISPLACEMENT" in upper:
                    current_kind = "U"
                    current_array = np.full((n_used_nodes, 3), np.nan, dtype=float)
                    continue

                if "STRESS" in upper:
                    current_kind = "STRESS"
                    current_array = np.full((n_used_nodes, 6), np.nan, dtype=float)
                    continue

                # CalculiX FRD label for equivalent plastic strain is PE.
                if " PE " in upper:
                    current_kind = "PE"
                    current_array = np.full(n_used_nodes, np.nan, dtype=float)
                    continue

                continue

            if is_block_end:
                if current_kind is not None:
                    _finalize_block(
                        current_kind,
                        current_array,
                        displacement_blocks,
                        stress_blocks,
                        pe_blocks,
                    )
                current_kind = None
                current_array = None
                continue

            if current_kind is None or not is_value_line:
                continue

            nums = _numbers_from_frd_line(raw[3:])
            if len(nums) < 2:
                continue

            nid = int(float(nums[0]))
            idx = id_to_idx.get(nid)

            if idx is None:
                continue

            if current_kind == "U":
                if len(nums) >= 4:
                    current_array[idx, :] = [
                        float(nums[1].replace("D", "E")),
                        float(nums[2].replace("D", "E")),
                        float(nums[3].replace("D", "E")),
                    ]

            elif current_kind == "STRESS":
                if len(nums) >= 7:
                    current_array[idx, :] = [
                        float(nums[1].replace("D", "E")),
                        float(nums[2].replace("D", "E")),
                        float(nums[3].replace("D", "E")),
                        float(nums[4].replace("D", "E")),
                        float(nums[5].replace("D", "E")),
                        float(nums[6].replace("D", "E")),
                    ]

            elif current_kind == "PE":
                if len(nums) >= 2:
                    current_array[idx] = float(nums[1].replace("D", "E"))

    if current_kind is not None:
        _finalize_block(
            current_kind,
            current_array,
            displacement_blocks,
            stress_blocks,
            pe_blocks,
        )

    return displacement_blocks, stress_blocks, pe_blocks


def von_mises_from_stress(stress_array):
    """
    Compute von Mises stress from stress tensor components.

    Assumed component order:
    Sxx, Syy, Szz, Sxy, Syz, Szx
    """
    sxx = stress_array[:, 0]
    syy = stress_array[:, 1]
    szz = stress_array[:, 2]
    sxy = stress_array[:, 3]
    syz = stress_array[:, 4]
    szx = stress_array[:, 5]

    return np.sqrt(
        0.5 * (
            (sxx - syy) ** 2
            + (syy - szz) ** 2
            + (szz - sxx) ** 2
        )
        + 3.0 * (sxy ** 2 + syz ** 2 + szx ** 2)
    )


def clean_history_blocks(displacement_blocks, stress_blocks, pe_blocks):
    """
    Replace NaNs and clip tiny negative PE numerical noise.
    """
    for i, u in enumerate(displacement_blocks):
        displacement_blocks[i] = np.nan_to_num(u, nan=0.0)

    for i, s in enumerate(stress_blocks):
        if np.isnan(s).all():
            stress_blocks[i] = np.zeros_like(s)
        else:
            fill = float(np.nanmedian(s))
            stress_blocks[i] = np.nan_to_num(s, nan=fill)

    for i, pe in enumerate(pe_blocks):
        if np.isnan(pe).all():
            pe_blocks[i] = np.zeros_like(pe)
        else:
            fill = float(np.nanmedian(pe))
            pe = np.nan_to_num(pe, nan=fill)
            pe_blocks[i] = np.maximum(pe, 0.0)

    return displacement_blocks, stress_blocks, pe_blocks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frd", required=True, type=Path)
    parser.add_argument("--inp", required=True, type=Path)
    parser.add_argument("--type", required=True, choices=["C3D8", "C3D10"])
    args = parser.parse_args()

    common_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(common_dir))

    from ccx_inp_mesh import read_ccx_inp_mesh
    from ccx_pyvista_grid import build_pyvista_grid

    mesh = read_ccx_inp_mesh(args.inp, args.type)
    _grid, used_node_ids, id_to_idx = build_pyvista_grid(mesh)

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

    print("Common CCX FRD result parser summary")
    print("====================================")
    print()
    print(f"INP: {args.inp}")
    print(f"FRD: {args.frd}")
    print(f"Element type: {mesh.element_type}")
    print(f"Used nodes: {len(used_node_ids)}")
    print()
    print(f"Displacement blocks: {len(displacement_blocks)}")
    print(f"Stress blocks: {len(stress_blocks)}")
    print(f"PE blocks: {len(pe_blocks)}")

    if displacement_blocks:
        u_final = displacement_blocks[-1]
        u_mag = np.linalg.norm(u_final, axis=1)
        print()
        print("Final displacement:")
        print(f"- min |U|: {float(np.min(u_mag)):.8e} mm")
        print(f"- max |U|: {float(np.max(u_mag)):.8e} mm")

    if stress_blocks:
        vm_final = von_mises_from_stress(stress_blocks[-1])
        print()
        print("Final von Mises:")
        print(f"- min S_vm: {float(np.min(vm_final)):.8e} MPa")
        print(f"- max S_vm: {float(np.max(vm_final)):.8e} MPa")
        print(f"- p99 S_vm: {float(np.percentile(vm_final, 99.0)):.8e} MPa")

    if pe_blocks:
        pe_final = pe_blocks[-1]
        print()
        print("Final PE / requested PEEQ:")
        print(f"- min PE: {float(np.min(pe_final)):.8e}")
        print(f"- max PE: {float(np.max(pe_final)):.8e}")
        print(f"- p99 PE: {float(np.percentile(pe_final, 99.0)):.8e}")


if __name__ == "__main__":
    main()
