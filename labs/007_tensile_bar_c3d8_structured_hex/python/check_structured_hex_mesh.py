#!/usr/bin/env python3
"""
Check generated structured C3D8 mesh.

Checks:
- all element corner orientation indicators
- edge lengths
- rough aspect ratios
"""

from pathlib import Path
import csv
import math


def dist(a, b):
    return math.sqrt(
        (a[0] - b[0]) ** 2
        + (a[1] - b[1]) ** 2
        + (a[2] - b[2]) ** 2
    )


def signed_hex_corner_volume(p1, p2, p4, p5):
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
    lab_dir = Path(__file__).resolve().parents[1]
    mesh_dir = lab_dir / "mesh"
    results_dir = lab_dir / "results"

    nodes_csv = mesh_dir / "structured_hex_nodes.csv"
    elems_csv = mesh_dir / "structured_hex_elements.csv"
    summary_file = results_dir / "structured_hex_mesh_quality_summary.txt"

    nodes = {}
    with nodes_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nid = int(row["nid"])
            nodes[nid] = (
                float(row["x_mm"]),
                float(row["y_mm"]),
                float(row["z_mm"]),
            )

    elements = []
    with elems_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = int(row["eid"])
            conn = tuple(int(row[f"n{i}"]) for i in range(1, 9))
            elements.append((eid, conn))

    edge_pairs = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]

    volume_indicators = []
    aspect_ratios = []
    min_edges = []
    max_edges = []

    negative = 0
    near_zero = 0
    worst_aspect = (0.0, None)
    min_volume = (float("inf"), None)
    max_volume = (-float("inf"), None)

    for eid, conn in elements:
        pts = [nodes[nid] for nid in conn]

        vol = signed_hex_corner_volume(pts[0], pts[1], pts[3], pts[4])
        volume_indicators.append(vol)

        if vol <= 0.0:
            negative += 1
        if abs(vol) < 1.0e-12:
            near_zero += 1

        if vol < min_volume[0]:
            min_volume = (vol, eid)
        if vol > max_volume[0]:
            max_volume = (vol, eid)

        edges = [dist(pts[i], pts[j]) for i, j in edge_pairs]
        e_min = min(edges)
        e_max = max(edges)
        ar = e_max / e_min if e_min > 0.0 else float("inf")

        min_edges.append(e_min)
        max_edges.append(e_max)
        aspect_ratios.append(ar)

        if ar > worst_aspect[0]:
            worst_aspect = (ar, eid)

    summary = f"""Lab 007 — Structured C3D8 Mesh Quality Check
============================================

Input:
{nodes_csv}
{elems_csv}

Counts:
- nodes: {len(nodes)}
- C3D8 elements: {len(elements)}

Orientation:
- negative or zero orientation indicators: {negative}
- near-zero orientation indicators: {near_zero}
- min signed corner volume indicator: {min_volume[0]:.12e} in element {min_volume[1]}
- max signed corner volume indicator: {max_volume[0]:.12e} in element {max_volume[1]}
- all strictly positive: {negative == 0}

Edge lengths:
- min edge length: {min(min_edges):.6f} mm
- max edge length: {max(max_edges):.6f} mm

Rough aspect ratio:
- max edge ratio: {max(aspect_ratios):.6f}
- worst aspect element: {worst_aspect[1]}

Assessment:
- orientation OK: {negative == 0}
- mesh size suitable for first C3D8 run: {len(elements) < 10000}

Output:
{summary_file}
"""

    summary_file.write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
