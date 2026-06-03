#!/usr/bin/env python3
"""
Postprocess the CalculiX .dat file for Lab 003.

The script extracts the displacement of the load nodes from the
CalculiX NODE PRINT output and compares the vertical tip displacement
with the analytical Euler-Bernoulli reference value.
"""

from pathlib import Path
import math


L = 1000.0
b = 100.0
s = 20.0
E = 71000.0
F_total = 1000.0

CASE_NAME = "cantilever_shell_gmsh"


def analytical_tip_displacement() -> float:
    """Euler-Bernoulli cantilever tip displacement in mm."""
    I = s * b**3 / 12.0
    return F_total * L**3 / (3.0 * E * I)


def parse_loadnode_displacements(dat_file: Path) -> dict[int, tuple[float, float, float]]:
    lines = dat_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    in_block = False
    values: dict[int, tuple[float, float, float]] = {}

    for line in lines:
        lower = line.lower()

        if "displacements" in lower and "set loadnodes" in lower:
            in_block = True
            continue

        if in_block:
            stripped = line.strip()

            if not stripped:
                continue

            if "displacements" in lower or "stresses" in lower or "forces" in lower:
                break

            parts = stripped.split()
            if len(parts) == 4:
                try:
                    node_id = int(parts[0])
                    u1 = float(parts[1])
                    u2 = float(parts[2])
                    u3 = float(parts[3])
                except ValueError:
                    continue

                values[node_id] = (u1, u2, u3)

    if not values:
        raise RuntimeError(f"No LOADNODES displacement block found in {dat_file}")

    return values


def main() -> None:
    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"

    dat_file = results_dir / f"{CASE_NAME}.dat"
    summary_file = results_dir / f"{CASE_NAME}_summary.txt"

    displacements = parse_loadnode_displacements(dat_file)

    u3_values = [u[2] for u in displacements.values()]
    u_magnitudes = [
        math.sqrt(u1**2 + u2**2 + u3**2)
        for u1, u2, u3 in displacements.values()
    ]

    ccx_mean_abs_u3 = sum(abs(v) for v in u3_values) / len(u3_values)
    ccx_max_abs_u = max(u_magnitudes)

    analytical = analytical_tip_displacement()
    error_percent = (ccx_mean_abs_u3 - analytical) / analytical * 100.0

    lines = []
    lines.append("Lab 003 — Gmsh Cantilever Shell Static Result")
    lines.append("=" * 52)
    lines.append("")
    lines.append(f"Load nodes: {sorted(displacements.keys())}")
    lines.append("")
    lines.append("Node displacements from CalculiX .dat:")
    for node_id, (u1, u2, u3) in sorted(displacements.items()):
        umag = math.sqrt(u1**2 + u2**2 + u3**2)
        lines.append(
            f"  node {node_id}: "
            f"U1 = {u1: .6f} mm, "
            f"U2 = {u2: .6e} mm, "
            f"U3 = {u3: .6f} mm, "
            f"|U| = {umag: .6f} mm"
        )

    lines.append("")
    lines.append(f"Analytical tip displacement:       {analytical:.6f} mm")
    lines.append(f"CalculiX mean abs(U3) load nodes:  {ccx_mean_abs_u3:.6f} mm")
    lines.append(f"CalculiX max abs(U) load nodes:    {ccx_max_abs_u:.6f} mm")
    lines.append(f"Relative error based on abs(U3):   {error_percent:.3f} %")
    lines.append("")

    text = "\n".join(lines)
    print(text)

    summary_file.write_text(text + "\n", encoding="utf-8")
    print(f"Written summary: {summary_file}")


if __name__ == "__main__":
    main()
