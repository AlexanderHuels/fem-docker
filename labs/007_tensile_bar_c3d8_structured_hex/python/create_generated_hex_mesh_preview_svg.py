#!/usr/bin/env python3
"""
Create SVG preview from the actually generated structured C3D8 mesh nodes.

Panels:
- XY view at z = 0
- XZ view at y = 0
- YZ section at x = 0
"""

from pathlib import Path
import csv


SVG_W = 1600
SVG_H = 1150

# Display-only exaggeration factors.
# The actual mesh coordinates are not changed.
XZ_Z_EXAGGERATION = 6.0
YZ_Z_EXAGGERATION = 1.0


def read_nodes(nodes_csv):
    nodes = []
    with nodes_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodes.append(
                {
                    "nid": int(row["nid"]),
                    "x": float(row["x_mm"]),
                    "y": float(row["y_mm"]),
                    "z": float(row["z_mm"]),
                    "ix": int(row["ix"]),
                    "iy": int(row["iy"]),
                    "iz": int(row["iz"]),
                }
            )
    return nodes


def map_point(a, b, a_min, a_max, b_min, b_max, ox, oy, w, h):
    px = ox + (a - a_min) / (a_max - a_min) * w
    py = oy + h - (b - b_min) / (b_max - b_min) * h
    return px, py

def map_equal_aspect(a, b, a_min, a_max, b_min, b_max, ox, oy, w, h):
    """Map with equal visual scale for a and b axes, centered in panel."""
    a_range = a_max - a_min
    b_range = b_max - b_min
    scale = min(w / a_range, h / b_range)

    used_w = a_range * scale
    used_h = b_range * scale

    x0 = ox + 0.5 * (w - used_w)
    y0 = oy + 0.5 * (h - used_h)

    px = x0 + (a - a_min) * scale
    py = y0 + used_h - (b - b_min) * scale
    return px, py


def svg_line(p1, p2, stroke="#777", width=1.0, opacity=1.0):
    return (
        f'<line x1="{p1[0]:.3f}" y1="{p1[1]:.3f}" '
        f'x2="{p2[0]:.3f}" y2="{p2[1]:.3f}" '
        f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>'
    )


def svg_polyline(points, stroke="#777", width=1.0, opacity=1.0):
    pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
    return (
        f'<polyline points="{pts}" fill="none" '
        f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>'
    )


def svg_text(x, y, text, size=18, weight="normal", fill="#111"):
    return (
        f'<text x="{x:.3f}" y="{y:.3f}" '
        f'font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{text}</text>'
    )


def svg_rect(x, y, w, h, stroke="#999", fill="none", width=1.2):
    return (
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
        f'stroke="{stroke}" stroke-width="{width}" fill="{fill}"/>'
    )


def main():
    lab_dir = Path(__file__).resolve().parents[1]
    mesh_dir = lab_dir / "mesh"
    figures_dir = lab_dir / "figures"
    results_dir = lab_dir / "results"
    figures_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    nodes_csv = mesh_dir / "structured_hex_nodes.csv"
    out_svg = figures_dir / "generated_structured_hex_mesh_preview.svg"
    summary_file = results_dir / "generated_structured_hex_mesh_preview_summary.txt"

    nodes = read_nodes(nodes_csv)

    ix_values = sorted({n["ix"] for n in nodes})
    iy_values = sorted({n["iy"] for n in nodes})
    iz_values = sorted({n["iz"] for n in nodes})

    ix_mid = ix_values[len(ix_values) // 2]
    iy_mid = iy_values[len(iy_values) // 2]
    iz_mid = iz_values[len(iz_values) // 2]

    by_index = {(n["ix"], n["iy"], n["iz"]): n for n in nodes}

    x_min = min(n["x"] for n in nodes)
    x_max = max(n["x"] for n in nodes)
    y_min = min(n["y"] for n in nodes)
    y_max = max(n["y"] for n in nodes)
    z_min = min(n["z"] for n in nodes)
    z_max = max(n["z"] for n in nodes)

    # Display-only z ranges for sections.
    z_mid = 0.5 * (z_min + z_max)
    z_half = 0.5 * (z_max - z_min)
    z_xz_min = z_mid - XZ_Z_EXAGGERATION * z_half
    z_xz_max = z_mid + XZ_Z_EXAGGERATION * z_half
    z_yz_min = z_mid - YZ_Z_EXAGGERATION * z_half
    z_yz_max = z_mid + YZ_Z_EXAGGERATION * z_half

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">')
    svg.append('<rect width="100%" height="100%" fill="white"/>')

    svg.append(svg_text(70, 38, "Lab 007 — Generated Structured C3D8 Mesh Preview", size=28, weight="bold"))
    svg.append(svg_text(70, 66, "Preview generated from structured_hex_nodes.csv", size=16, fill="#444"))

    # Panels
    xy = dict(ox=70, oy=100, w=1460, h=470)
    xz = dict(ox=70, oy=640, w=980, h=210)
    yz = dict(ox=1150, oy=640, w=320, h=320)

    svg.append(svg_rect(xy["ox"], xy["oy"], xy["w"], xy["h"]))
    svg.append(svg_rect(xz["ox"], xz["oy"], xz["w"], xz["h"]))
    svg.append(svg_rect(yz["ox"], yz["oy"], yz["w"], yz["h"]))

    svg.append(svg_text(xy["ox"] + 10, xy["oy"] + 28, "XY view at z = 0", size=20, weight="bold"))
    svg.append(svg_text(xz["ox"] + 10, xz["oy"] + 28, f"XZ view at y = 0, z display x{XZ_Z_EXAGGERATION:g}", size=20, weight="bold"))
    svg.append(svg_text(yz["ox"] + 10, yz["oy"] + 28, "YZ section at x = 0, true aspect", size=20, weight="bold"))

    # Inner drawing areas
    xy_inner = dict(ox=xy["ox"] + 40, oy=xy["oy"] + 55, w=xy["w"] - 80, h=xy["h"] - 90)
    xz_inner = dict(ox=xz["ox"] + 40, oy=xz["oy"] + 55, w=xz["w"] - 80, h=xz["h"] - 90)
    yz_inner = dict(ox=yz["ox"] + 40, oy=yz["oy"] + 55, w=yz["w"] - 80, h=yz["h"] - 90)

    # XY grid at z mid
    for ix in ix_values:
        pts = []
        for iy in iy_values:
            n = by_index[(ix, iy, iz_mid)]
            pts.append(map_point(n["x"], n["y"], x_min, x_max, y_min, y_max, **xy_inner))
        stroke = "#2f6db2" if ix == ix_mid else "#9bbbe0"
        width = 1.5 if ix == ix_mid else 0.75
        svg.append(svg_polyline(pts, stroke=stroke, width=width, opacity=0.95))

    for iy in iy_values:
        pts = []
        for ix in ix_values:
            n = by_index[(ix, iy, iz_mid)]
            pts.append(map_point(n["x"], n["y"], x_min, x_max, y_min, y_max, **xy_inner))
        stroke = "#c0392b" if iy == iy_mid else "#e5a6a0"
        width = 1.5 if iy == iy_mid else 0.75
        svg.append(svg_polyline(pts, stroke=stroke, width=width, opacity=0.95))

    # XZ grid at y mid
    for ix in ix_values:
        pts = []
        for iz in iz_values:
            n = by_index[(ix, iy_mid, iz)]
            pts.append(map_point(n["x"], n["z"], x_min, x_max, z_xz_min, z_xz_max, **xz_inner))
        stroke = "#2f6db2" if ix == ix_mid else "#9bbbe0"
        width = 1.5 if ix == ix_mid else 0.75
        svg.append(svg_polyline(pts, stroke=stroke, width=width, opacity=0.95))

    for iz in iz_values:
        pts = []
        for ix in ix_values:
            n = by_index[(ix, iy_mid, iz)]
            pts.append(map_point(n["x"], n["z"], x_min, x_max, z_xz_min, z_xz_max, **xz_inner))
        stroke = "#2ca25f" if iz == iz_mid else "#9adbb8"
        width = 1.6 if iz == iz_mid else 1.0
        svg.append(svg_polyline(pts, stroke=stroke, width=width, opacity=0.95))

    # YZ grid at x mid
    for iy in iy_values:
        pts = []
        for iz in iz_values:
            n = by_index[(ix_mid, iy, iz)]
            pts.append(map_equal_aspect(n["y"], n["z"], y_min, y_max, z_yz_min, z_yz_max, **yz_inner))
        stroke = "#c0392b" if iy == iy_mid else "#e5a6a0"
        width = 1.5 if iy == iy_mid else 0.8
        svg.append(svg_polyline(pts, stroke=stroke, width=width, opacity=0.95))

    for iz in iz_values:
        pts = []
        for iy in iy_values:
            n = by_index[(ix_mid, iy, iz)]
            pts.append(map_equal_aspect(n["y"], n["z"], y_min, y_max, z_yz_min, z_yz_max, **yz_inner))
        stroke = "#2ca25f" if iz == iz_mid else "#9adbb8"
        width = 1.6 if iz == iz_mid else 1.0
        svg.append(svg_polyline(pts, stroke=stroke, width=width, opacity=0.95))

    # Notes
    notes = [
        f"Nodes: {len(nodes)}",
        f"x stations: {len(ix_values)}",
        f"width stations: {len(iy_values)}",
        f"z stations: {len(iz_values)}",
        "Blue: x-station lines",
        "Red: width lines",
        "Green: thickness planes",
        f"XZ z display x{XZ_Z_EXAGGERATION:g}",
        "YZ true physical aspect",
    ]
    for i, item in enumerate(notes):
        svg.append(svg_text(70, 910 + 26 * i, item, size=17, fill="#333"))

    svg.append("</svg>")
    out_svg.write_text("\n".join(svg), encoding="utf-8")

    summary = f"""Lab 007 — Generated Structured Hex Mesh Preview
================================================

Input:
{nodes_csv}

Output:
{out_svg}

Views:
- XY at z-index {iz_mid}
- XZ at y-index {iy_mid}
- YZ at x-index {ix_mid}

Counts:
- nodes: {len(nodes)}
- x stations: {len(ix_values)}
- width stations: {len(iy_values)}
- z stations: {len(iz_values)}

Display scaling:
- XZ z exaggeration: {XZ_Z_EXAGGERATION}
- YZ z exaggeration: {YZ_Z_EXAGGERATION}
"""
    summary_file.write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
