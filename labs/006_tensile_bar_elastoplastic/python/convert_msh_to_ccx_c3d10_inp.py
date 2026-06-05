#!/usr/bin/env python3
"""
Convert the Lab 006 Gmsh 3D second-order tetra mesh to a CalculiX C3D10 input file.

Lab 006 is now S355MC-only.

Modes:
- default: force-displacement run with compact .dat output
- --viz: additionally writes nodal displacement field U to .frd for PyVista visualization

Important:
Gmsh MSH2 type 11 tetra10 midside-node order differs from CalculiX C3D10.
The converter remaps:
    Gmsh:     1,2,3,4, 12,23,31,14,34,24
    CalculiX: 1,2,3,4, 12,23,31,14,24,34
"""

from pathlib import Path
from collections import Counter
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from specimen_design import SpecimenGeometry


IN_CASE_NAME = "tensile_dogbone_iso6892_form1_3d"
OUT_CASE_BASENAME = "tensile_dogbone_iso6892_form1_c3d10"

RIGHT_DISPLACEMENT_MM = 2.0


def gmsh_tet10_to_ccx(conn):
    """
    Convert Gmsh MSH2 type 11 tetra10 ordering to CalculiX C3D10 ordering.

    Gmsh observed:
        1,2,3,4, 12,23,31,14,34,24

    CalculiX C3D10:
        1,2,3,4, 12,23,31,14,24,34
    """
    if len(conn) != 10:
        raise RuntimeError(f"Expected 10-node tetra, got {len(conn)} nodes.")

    n1, n2, n3, n4, n12, n23, n31, n14, n34, n24 = conn
    return (n1, n2, n3, n4, n12, n23, n31, n14, n24, n34)


def read_msh2(msh_file: Path):
    lines = msh_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    nodes = {}
    tetra10 = []
    etype_counter = Counter()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line == "$Nodes":
            n_nodes = int(lines[i + 1].strip())
            i += 2
            for _ in range(n_nodes):
                parts = lines[i].split()
                nid = int(parts[0])
                x, y, z = map(float, parts[1:4])
                nodes[nid] = (x, y, z)
                i += 1
            continue

        if line == "$Elements":
            n_elements = int(lines[i + 1].strip())
            i += 2
            for _ in range(n_elements):
                parts = lines[i].split()
                eid = int(parts[0])
                etype = int(parts[1])
                ntags = int(parts[2])
                conn = [int(v) for v in parts[3 + ntags:]]

                etype_counter[etype] += 1

                if etype == 11:
                    tetra10.append((eid, gmsh_tet10_to_ccx(tuple(conn))))

                i += 1
            continue

        i += 1

    if not nodes:
        raise RuntimeError(f"No nodes found in {msh_file}")
    if not tetra10:
        raise RuntimeError(f"No type 11 tetra10 elements found in {msh_file}")

    return nodes, tetra10, etype_counter


def signed_tet_volume6(nodes, conn):
    n1, n2, n3, n4 = conn[:4]

    x1, y1, z1 = nodes[n1]
    x2, y2, z2 = nodes[n2]
    x3, y3, z3 = nodes[n3]
    x4, y4, z4 = nodes[n4]

    ax, ay, az = x2 - x1, y2 - y1, z2 - z1
    bx, by, bz = x3 - x1, y3 - y1, z3 - z1
    cx, cy, cz = x4 - x1, y4 - y1, z4 - z1

    return (
        ax * (by * cz - bz * cy)
        - ay * (bx * cz - bz * cx)
        + az * (bx * cy - by * cx)
    )


def orient_c3d10_positive(nodes, conn):
    """
    Ensure positive corner tetra orientation.

    If corners 2 and 3 are swapped, midside nodes are remapped consistently.
    """
    vol6 = signed_tet_volume6(nodes, conn)

    if vol6 >= 0.0:
        return conn, False, vol6

    n1, n2, n3, n4, n12, n23, n31, n14, n24, n34 = conn

    corrected = (
        n1, n3, n2, n4,
        n31, n23, n12,
        n14, n34, n24,
    )

    return corrected, True, vol6


def write_nset(f, name: str, node_ids, per_line: int = 12):
    values = sorted(set(node_ids))
    f.write(f"*NSET, NSET={name}\n")
    for i in range(0, len(values), per_line):
        f.write(", ".join(str(v) for v in values[i:i + per_line]) + "\n")


def write_elset(f, name: str, elem_ids, per_line: int = 12):
    values = sorted(set(elem_ids))
    f.write(f"*ELSET, ELSET={name}\n")
    for i in range(0, len(values), per_line):
        f.write(", ".join(str(v) for v in values[i:i + per_line]) + "\n")


def pick_nearest_node(nodes, candidates, target):
    tx, ty, tz = target

    def dist2(nid):
        x, y, z = nodes[nid]
        return (x - tx) ** 2 + (y - ty) ** 2 + (z - tz) ** 2

    return min(candidates, key=dist2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--viz",
        action="store_true",
        help="Create visualization input and write nodal displacement field U to FRD.",
    )
    parser.add_argument(
        "--fields",
        action="store_true",
        help="Create full field-output input with U, S, E and PE for PyVista postprocessing.",
    )
    args = parser.parse_args()

    if args.viz and args.fields:
        raise SystemExit("Use either --viz or --fields, not both.")

    lab_dir = Path(__file__).resolve().parents[1]
    msh_file = lab_dir / "mesh" / f"{IN_CASE_NAME}.msh"
    input_dir = lab_dir / "input"
    input_dir.mkdir(exist_ok=True)

    material_name = "S355MC"
    material_inc = lab_dir / "materials" / "S355MC" / "s355mc_ccx_material.inc"
    if not material_inc.exists():
        raise FileNotFoundError(material_inc)

    if args.fields:
        out_case_name = f"{OUT_CASE_BASENAME}_s355mc_fields"
    elif args.viz:
        out_case_name = f"{OUT_CASE_BASENAME}_s355mc_viz"
    else:
        out_case_name = f"{OUT_CASE_BASENAME}_s355mc"

    out_file = input_dir / f"{out_case_name}.inp"

    geom = SpecimenGeometry()
    nodes, tetra10, etype_counter = read_msh2(msh_file)

    oriented_tetra10 = []
    negative_before = 0
    flipped_elements = 0
    near_zero_volume = 0

    for eid, conn in tetra10:
        corrected_conn, flipped, vol6 = orient_c3d10_positive(nodes, conn)

        if vol6 < 0.0:
            negative_before += 1
        if abs(vol6) < 1e-12:
            near_zero_volume += 1
        if flipped:
            flipped_elements += 1

        oriented_tetra10.append((eid, corrected_conn))

    tetra10 = oriented_tetra10

    xs = [p[0] for p in nodes.values()]
    ys = [p[1] for p in nodes.values()]
    zs = [p[2] for p in nodes.values()]

    x_min, x_max = min(xs), max(xs)
    y_max = max(ys)
    z_min, z_max = min(zs), max(zs)

    tol = 1e-6

    left_end = [nid for nid, (x, _y, _z) in nodes.items() if abs(x - x_min) < tol]
    right_end = [nid for nid, (x, _y, _z) in nodes.items() if abs(x - x_max) < tol]
    all_nodes = sorted(nodes)

    if not left_end or not right_end:
        raise RuntimeError("Could not identify left/right end nodes by x-coordinate.")

    left_center = pick_nearest_node(nodes, left_end, (x_min, 0.0, 0.0))
    left_ymax_center_z = pick_nearest_node(nodes, left_end, (x_min, y_max, 0.0))

    elem_ids = [eid for eid, _conn in tetra10]

    s0 = geom.thickness_a0_mm * geom.width_b0_mm
    yield_force_estimate = 355.0 * s0

    with out_file.open("w", encoding="utf-8") as f:
        f.write("*HEADING\n")
        f.write("Lab 006 - EN ISO 6892-1 flat dogbone tensile specimen, C3D10 S355MC\n")
        f.write("Generated by python/convert_msh_to_ccx_c3d10_inp.py\n")
        f.write("\n")

        f.write("*NODE\n")
        for nid in sorted(nodes):
            x, y, z = nodes[nid]
            f.write(f"{nid}, {x:.9f}, {y:.9f}, {z:.9f}\n")
        f.write("\n")

        f.write("*ELEMENT, TYPE=C3D10, ELSET=EALL\n")
        for eid, conn in tetra10:
            f.write(f"{eid}, " + ", ".join(str(nid) for nid in conn) + "\n")
        f.write("\n")

        write_nset(f, "ALLNODES", all_nodes)
        f.write("\n")
        write_nset(f, "LEFT_END", left_end)
        f.write("\n")
        write_nset(f, "RIGHT_END", right_end)
        f.write("\n")
        write_nset(f, "FIX_YZ_NODE", [left_center])
        f.write("\n")
        write_nset(f, "FIX_Z_NODE", [left_ymax_center_z])
        f.write("\n")

        write_elset(f, "EALL_SOLID", elem_ids)
        f.write("\n")

        f.write(material_inc.read_text(encoding="utf-8").rstrip() + "\n\n")

        f.write(f"*SOLID SECTION, ELSET=EALL_SOLID, MATERIAL={material_name}\n")
        f.write("\n")

        f.write("*BOUNDARY\n")
        f.write("LEFT_END, 1, 1, 0.0\n")
        f.write("FIX_YZ_NODE, 2, 3, 0.0\n")
        f.write("FIX_Z_NODE, 3, 3, 0.0\n")
        f.write("\n")

        f.write("*STEP, NLGEOM\n")
        f.write("*STATIC\n")
        f.write("0.01, 1.0, 1e-08, 0.05\n")
        f.write("\n")

        f.write("*BOUNDARY\n")
        f.write(f"RIGHT_END, 1, 1, {RIGHT_DISPLACEMENT_MM:.6f}\n")
        f.write("\n")

        if args.viz or args.fields:
            f.write("*NODE FILE, NSET=ALLNODES\n")
            f.write("U\n")
            f.write("\n")

        if args.fields:
            f.write("*EL FILE, ELSET=EALL_SOLID\n")
            f.write("S, E, PE\n")
            f.write("\n")

        f.write("*NODE PRINT, NSET=RIGHT_END\n")
        f.write("U, RF\n")
        f.write("\n")

        f.write("*NODE PRINT, NSET=LEFT_END\n")
        f.write("RF\n")
        f.write("\n")

        f.write("*END STEP\n")

    print(f"Written: {out_file}")
    print(f"Case name: {out_case_name}")
    print(f"Visualization mode: {args.viz}")
    print(f"Full field-output mode: {args.fields}")
    print(f"Material name: {material_name}")
    print(f"Nodes: {len(nodes)}")
    print(f"C3D10 elements: {len(tetra10)}")
    print(f"Negative corner orientation before correction: {negative_before}")
    print(f"Flipped C3D10 elements: {flipped_elements}")
    print(f"Near-zero corner volumes: {near_zero_volume}")
    print("Original Gmsh element types:")
    for etype, count in sorted(etype_counter.items()):
        print(f"  type {etype}: {count}")
    print(f"X bounds: {x_min:.6f} ... {x_max:.6f} mm")
    print(f"Y bounds: {min(ys):.6f} ... {max(ys):.6f} mm")
    print(f"Z bounds: {z_min:.6f} ... {z_max:.6f} mm")
    print(f"Left end nodes: {len(left_end)}")
    print(f"Right end nodes: {len(right_end)}")
    print(f"FIX_YZ_NODE: {left_center} at {nodes[left_center]}")
    print(f"FIX_Z_NODE: {left_ymax_center_z} at {nodes[left_ymax_center_z]}")
    print(f"S0: {s0:.6f} mm^2")
    print(f"Yield force estimate: {yield_force_estimate:.3f} N")
    print(f"Prescribed right displacement: {RIGHT_DISPLACEMENT_MM:.6f} mm")


if __name__ == "__main__":
    main()
