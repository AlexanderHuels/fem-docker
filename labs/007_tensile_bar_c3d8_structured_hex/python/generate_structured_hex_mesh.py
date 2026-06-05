#!/usr/bin/env python3
"""
Generate the first structured full C3D8 mesh for Lab 007.

Outputs:
- mesh/structured_hex_nodes.csv
- mesh/structured_hex_elements.csv
- results/structured_hex_mesh_summary.txt
"""

from pathlib import Path
import csv
import math
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mesh_design import SpecimenGeometry, StructuredHexMeshDesign
from generate_structured_stations import build_x_stations, half_width_at_x, linspace


def signed_hex_corner_volume(p1, p2, p4, p5):
    """
    Simple orientation check using corner vectors from node 1:
      v12 = p2 - p1
      v14 = p4 - p1
      v15 = p5 - p1
    """
    v12 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
    v14 = (p4[0] - p1[0], p4[1] - p1[1], p4[2] - p1[2])
    v15 = (p5[0] - p1[0], p5[1] - p1[1], p5[2] - p1[2])

    cross = (
        v14[1] * v15[2] - v14[2] * v15[1],
        v14[2] * v15[0] - v14[0] * v15[2],
        v14[0] * v15[1] - v14[1] * v15[0],
    )
    return v12[0] * cross[0] + v12[1] * cross[1] + v12[2] * cross[2]


def main():
    geom = SpecimenGeometry()
    mesh = StructuredHexMeshDesign()

    lab_dir = Path(__file__).resolve().parents[1]
    mesh_dir = lab_dir / "mesh"
    results_dir = lab_dir / "results"
    mesh_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    x_values = build_x_stations(geom, mesh)
    eta_values = linspace(-1.0, 1.0, mesh.width_element_divisions + 1)
    z_values = linspace(
        -0.5 * geom.thickness_a0_mm,
        0.5 * geom.thickness_a0_mm,
        mesh.thickness_element_layers + 1,
    )

    nodes_csv = mesh_dir / "structured_hex_nodes.csv"
    elems_csv = mesh_dir / "structured_hex_elements.csv"
    summary_txt = results_dir / "structured_hex_mesh_summary.txt"

    node_id_map = {}
    node_xyz = {}
    nodes = []
    nid = 1

    # -----------------------------
    # Nodes
    # -----------------------------
    for ix, x in enumerate(x_values):
        hw = half_width_at_x(x, geom)
        for iy, eta in enumerate(eta_values):
            y = eta * hw
            for iz, z in enumerate(z_values):
                node_id_map[(ix, iy, iz)] = nid
                node_xyz[nid] = (x, y, z)
                nodes.append((nid, x, y, z, ix, iy, iz))
                nid += 1

    # -----------------------------
    # Elements
    # -----------------------------
    elements = []
    eid = 1

    for ix in range(len(x_values) - 1):
        for iy in range(len(eta_values) - 1):
            for iz in range(len(z_values) - 1):
                n1 = node_id_map[(ix,     iy,     iz    )]
                n2 = node_id_map[(ix + 1, iy,     iz    )]
                n3 = node_id_map[(ix + 1, iy + 1, iz    )]
                n4 = node_id_map[(ix,     iy + 1, iz    )]
                n5 = node_id_map[(ix,     iy,     iz + 1)]
                n6 = node_id_map[(ix + 1, iy,     iz + 1)]
                n7 = node_id_map[(ix + 1, iy + 1, iz + 1)]
                n8 = node_id_map[(ix,     iy + 1, iz + 1)]

                elements.append((eid, n1, n2, n3, n4, n5, n6, n7, n8, ix, iy, iz))
                eid += 1

    # -----------------------------
    # Write node CSV
    # -----------------------------
    with nodes_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nid", "x_mm", "y_mm", "z_mm", "ix", "iy", "iz"])
        writer.writerows(nodes)

    # -----------------------------
    # Write element CSV
    # -----------------------------
    with elems_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["eid", "n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8", "ix", "iy", "iz"])
        writer.writerows(elements)

    # -----------------------------
    # Checks
    # -----------------------------
    x_min = min(x_values)
    x_max = max(x_values)
    z_min = min(z_values)
    z_max = max(z_values)

    y_values_all = [row[2] for row in nodes]
    y_min = min(y_values_all)
    y_max = max(y_values_all)

    left_end_nodes = [nid for nid, x, y, z, ix, iy, iz in nodes if abs(x - x_min) < 1e-12]
    right_end_nodes = [nid for nid, x, y, z, ix, iy, iz in nodes if abs(x - x_max) < 1e-12]
    x0_nodes = [nid for nid, x, y, z, ix, iy, iz in nodes if abs(x) < 1e-12]
    y0_nodes = [nid for nid, x, y, z, ix, iy, iz in nodes if abs(y) < 1e-12]
    z0_nodes = [nid for nid, x, y, z, ix, iy, iz in nodes if abs(z) < 1e-12]

    # orientation check on first element
    first_e = elements[0]
    p1 = node_xyz[first_e[1]]
    p2 = node_xyz[first_e[2]]
    p4 = node_xyz[first_e[4]]
    p5 = node_xyz[first_e[5]]
    signed_vol_indicator = signed_hex_corner_volume(p1, p2, p4, p5)

    expected_nodes = len(x_values) * len(eta_values) * len(z_values)
    expected_elems = (len(x_values) - 1) * (len(eta_values) - 1) * (len(z_values) - 1)

    summary = f"""Lab 007 — Structured Hex Mesh Generation
========================================

Specimen:
- total length Lt: {geom.total_length_Lt_mm:.3f} mm
- reduced width b0: {geom.width_b0_mm:.3f} mm
- head width B: {geom.head_width_B_mm:.3f} mm
- thickness a0: {geom.thickness_a0_mm:.3f} mm

Structured mesh:
- x stations: {len(x_values)}
- width stations: {len(eta_values)}
- z stations: {len(z_values)}

Generated:
- nodes: {len(nodes)}
- C3D8 elements: {len(elements)}

Expected:
- nodes: {expected_nodes}
- C3D8 elements: {expected_elems}

Node-set style counts:
- LEFT_END nodes: {len(left_end_nodes)}
- RIGHT_END nodes: {len(right_end_nodes)}
- X0 plane nodes: {len(x0_nodes)}
- Y0 plane nodes: {len(y0_nodes)}
- Z0 plane nodes: {len(z0_nodes)}

Bounds:
- x: {x_min:.6f} ... {x_max:.6f} mm
- y: {y_min:.6f} ... {y_max:.6f} mm
- z: {z_min:.6f} ... {z_max:.6f} mm

Orientation check:
- first element signed corner volume indicator: {signed_vol_indicator:.12f}
- positive orientation expected: {signed_vol_indicator > 0.0}

Output files:
{nodes_csv}
{elems_csv}
"""

    summary_txt.write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
