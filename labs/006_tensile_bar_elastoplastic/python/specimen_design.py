#!/usr/bin/env python3
"""
Design definition for Lab 006.

The current values are fixed defaults, but the file is intentionally structured
so that the geometry can later be parameterized.
"""

from dataclasses import dataclass
from pathlib import Path
import csv
import math


@dataclass(frozen=True)
class SpecimenGeometry:
    # EN ISO 6892-1:2019 Annex B, form 1
    thickness_a0_mm: float = 2.0
    width_b0_mm: float = 12.5
    gauge_length_L0_mm: float = 50.0
    parallel_length_Lc_mm: float = 75.0

    # FEM modelling choices for dogbone heads / transition
    head_width_B_mm: float = 25.0
    min_transition_radius_mm: float = 30.0
    transition_length_mm: float = 35.0
    grip_length_mm: float = 35.0


@dataclass(frozen=True)
class MaterialEstimate:
    yield_stress_MPa: float = 250.0


def smoothstep_min_radius(delta_y: float, length: float, samples: int = 20001) -> float:
    """
    Estimate minimum curvature radius for a smoothstep transition.

    Transition:
        y(t) = delta_y * (6 t^5 - 15 t^4 + 10 t^3), t in [0, 1]

    This is used only as a design check for the planned dogbone contour.
    """
    max_curvature = 0.0

    for i in range(samples):
        t = i / (samples - 1)

        dy_dt = 30.0 * t**4 - 60.0 * t**3 + 30.0 * t**2
        d2y_dt2 = 120.0 * t**3 - 180.0 * t**2 + 60.0 * t

        dy_dx = delta_y / length * dy_dt
        d2y_dx2 = delta_y / (length * length) * d2y_dt2

        curvature = abs(d2y_dx2) / ((1.0 + dy_dx * dy_dx) ** 1.5)
        max_curvature = max(max_curvature, curvature)

    if max_curvature <= 0.0:
        return math.inf

    return 1.0 / max_curvature


def main() -> None:
    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"
    results_dir.mkdir(exist_ok=True)

    geom = SpecimenGeometry()
    mat = MaterialEstimate()

    half_width_delta = 0.5 * (geom.head_width_B_mm - geom.width_b0_mm)

    reduced_area_S0_mm2 = geom.thickness_a0_mm * geom.width_b0_mm
    yield_force_N = mat.yield_stress_MPa * reduced_area_S0_mm2

    free_contour_length_mm = (
        geom.parallel_length_Lc_mm
        + 2.0 * geom.transition_length_mm
    )

    total_length_Lt_mm = (
        geom.parallel_length_Lc_mm
        + 2.0 * geom.transition_length_mm
        + 2.0 * geom.grip_length_mm
    )

    estimated_transition_radius_mm = smoothstep_min_radius(
        delta_y=half_width_delta,
        length=geom.transition_length_mm,
    )

    rows = [
        ("thickness_a0_mm", geom.thickness_a0_mm, "mm"),
        ("width_b0_mm", geom.width_b0_mm, "mm"),
        ("gauge_length_L0_mm", geom.gauge_length_L0_mm, "mm"),
        ("parallel_length_Lc_mm", geom.parallel_length_Lc_mm, "mm"),
        ("head_width_B_mm", geom.head_width_B_mm, "mm"),
        ("min_transition_radius_mm", geom.min_transition_radius_mm, "mm"),
        ("transition_length_mm", geom.transition_length_mm, "mm"),
        ("grip_length_mm", geom.grip_length_mm, "mm"),
        ("reduced_area_S0_mm2", reduced_area_S0_mm2, "mm^2"),
        ("free_contour_length_mm", free_contour_length_mm, "mm"),
        ("total_length_Lt_mm", total_length_Lt_mm, "mm"),
        ("yield_stress_MPa", mat.yield_stress_MPa, "MPa"),
        ("yield_force_estimate_N", yield_force_N, "N"),
        ("estimated_transition_radius_mm", estimated_transition_radius_mm, "mm"),
    ]

    csv_file = results_dir / "specimen_geometry_parameters.csv"
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "value", "unit"])
        writer.writerows(rows)

    summary_file = results_dir / "specimen_geometry_summary.txt"
    summary = f"""Lab 006 — Tensile Specimen Geometry Design
==========================================

Selected specimen:
- Flat dogbone specimen
- EN ISO 6892-1:2019 Annex B, specimen form 1
- Thickness a0: {geom.thickness_a0_mm:.3f} mm
- Width b0: {geom.width_b0_mm:.3f} mm
- Gauge length L0: {geom.gauge_length_L0_mm:.3f} mm
- Parallel length Lc: {geom.parallel_length_Lc_mm:.3f} mm

FEM modelling choices:
- Head width B: {geom.head_width_B_mm:.3f} mm
- Minimum transition radius target: {geom.min_transition_radius_mm:.3f} mm
- Transition length per side: {geom.transition_length_mm:.3f} mm
- Grip length per side: {geom.grip_length_mm:.3f} mm
- Total model length Lt: {total_length_Lt_mm:.3f} mm

Checks:
- B >= 1.2 * b0: {geom.head_width_B_mm:.3f} >= {1.2 * geom.width_b0_mm:.3f} mm
- Estimated smooth transition radius: {estimated_transition_radius_mm:.3f} mm
- Radius target fulfilled: {estimated_transition_radius_mm >= geom.min_transition_radius_mm}

First-order estimate:
- Reduced area S0: {reduced_area_S0_mm2:.3f} mm²
- Yield stress estimate: {mat.yield_stress_MPa:.3f} MPa
- Yield force estimate: {yield_force_N:.3f} N
"""

    summary_file.write_text(summary, encoding="utf-8")

    print(summary)
    print(f"Written: {csv_file}")
    print(f"Written: {summary_file}")


if __name__ == "__main__":
    main()
