#!/usr/bin/env python3
"""
Postprocess Lab 002 mesh convergence results.

The script reads:
- results/mesh_variants.csv
- CalculiX .dat files for all mesh variants

It writes:
- results/convergence_results.csv
- results/convergence_summary.md
"""

from pathlib import Path
import csv
import math


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

    variants_file = results_dir / "mesh_variants.csv"
    out_csv = results_dir / "convergence_results.csv"
    out_md = results_dir / "convergence_summary.md"

    with variants_file.open("r", newline="", encoding="utf-8") as f:
        variants = list(csv.DictReader(f))

    rows = []

    for variant in variants:
        case_name = variant["case_name"]
        dat_file = results_dir / f"{case_name}.dat"

        displacements = parse_loadnode_displacements(dat_file)

        u3_values = [u[2] for u in displacements.values()]
        u_magnitudes = [
            math.sqrt(u1**2 + u2**2 + u3**2)
            for u1, u2, u3 in displacements.values()
        ]

        mean_abs_u3 = sum(abs(v) for v in u3_values) / len(u3_values)
        max_abs_u = max(u_magnitudes)

        analytical = float(variant["analytical_tip_displacement_mm"])
        error_vs_analytical = (mean_abs_u3 - analytical) / analytical * 100.0

        rows.append({
            "case_name": case_name,
            "nx": int(variant["nx"]),
            "nz": int(variant["nz"]),
            "nodes": int(variant["nodes"]),
            "elements": int(variant["elements"]),
            "element_size_x_mm": float(variant["element_size_x_mm"]),
            "mean_abs_u3_mm": mean_abs_u3,
            "max_abs_u_mm": max_abs_u,
            "analytical_tip_displacement_mm": analytical,
            "error_vs_analytical_percent": error_vs_analytical,
        })

    rows.sort(key=lambda row: row["nx"])

    finest_u3 = rows[-1]["mean_abs_u3_mm"]

    for row in rows:
        row["error_vs_finest_percent"] = (
            (row["mean_abs_u3_mm"] - finest_u3) / finest_u3 * 100.0
        )

    fieldnames = [
        "case_name",
        "nx",
        "nz",
        "nodes",
        "elements",
        "element_size_x_mm",
        "mean_abs_u3_mm",
        "max_abs_u_mm",
        "analytical_tip_displacement_mm",
        "error_vs_analytical_percent",
        "error_vs_finest_percent",
    ]

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md_lines = []
    md_lines.append("# Lab 002 — Mesh Convergence Results")
    md_lines.append("")
    md_lines.append("Cantilever shell benchmark solved with CalculiX 2.23 in Docker.")
    md_lines.append("")
    md_lines.append(f"Analytical Euler-Bernoulli reference: {rows[0]['analytical_tip_displacement_mm']:.6f} mm")
    md_lines.append(f"Finest FE reference used here: nx={rows[-1]['nx']}, U3={finest_u3:.6f} mm")
    md_lines.append("")
    md_lines.append("| nx | elements | element size x [mm] | mean abs(U3) [mm] | error vs analytical [%] | error vs finest [%] |")
    md_lines.append("|---:|---------:|--------------------:|---------------:|------------------------:|--------------------:|")

    for row in rows:
        md_lines.append(
            f"| {row['nx']} "
            f"| {row['elements']} "
            f"| {row['element_size_x_mm']:.3f} "
            f"| {row['mean_abs_u3_mm']:.6f} "
            f"| {row['error_vs_analytical_percent']:.3f} "
            f"| {row['error_vs_finest_percent']:.3f} |"
        )

    md_lines.append("")
    md_lines.append("Observation:")
    md_lines.append("")
    md_lines.append("- The computed tip displacement increases with mesh refinement.")
    md_lines.append("- The coarse nx=5 mesh is clearly too stiff.")
    md_lines.append("- The solution is already close to the finest nx=80 reference from nx=20 onward.")
    md_lines.append("- The comparison against Euler-Bernoulli theory is useful as an analytical check, but the FE shell model converges toward its own shell-model reference solution.")

    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Written: {out_csv}")
    print(f"Written: {out_md}")
    print("")
    print(out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
