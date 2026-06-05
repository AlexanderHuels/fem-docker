#!/usr/bin/env python3
"""
Postprocess Lab 007 CalculiX .dat output.

Extract:
- mean right-end displacement U1
- summed reaction force RF1 on left and right end node sets
- force-displacement curve

Usage:
    python3 postprocess_force_displacement.py \
        --case tensile_dogbone_iso6892_form1_c3d8_s355mc
"""

from pathlib import Path
import argparse
import csv
import re


DEFAULT_CASE_NAME = "tensile_dogbone_iso6892_form1_c3d10_elastoplastic"


def short_case_label(case_name: str) -> str:
    if case_name.endswith("_s355mc"):
        return "s355mc"
    if case_name.endswith("_elastoplastic"):
        return "demo"
    return case_name


def parse_node_blocks(dat_file: Path):
    lines = dat_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    blocks = []
    current = None

    header_re = re.compile(
        r"(displacements|forces)\s*\([^)]*\)\s*for set\s+([A-Za-z0-9_]+).*time\s+([0-9.Ee+-]+)",
        re.IGNORECASE,
    )

    for raw in lines:
        line = raw.strip()
        lower = raw.lower()

        match = header_re.search(raw)
        if match:
            if current is not None:
                blocks.append(current)

            quantity = match.group(1).lower()
            nset = match.group(2).upper()
            time = float(match.group(3).replace("D", "E"))

            current = {
                "quantity": quantity,
                "nset": nset,
                "time": time,
                "rows": [],
            }
            continue

        if current is not None:
            if not line:
                continue

            if "step" in lower or "increment" in lower:
                continue

            parts = line.split()
            if len(parts) == 4:
                try:
                    nid = int(parts[0])
                    v1 = float(parts[1].replace("D", "E"))
                    v2 = float(parts[2].replace("D", "E"))
                    v3 = float(parts[3].replace("D", "E"))
                except ValueError:
                    continue

                current["rows"].append((nid, v1, v2, v3))

    if current is not None:
        blocks.append(current)

    return blocks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        default=DEFAULT_CASE_NAME,
        help="CalculiX case name without file extension.",
    )
    args = parser.parse_args()

    case_name = args.case
    label = short_case_label(case_name)

    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"
    dat_file = results_dir / f"{case_name}.dat"

    if not dat_file.exists():
        raise FileNotFoundError(dat_file)

    blocks = parse_node_blocks(dat_file)

    if not blocks:
        raise RuntimeError(f"No node print blocks found in {dat_file}")

    by_time = {}

    for block in blocks:
        t = block["time"]
        key = (block["quantity"], block["nset"])
        by_time.setdefault(t, {})[key] = block["rows"]

    rows_out = []

    for t in sorted(by_time):
        data = by_time[t]

        right_u = data.get(("displacements", "RIGHT_END"), [])
        right_rf = data.get(("forces", "RIGHT_END"), [])
        left_rf = data.get(("forces", "LEFT_END"), [])

        if not right_u:
            continue

        mean_u1_right = sum(row[1] for row in right_u) / len(right_u)

        sum_rf1_right = sum(row[1] for row in right_rf) if right_rf else 0.0
        sum_rf1_left = sum(row[1] for row in left_rf) if left_rf else 0.0

        tensile_force_from_left = -sum_rf1_left
        tensile_force_from_right = sum_rf1_right

        rows_out.append({
            "time": t,
            "mean_u1_right_mm": mean_u1_right,
            "sum_rf1_left_N": sum_rf1_left,
            "sum_rf1_right_N": sum_rf1_right,
            "tensile_force_from_left_N": tensile_force_from_left,
            "tensile_force_from_right_N": tensile_force_from_right,
            "right_u_node_count": len(right_u),
            "left_rf_node_count": len(left_rf),
            "right_rf_node_count": len(right_rf),
        })

    if not rows_out:
        raise RuntimeError("No usable force-displacement rows extracted.")

    csv_file = results_dir / f"{label}_force_displacement_curve.csv"
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)

    final = rows_out[-1]
    s0_mm2 = 25.0
    final_engineering_stress = final["tensile_force_from_left_N"] / s0_mm2

    summary = f"""Lab 007 — Force-Displacement Summary
====================================

Case:
{case_name}

Label:
{label}

Extracted increments:
{len(rows_out)}

Final step time:
{final["time"]:.6f}

Final mean right-end displacement:
{final["mean_u1_right_mm"]:.6f} mm

Final summed reaction force:
Left end RF1 sum:  {final["sum_rf1_left_N"]:.6f} N
Right end RF1 sum: {final["sum_rf1_right_N"]:.6f} N

Positive tensile force convention:
From left reaction:  {final["tensile_force_from_left_N"]:.6f} N
From right reaction: {final["tensile_force_from_right_N"]:.6f} N

Engineering stress estimate:
S0 = {s0_mm2:.6f} mm²
sigma_eng = {final_engineering_stress:.6f} MPa

Node counts:
Right displacement nodes: {final["right_u_node_count"]}
Left RF nodes:            {final["left_rf_node_count"]}
Right RF nodes:           {final["right_rf_node_count"]}

Files:
{csv_file}
"""

    summary_file = results_dir / f"{label}_force_displacement_summary.txt"
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
