#!/usr/bin/env python3
"""
Generate structured x/y/z stations for Lab 007.

This script does not generate C3D8 elements yet.
It only defines the structured station layout and checks symmetry.
"""

from pathlib import Path
import csv
import math
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mesh_design import SpecimenGeometry, StructuredHexMeshDesign


def linspace(a, b, n_points):
    if n_points < 2:
        raise ValueError("n_points must be >= 2")
    step = (b - a) / (n_points - 1)
    return [a + i * step for i in range(n_points)]


def smoothstep(t):
    """Cubic smooth transition from 0 to 1."""
    return 3.0 * t * t - 2.0 * t * t * t


def half_width_at_x(x, geom: SpecimenGeometry):
    """
    Smooth dogbone half-width as function of x.

    Zones:
    - parallel reduced section: constant b0 / 2
    - grip/head section: constant B / 2
    - transition: smooth cubic interpolation
    """
    ax = abs(x)

    half_b0 = 0.5 * geom.width_b0_mm
    half_B = 0.5 * geom.head_width_B_mm

    x_parallel_end = 0.5 * geom.parallel_length_Lc_mm
    x_transition_end = x_parallel_end + geom.transition_length_mm

    if ax <= x_parallel_end:
        return half_b0

    if ax >= x_transition_end:
        return half_B

    t = (ax - x_parallel_end) / geom.transition_length_mm
    return half_b0 + (half_B - half_b0) * smoothstep(t)


def zone_at_x(x, geom: SpecimenGeometry):
    ax = abs(x)
    x_parallel_end = 0.5 * geom.parallel_length_Lc_mm
    x_transition_end = x_parallel_end + geom.transition_length_mm

    if ax <= x_parallel_end:
        return "parallel"
    if ax <= x_transition_end:
        return "transition"
    return "grip"


def build_x_stations(geom: SpecimenGeometry, mesh: StructuredHexMeshDesign):
    x_left = -geom.half_length_mm
    x_right = geom.half_length_mm

    x_left_grip_end = -0.5 * geom.parallel_length_Lc_mm - geom.transition_length_mm
    x_left_parallel_start = -0.5 * geom.parallel_length_Lc_mm
    x_right_parallel_end = 0.5 * geom.parallel_length_Lc_mm
    x_right_grip_start = 0.5 * geom.parallel_length_Lc_mm + geom.transition_length_mm

    segments = []

    # Left grip
    segments.append(
        linspace(
            x_left,
            x_left_grip_end,
            mesh.grip_x_divisions_per_side + 1,
        )
    )

    # Left transition
    segments.append(
        linspace(
            x_left_grip_end,
            x_left_parallel_start,
            mesh.transition_x_divisions_per_side + 1,
        )[1:]
    )

    # Parallel section
    segments.append(
        linspace(
            x_left_parallel_start,
            x_right_parallel_end,
            mesh.parallel_x_divisions_total + 1,
        )[1:]
    )

    # Right transition
    segments.append(
        linspace(
            x_right_parallel_end,
            x_right_grip_start,
            mesh.transition_x_divisions_per_side + 1,
        )[1:]
    )

    # Right grip
    segments.append(
        linspace(
            x_right_grip_start,
            x_right,
            mesh.grip_x_divisions_per_side + 1,
        )[1:]
    )

    x_values = [x for segment in segments for x in segment]
    return x_values


def main():
    geom = SpecimenGeometry()
    mesh = StructuredHexMeshDesign()

    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"
    results_dir.mkdir(exist_ok=True)

    x_values = build_x_stations(geom, mesh)

    eta_values = linspace(-1.0, 1.0, mesh.width_element_divisions + 1)
    z_values = linspace(
        -0.5 * geom.thickness_a0_mm,
        0.5 * geom.thickness_a0_mm,
        mesh.thickness_element_layers + 1,
    )

    # Symmetry and mid-plane checks
    checks = {
        "x_count": len(x_values),
        "eta_count": len(eta_values),
        "z_count": len(z_values),
        "x_min": min(x_values),
        "x_max": max(x_values),
        "z_min": min(z_values),
        "z_max": max(z_values),
        "x_zero_present": any(abs(x) < 1.0e-9 for x in x_values),
        "eta_zero_present": any(abs(e) < 1.0e-12 for e in eta_values),
        "z_zero_present": any(abs(z) < 1.0e-12 for z in z_values),
        "x_symmetric": all(
            abs(x_values[i] + x_values[-1 - i]) < 1.0e-9
            for i in range(len(x_values))
        ),
        "eta_symmetric": all(
            abs(eta_values[i] + eta_values[-1 - i]) < 1.0e-12
            for i in range(len(eta_values))
        ),
        "z_symmetric": all(
            abs(z_values[i] + z_values[-1 - i]) < 1.0e-12
            for i in range(len(z_values))
        ),
    }

    x_csv = results_dir / "structured_hex_x_stations.csv"
    with x_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["i", "x_mm", "half_width_mm", "full_width_mm", "zone"])
        for i, x in enumerate(x_values):
            hw = half_width_at_x(x, geom)
            writer.writerow([i, f"{x:.9f}", f"{hw:.9f}", f"{2.0 * hw:.9f}", zone_at_x(x, geom)])

    yz_csv = results_dir / "structured_hex_yz_reference_stations.csv"
    with yz_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["eta_index", "eta", "z_index", "z_mm"])
        for j, eta in enumerate(eta_values):
            for k, z in enumerate(z_values):
                writer.writerow([j, f"{eta:.9f}", k, f"{z:.9f}"])

    summary = f"""Lab 007 — Structured Station Generation
=======================================

Specimen:
- total length Lt: {geom.total_length_Lt_mm:.3f} mm
- half length: {geom.half_length_mm:.3f} mm
- reduced width b0: {geom.width_b0_mm:.3f} mm
- head width B: {geom.head_width_B_mm:.3f} mm
- thickness a0: {geom.thickness_a0_mm:.3f} mm

Station counts:
- x stations: {len(x_values)}
- x element divisions: {len(x_values) - 1}
- eta stations over width: {len(eta_values)}
- width element divisions: {len(eta_values) - 1}
- z stations: {len(z_values)}
- thickness element layers: {len(z_values) - 1}

Expected C3D8 element count:
{(len(x_values) - 1) * (len(eta_values) - 1) * (len(z_values) - 1)}

Symmetry checks:
- x = 0 station present: {checks["x_zero_present"]}
- eta = 0 station present: {checks["eta_zero_present"]}
- z = 0 station present: {checks["z_zero_present"]}
- x stations symmetric: {checks["x_symmetric"]}
- eta stations symmetric: {checks["eta_symmetric"]}
- z stations symmetric: {checks["z_symmetric"]}

Bounds:
- x: {min(x_values):.6f} ... {max(x_values):.6f} mm
- z: {min(z_values):.6f} ... {max(z_values):.6f} mm

Selected width checks:
- half width at x = 0: {half_width_at_x(0.0, geom):.6f} mm
- full width at x = 0: {2.0 * half_width_at_x(0.0, geom):.6f} mm
- half width at grip end: {half_width_at_x(geom.half_length_mm, geom):.6f} mm
- full width at grip end: {2.0 * half_width_at_x(geom.half_length_mm, geom):.6f} mm

Output files:
{x_csv}
{yz_csv}
"""

    summary_file = results_dir / "structured_hex_station_summary.txt"
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
