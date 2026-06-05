#!/usr/bin/env python3
"""
Create a visual SVG preview of the structured Lab 007 mesh concept.

Panels:
- top: XY mesh preview
- bottom: XZ mesh preview
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mesh_design import SpecimenGeometry, StructuredHexMeshDesign
from generate_structured_stations import build_x_stations, half_width_at_x, linspace


SVG_W = 1600
SVG_H = 1000

MARGIN_X = 80
MARGIN_Y = 60

TOP_PANEL_H = 520
BOTTOM_PANEL_H = 260

TOP_PANEL_W = 1440
BOTTOM_PANEL_W = 1440


def map_xy(x, y, x_min, x_max, y_min, y_max, ox, oy, w, h):
    px = ox + (x - x_min) / (x_max - x_min) * w
    py = oy + h - (y - y_min) / (y_max - y_min) * h
    return px, py


def polyline(points, stroke="#666", stroke_width=1.0, fill="none", opacity=1.0):
    pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
    return (
        f'<polyline points="{pts}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}" '
        f'fill="{fill}" opacity="{opacity}"/>'
    )


def line(x1, y1, x2, y2, stroke="#666", stroke_width=1.0, opacity=1.0):
    return (
        f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}" opacity="{opacity}"/>'
    )


def text(x, y, s, size=20, weight="normal", anchor="start", fill="#111"):
    return (
        f'<text x="{x:.3f}" y="{y:.3f}" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{s}</text>'
    )


def rect(x, y, w, h, stroke="#222", stroke_width=1.5, fill="none"):
    return (
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}" fill="{fill}"/>'
    )


def main():
    geom = SpecimenGeometry()
    mesh = StructuredHexMeshDesign()

    lab_dir = Path(__file__).resolve().parents[1]
    figures_dir = lab_dir / "figures"
    results_dir = lab_dir / "results"
    figures_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    x_values = build_x_stations(geom, mesh)
    eta_values = linspace(-1.0, 1.0, mesh.width_element_divisions + 1)
    z_values = linspace(
        -0.5 * geom.thickness_a0_mm,
        0.5 * geom.thickness_a0_mm,
        mesh.thickness_element_layers + 1,
    )

    x_min = min(x_values)
    x_max = max(x_values)
    y_min = -0.5 * geom.head_width_B_mm
    y_max = 0.5 * geom.head_width_B_mm
    z_min = min(z_values)
    z_max = max(z_values)

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">'
    )
    svg.append('<rect width="100%" height="100%" fill="white"/>')

    svg.append(text(80, 38, "Lab 007 — Structured C3D8 Hex Mesh Preview", size=28, weight="bold"))
    svg.append(text(80, 66, "Full dogbone specimen, symmetric mesh topology about x = 0, y = 0, z = 0", size=16, fill="#444"))

    # Panel frames
    top_x = MARGIN_X
    top_y = 100
    svg.append(rect(top_x, top_y, TOP_PANEL_W, TOP_PANEL_H, stroke="#999", stroke_width=1.2))

    bot_x = MARGIN_X
    bot_y = 690
    svg.append(rect(bot_x, bot_y, BOTTOM_PANEL_W, BOTTOM_PANEL_H, stroke="#999", stroke_width=1.2))

    svg.append(text(top_x + 10, top_y + 28, "XY view — structured mesh lines", size=20, weight="bold"))
    svg.append(text(bot_x + 10, bot_y + 28, "XZ view — four element layers through thickness", size=20, weight="bold"))

    # Drawing areas inside panels
    xy_ox = top_x + 40
    xy_oy = top_y + 50
    xy_w = TOP_PANEL_W - 80
    xy_h = TOP_PANEL_H - 90

    xz_ox = bot_x + 40
    xz_oy = bot_y + 50
    xz_w = BOTTOM_PANEL_W - 80
    xz_h = BOTTOM_PANEL_H - 90

    # XY outline
    top_outline = []
    bottom_outline = []
    for x in x_values:
        hw = half_width_at_x(x, geom)
        top_outline.append(map_xy(x, hw, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h))
        bottom_outline.append(map_xy(x, -hw, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h))

    svg.append(polyline(top_outline, stroke="#111", stroke_width=2.0))
    svg.append(polyline(bottom_outline, stroke="#111", stroke_width=2.0))

    # XY x-station lines
    for x in x_values:
        hw = half_width_at_x(x, geom)
        p1 = map_xy(x, -hw, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h)
        p2 = map_xy(x, hw, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h)
        stroke = "#2f6db2" if abs(x) < 1e-9 else "#8fb3da"
        sw = 1.5 if abs(x) < 1e-9 else 0.8
        svg.append(line(p1[0], p1[1], p2[0], p2[1], stroke=stroke, stroke_width=sw, opacity=0.95))

    # XY eta lines
    for eta in eta_values:
        pts = []
        for x in x_values:
            y = eta * half_width_at_x(x, geom)
            pts.append(map_xy(x, y, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h))
        stroke = "#c03a2b" if abs(eta) < 1e-12 else "#e3a29a"
        sw = 1.5 if abs(eta) < 1e-12 else 0.8
        svg.append(polyline(pts, stroke=stroke, stroke_width=sw, opacity=0.95))

    # XY center markers / labels
    x0a = map_xy(0.0, y_min, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h)
    x0b = map_xy(0.0, y_max, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h)
    y0a = map_xy(x_min, 0.0, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h)
    y0b = map_xy(x_max, 0.0, x_min, x_max, y_min, y_max, xy_ox, xy_oy, xy_w, xy_h)
    svg.append(line(x0a[0], x0a[1], x0b[0], x0b[1], stroke="#1d4f91", stroke_width=1.6, opacity=0.9))
    svg.append(line(y0a[0], y0a[1], y0b[0], y0b[1], stroke="#a93226", stroke_width=1.6, opacity=0.9))

    # XZ view
    # outer rectangle
    tl = map_xy(x_min, z_max, x_min, x_max, z_min, z_max, xz_ox, xz_oy, xz_w, xz_h)
    br = map_xy(x_max, z_min, x_min, x_max, z_min, z_max, xz_ox, xz_oy, xz_w, xz_h)
    svg.append(rect(tl[0], tl[1], br[0] - tl[0], br[1] - tl[1], stroke="#111", stroke_width=2.0))

    # x station lines in XZ
    for x in x_values:
        p1 = map_xy(x, z_min, x_min, x_max, z_min, z_max, xz_ox, xz_oy, xz_w, xz_h)
        p2 = map_xy(x, z_max, x_min, x_max, z_min, z_max, xz_ox, xz_oy, xz_w, xz_h)
        stroke = "#2f6db2" if abs(x) < 1e-9 else "#8fb3da"
        sw = 1.5 if abs(x) < 1e-9 else 0.8
        svg.append(line(p1[0], p1[1], p2[0], p2[1], stroke=stroke, stroke_width=sw, opacity=0.95))

    # z layers
    for z in z_values:
        p1 = map_xy(x_min, z, x_min, x_max, z_min, z_max, xz_ox, xz_oy, xz_w, xz_h)
        p2 = map_xy(x_max, z, x_min, x_max, z_min, z_max, xz_ox, xz_oy, xz_w, xz_h)
        stroke = "#2ca25f" if abs(z) < 1e-12 else "#9adbb8"
        sw = 1.6 if abs(z) < 1e-12 else 1.0
        svg.append(line(p1[0], p1[1], p2[0], p2[1], stroke=stroke, stroke_width=sw, opacity=0.95))

    # footer notes
    info_x = 1525
    info_y = 160
    notes = [
        f"x stations: {len(x_values)}",
        f"x divisions: {len(x_values) - 1}",
        f"width divisions: {len(eta_values) - 1}",
        f"thickness layers: {len(z_values) - 1}",
        f"expected C3D8: {(len(x_values) - 1) * (len(eta_values) - 1) * (len(z_values) - 1)}",
        "",
        "Blue: x station lines",
        "Red: width/eta lines",
        "Green: thickness planes",
    ]
    for i, s in enumerate(notes):
        svg.append(text(info_x, info_y + i * 24, s, size=16, fill="#333"))

    out_file = figures_dir / "structured_hex_mesh_preview.svg"
    svg.append("</svg>")
    out_file.write_text("\n".join(svg), encoding="utf-8")

    summary = f"""Lab 007 — Structured Mesh Preview SVG
=====================================

Output:
{out_file}

Preview content:
- XY view with structured mesh lines
- XZ view with 4 thickness layers

Counts:
- x stations: {len(x_values)}
- width stations: {len(eta_values)}
- z stations: {len(z_values)}
- expected C3D8 elements: {(len(x_values) - 1) * (len(eta_values) - 1) * (len(z_values) - 1)}
"""
    summary_file = results_dir / "structured_hex_mesh_preview_summary.txt"
    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
