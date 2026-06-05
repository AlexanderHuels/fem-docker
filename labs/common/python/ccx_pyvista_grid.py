#!/usr/bin/env python3
"""
Build PyVista unstructured grids from CalculiX INP meshes.

Supported:
- C3D8  -> VTK/PyVista HEXAHEDRON
- C3D10 -> VTK/PyVista QUADRATIC_TETRA
"""

from pathlib import Path
import argparse
import sys

import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ccx_inp_mesh import read_ccx_inp_mesh


def build_pyvista_grid(mesh):
    """
    Build a PyVista UnstructuredGrid from a parsed CcxMesh.

    Returns:
    - grid
    - used_node_ids
    - node_id_to_index
    """
    used_node_ids = sorted({nid for _eid, conn in mesh.elements for nid in conn})
    node_id_to_index = {nid: i for i, nid in enumerate(used_node_ids)}

    points = np.array([mesh.nodes[nid] for nid in used_node_ids], dtype=float)

    cells = []
    celltypes = []

    if mesh.element_type == "C3D8":
        for _eid, conn in mesh.elements:
            local = [node_id_to_index[nid] for nid in conn]
            cells.extend([8] + local)
            celltypes.append(pv.CellType.HEXAHEDRON)

    elif mesh.element_type == "C3D10":
        for _eid, conn in mesh.elements:
            local = [node_id_to_index[nid] for nid in conn]
            cells.extend([10] + local)
            celltypes.append(pv.CellType.QUADRATIC_TETRA)

    else:
        raise RuntimeError(f"Unsupported element type: {mesh.element_type}")

    grid = pv.UnstructuredGrid(
        np.array(cells, dtype=np.int64),
        np.array(celltypes, dtype=np.uint8),
        points,
    )

    return grid, used_node_ids, node_id_to_index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inp", required=True, type=Path)
    parser.add_argument("--type", required=True, choices=["C3D8", "C3D10"])
    args = parser.parse_args()

    mesh = read_ccx_inp_mesh(args.inp, args.type)
    grid, used_node_ids, node_id_to_index = build_pyvista_grid(mesh)

    print("Common PyVista grid summary")
    print("===========================")
    print()
    print(f"Input: {args.inp}")
    print(f"Element type: {mesh.element_type}")
    print(f"Original nodes: {mesh.node_count}")
    print(f"Used nodes: {len(used_node_ids)}")
    print(f"Elements/cells: {mesh.element_count}")
    print(f"PyVista cells: {grid.n_cells}")
    print(f"PyVista points: {grid.n_points}")
    print(f"PyVista cell types: {sorted(set(grid.celltypes.tolist()))}")


if __name__ == "__main__":
    main()
