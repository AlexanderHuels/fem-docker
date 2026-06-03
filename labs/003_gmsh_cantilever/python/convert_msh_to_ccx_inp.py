#!/usr/bin/env python3
"""
Convert the Gmsh MSH2 quad mesh into a CalculiX shell input file.

This converter is intentionally small and specific to Lab 003:
- reads ASCII MSH2 format
- extracts 4-node quadrilateral elements
- detects fixed and free-edge nodes from coordinates
- writes a CalculiX S4 shell model
"""

from pathlib import Path
import math


# ---------------------------------------------------------------------------
# Physical/model parameters
# ---------------------------------------------------------------------------

L = 1000.0
b = 100.0
s = 20.0

E = 71000.0
nu = 0.3

F_total = -1000.0

CASE_NAME = "cantilever_shell_gmsh"


def analytical_tip_displacement() -> float:
    I = s * b**3 / 12.0
    return abs(F_total) * L**3 / (3.0 * E * I)


def read_msh2(msh_file: Path):
    lines = msh_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    nodes = {}
    quad_elements = []

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

                node_ids = list(map(int, parts[3 + ntags:]))

                # Gmsh MSH2 element type 3 = 4-node quadrangle
                if etype == 3:
                    quad_elements.append((eid, node_ids))

                i += 1
            continue

        i += 1

    if not nodes:
        raise RuntimeError(f"No nodes found in {msh_file}")

    if not quad_elements:
        raise RuntimeError(f"No 4-node quad elements found in {msh_file}")

    return nodes, quad_elements


def write_nset(f, name: str, values: list[int], chunk_size: int = 12) -> None:
    f.write(f"*NSET, NSET={name}\n")
    for i in range(0, len(values), chunk_size):
        chunk = values[i:i + chunk_size]
        f.write(", ".join(str(v) for v in chunk) + "\n")


def main() -> None:
    lab_dir = Path(__file__).resolve().parents[1]
    msh_file = lab_dir / "mesh" / f"{CASE_NAME}.msh"
    inp_file = lab_dir / "input" / f"{CASE_NAME}.inp"

    nodes, quad_elements = read_msh2(msh_file)

    tol = 1.0e-6

    fixed_nodes = sorted(
        nid for nid, (x, y, z) in nodes.items()
        if abs(x - 0.0) < tol
    )

    free_end_nodes = sorted(
        nid for nid, (x, y, z) in nodes.items()
        if abs(x - L) < tol
    )

    if not fixed_nodes:
        raise RuntimeError("No fixed-edge nodes found at x=0")

    if not free_end_nodes:
        raise RuntimeError("No free-edge nodes found at x=L")

    # Select two free-end nodes closest to z=0.
    load_nodes = sorted(
        free_end_nodes,
        key=lambda nid: (abs(nodes[nid][2]), nodes[nid][2])
    )[:2]

    load_per_node = F_total / len(load_nodes)

    # Renumber quad elements sequentially for clean CCX input.
    ccx_elements = []
    for new_eid, (_gmsh_eid, conn) in enumerate(quad_elements, start=1):
        if len(conn) != 4:
            raise RuntimeError(f"Unexpected quad connectivity: {conn}")
        ccx_elements.append((new_eid, conn))

    with inp_file.open("w", encoding="utf-8") as f:
        f.write("*HEADING\n")
        f.write("Lab 003 - Gmsh generated cantilever shell benchmark\n")
        f.write("Generated from mesh/cantilever_shell_gmsh.msh\n")
        f.write("\n")

        f.write("*NODE\n")
        for nid in sorted(nodes):
            x, y, z = nodes[nid]
            f.write(f"{nid}, {x:.6f}, {y:.6f}, {z:.6f}\n")
        f.write("\n")

        f.write("*ELEMENT, TYPE=S4, ELSET=EALL\n")
        for eid, conn in ccx_elements:
            f.write(f"{eid}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}\n")
        f.write("\n")

        write_nset(f, "FIXED", fixed_nodes)
        f.write("\n")
        write_nset(f, "FREE_END", free_end_nodes)
        f.write("\n")
        write_nset(f, "LOADNODES", load_nodes)
        f.write("\n")

        f.write("*MATERIAL, NAME=ALUMINUM\n")
        f.write("*ELASTIC\n")
        f.write(f"{E:.6f}, {nu:.6f}\n")
        f.write("\n")

        f.write("*SHELL SECTION, ELSET=EALL, MATERIAL=ALUMINUM\n")
        f.write(f"{s:.6f}\n")
        f.write("\n")

        f.write("*BOUNDARY\n")
        f.write("FIXED, 1, 6, 0.\n")
        f.write("\n")

        f.write("*STEP\n")
        f.write("*STATIC\n")
        f.write("\n")

        f.write("*CLOAD\n")
        for nid in load_nodes:
            f.write(f"{nid}, 3, {load_per_node:.6f}\n")
        f.write("\n")

        f.write("*NODE FILE\n")
        f.write("U, RF\n")
        f.write("\n")

        f.write("*NODE PRINT, NSET=LOADNODES\n")
        f.write("U\n")
        f.write("\n")

        f.write("*END STEP\n")

    print(f"Read mesh: {msh_file}")
    print(f"Written: {inp_file}")
    print(f"Nodes: {len(nodes)}")
    print(f"Quad shell elements: {len(ccx_elements)}")
    print(f"Fixed nodes: {len(fixed_nodes)}")
    print(f"Free-end nodes: {len(free_end_nodes)}")
    print(f"Load nodes: {load_nodes}")
    print(f"Load per node: {load_per_node:.3f} N")
    print(f"Analytical tip displacement: {analytical_tip_displacement():.6f} mm")


if __name__ == "__main__":
    main()
