#!/usr/bin/env python3
"""
Lab 007 structured C3D8 mesh design parameters.

This file only defines and checks the structured mesh design.
It does not generate the mesh yet.
"""

from dataclasses import dataclass
from pathlib import Path
import csv


@dataclass(frozen=True)
class SpecimenGeometry:
    thickness_a0_mm: float = 2.0
    width_b0_mm: float = 12.5
    gauge_length_L0_mm: float = 50.0
    parallel_length_Lc_mm: float = 75.0
    head_width_B_mm: float = 25.0
    transition_length_mm: float = 35.0
    grip_length_mm: float = 35.0

    @property
    def total_length_Lt_mm(self) -> float:
        return (
            self.parallel_length_Lc_mm
            + 2.0 * self.transition_length_mm
            + 2.0 * self.grip_length_mm
        )

    @property
    def half_length_mm(self) -> float:
        return 0.5 * self.total_length_Lt_mm

    @property
    def half_parallel_length_mm(self) -> float:
        return 0.5 * self.parallel_length_Lc_mm

    @property
    def reduced_area_S0_mm2(self) -> float:
        return self.thickness_a0_mm * self.width_b0_mm


@dataclass(frozen=True)
class StructuredHexMeshDesign:
    thickness_element_layers: int = 4
    width_element_divisions: int = 12

    parallel_x_divisions_total: int = 40
    transition_x_divisions_per_side: int = 20
    grip_x_divisions_per_side: int = 14

    @property
    def thickness_node_planes(self) -> int:
        return self.thickness_element_layers + 1

    @property
    def total_x_divisions(self) -> int:
        return (
            self.parallel_x_divisions_total
            + 2 * self.transition_x_divisions_per_side
            + 2 * self.grip_x_divisions_per_side
        )

    @property
    def estimated_hex_elements(self) -> int:
        return (
            self.total_x_divisions
            * self.width_element_divisions
            * self.thickness_element_layers
        )

    @property
    def estimated_nodes(self) -> int:
        return (
            (self.total_x_divisions + 1)
            * (self.width_element_divisions + 1)
            * (self.thickness_element_layers + 1)
        )


def main():
    geom = SpecimenGeometry()
    mesh = StructuredHexMeshDesign()

    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"
    results_dir.mkdir(exist_ok=True)

    checks = {
        "x_midplane_present": mesh.parallel_x_divisions_total % 2 == 0,
        "y_centerline_present": mesh.width_element_divisions % 2 == 0,
        "z_midplane_present": mesh.thickness_element_layers % 2 == 0,
        "thickness_node_planes_is_5": mesh.thickness_node_planes == 5,
    }

    rows = [
        ("thickness_a0_mm", geom.thickness_a0_mm),
        ("width_b0_mm", geom.width_b0_mm),
        ("gauge_length_L0_mm", geom.gauge_length_L0_mm),
        ("parallel_length_Lc_mm", geom.parallel_length_Lc_mm),
        ("head_width_B_mm", geom.head_width_B_mm),
        ("transition_length_mm", geom.transition_length_mm),
        ("grip_length_mm", geom.grip_length_mm),
        ("total_length_Lt_mm", geom.total_length_Lt_mm),
        ("reduced_area_S0_mm2", geom.reduced_area_S0_mm2),
        ("thickness_element_layers", mesh.thickness_element_layers),
        ("thickness_node_planes", mesh.thickness_node_planes),
        ("width_element_divisions", mesh.width_element_divisions),
        ("parallel_x_divisions_total", mesh.parallel_x_divisions_total),
        ("transition_x_divisions_per_side", mesh.transition_x_divisions_per_side),
        ("grip_x_divisions_per_side", mesh.grip_x_divisions_per_side),
        ("total_x_divisions", mesh.total_x_divisions),
        ("estimated_c3d8_elements", mesh.estimated_hex_elements),
        ("estimated_nodes", mesh.estimated_nodes),
    ]

    csv_file = results_dir / "structured_hex_mesh_design.csv"
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "value"])
        writer.writerows(rows)

    summary = f"""Lab 007 — Structured C3D8 Mesh Design
=====================================

Specimen geometry:
- thickness a0: {geom.thickness_a0_mm:.3f} mm
- reduced width b0: {geom.width_b0_mm:.3f} mm
- gauge length L0: {geom.gauge_length_L0_mm:.3f} mm
- parallel length Lc: {geom.parallel_length_Lc_mm:.3f} mm
- head width B: {geom.head_width_B_mm:.3f} mm
- transition length per side: {geom.transition_length_mm:.3f} mm
- grip length per side: {geom.grip_length_mm:.3f} mm
- total length Lt: {geom.total_length_Lt_mm:.3f} mm
- reduced area S0: {geom.reduced_area_S0_mm2:.3f} mm²

Structured C3D8 mesh design:
- thickness element layers: {mesh.thickness_element_layers}
- thickness node planes: {mesh.thickness_node_planes}
- width element divisions: {mesh.width_element_divisions}
- parallel x divisions total: {mesh.parallel_x_divisions_total}
- transition x divisions per side: {mesh.transition_x_divisions_per_side}
- grip x divisions per side: {mesh.grip_x_divisions_per_side}
- total x divisions: {mesh.total_x_divisions}

Estimated mesh size:
- C3D8 elements: {mesh.estimated_hex_elements}
- nodes: {mesh.estimated_nodes}

Symmetry checks:
- x = 0 station present: {checks["x_midplane_present"]}
- y = 0 centerline present: {checks["y_centerline_present"]}
- z = 0 mid-thickness plane present: {checks["z_midplane_present"]}
- five thickness node planes: {checks["thickness_node_planes_is_5"]}

Output:
{csv_file}
"""

    summary_file = results_dir / "structured_hex_mesh_design_summary.txt"
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
