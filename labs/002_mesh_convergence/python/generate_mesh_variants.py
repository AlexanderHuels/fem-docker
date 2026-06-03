#!/usr/bin/env python3
"""
Generate CalculiX input files for Lab 002 mesh convergence study.

Unit system:
- Force: N
- Length: mm
- Stress: MPa = N/mm²
"""

from pathlib import Path
import csv


# ---------------------------------------------------------------------------
# Model parameters
# ---------------------------------------------------------------------------

L = 1000.0
b = 100.0
s = 20.0

E = 71000.0
nu = 0.3

F_total = -1000.0

NX_VARIANTS = [5, 10, 20, 40, 80]
NZ = 5


def analytical_tip_displacement() -> float:
    """Euler-Bernoulli cantilever tip displacement in mm."""
    I = s * b**3 / 12.0
    return abs(F_total) * L**3 / (3.0 * E * I)


def node_id(i: int, j: int, nz: int) -> int:
    return i * (nz + 1) + j + 1


def chunks(values, size=12):
    for i in range(0, len(values), size):
        yield values[i:i + size]


def write_nset(file, name: str, values: list[int]) -> None:
    file.write(f"*NSET, NSET={name}\n")
    for chunk in chunks(values):
        file.write(", ".join(str(v) for v in chunk) + "\n")


def build_variant(nx: int, nz: int) -> dict:
    nodes = []
    for i in range(nx + 1):
        x = L * i / nx
        for j in range(nz + 1):
            z = -b / 2.0 + b * j / nz
            y = 0.0
            nodes.append((node_id(i, j, nz), x, y, z))

    elements = []
    eid = 1
    for i in range(nx):
        for j in range(nz):
            n1 = node_id(i, j, nz)
            n2 = node_id(i + 1, j, nz)
            n3 = node_id(i + 1, j + 1, nz)
            n4 = node_id(i, j + 1, nz)
            elements.append((eid, n1, n2, n3, n4))
            eid += 1

    fixed_nodes = [node_id(0, j, nz) for j in range(nz + 1)]
    free_end_nodes = [node_id(nx, j, nz) for j in range(nz + 1)]

    node_z = {nid: z for nid, _x, _y, z in nodes}
    load_nodes = sorted(free_end_nodes, key=lambda nid: (abs(node_z[nid]), node_z[nid]))[:2]
    load_per_node = F_total / len(load_nodes)

    return {
        "nx": nx,
        "nz": nz,
        "nodes": nodes,
        "elements": elements,
        "fixed_nodes": fixed_nodes,
        "free_end_nodes": free_end_nodes,
        "load_nodes": load_nodes,
        "load_per_node": load_per_node,
        "element_size_x": L / nx,
    }


def write_inp(case: dict, out_file: Path) -> None:
    with out_file.open("w", encoding="utf-8") as f:
        f.write("*HEADING\n")
        f.write("Lab 002 - Cantilever shell mesh convergence study\n")
        f.write(f"nx={case['nx']}, nz={case['nz']}\n")
        f.write("\n")

        f.write("*NODE\n")
        for nid, x, y, z in case["nodes"]:
            f.write(f"{nid}, {x:.6f}, {y:.6f}, {z:.6f}\n")
        f.write("\n")

        f.write("*ELEMENT, TYPE=S4, ELSET=EALL\n")
        for eid, n1, n2, n3, n4 in case["elements"]:
            f.write(f"{eid}, {n1}, {n2}, {n3}, {n4}\n")
        f.write("\n")

        write_nset(f, "FIXED", case["fixed_nodes"])
        f.write("\n")
        write_nset(f, "FREE_END", case["free_end_nodes"])
        f.write("\n")
        write_nset(f, "LOADNODES", case["load_nodes"])
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
        for nid in case["load_nodes"]:
            f.write(f"{nid}, 3, {case['load_per_node']:.6f}\n")
        f.write("\n")

        f.write("*NODE FILE\n")
        f.write("U, RF\n")
        f.write("\n")

        f.write("*NODE PRINT, NSET=LOADNODES\n")
        f.write("U\n")
        f.write("\n")

        f.write("*END STEP\n")


def main() -> None:
    lab_dir = Path(__file__).resolve().parents[1]
    input_dir = lab_dir / "input"
    results_dir = lab_dir / "results"

    input_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    analytical = analytical_tip_displacement()
    rows = []

    for nx in NX_VARIANTS:
        case = build_variant(nx=nx, nz=NZ)
        case_name = f"cantilever_shell_nx{nx:03d}_nz{NZ:03d}"
        inp_file = input_dir / f"{case_name}.inp"

        write_inp(case, inp_file)

        rows.append({
            "case_name": case_name,
            "nx": nx,
            "nz": NZ,
            "nodes": len(case["nodes"]),
            "elements": len(case["elements"]),
            "element_size_x_mm": case["element_size_x"],
            "load_nodes": " ".join(str(n) for n in case["load_nodes"]),
            "load_per_node_N": case["load_per_node"],
            "analytical_tip_displacement_mm": analytical,
        })

        print(
            f"Written {inp_file.name}: "
            f"nx={nx}, nz={NZ}, nodes={len(case['nodes'])}, "
            f"elements={len(case['elements'])}, load_nodes={case['load_nodes']}"
        )

    csv_file = results_dir / "mesh_variants.csv"
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Written metadata: {csv_file}")
    print(f"Analytical tip displacement: {analytical:.6f} mm")


if __name__ == "__main__":
    main()
