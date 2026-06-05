#!/usr/bin/env python3
"""
Create an SVG force-displacement plot for Lab 006.

No external Python packages are required.
"""

from pathlib import Path
import csv
import math


SVG_WIDTH = 1400
SVG_HEIGHT = 800
MARGIN_LEFT = 125
MARGIN_RIGHT = 90
MARGIN_TOP = 135
MARGIN_BOTTOM = 115


def nice_ymax_kN(force_n: float) -> float:
    force_kn = force_n / 1000.0
    if force_kn <= 2:
        return 2.0
    if force_kn <= 5:
        return 5.0
    if force_kn <= 8:
        return 8.0
    if force_kn <= 10:
        return 10.0
    return math.ceil(force_kn / 5.0) * 5.0


def svg_text(x, y, text, size=18, weight="normal", anchor="start", color="#111111"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="{color}">{text}</text>'
    )


def main():
    lab_dir = Path(__file__).resolve().parents[1]
    csv_file = lab_dir / "results" / "force_displacement_curve.csv"
    out_file = lab_dir / "figures" / "force_displacement_curve.svg"

    rows = []
    with csv_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = float(row["mean_u1_right_mm"])
            force = float(row["tensile_force_from_left_N"])
            rows.append((u, force))

    if not rows:
        raise RuntimeError("No force-displacement rows found.")

    xmax = max(u for u, _f in rows)
    ymax_force = max(f for _u, f in rows)
    ymax_plot_n = nice_ymax_kN(ymax_force) * 1000.0

    plot_w = SVG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_h = SVG_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

    def map_x(u):
        return MARGIN_LEFT + (u / xmax) * plot_w

    def map_y(force_n):
        return MARGIN_TOP + plot_h - (force_n / ymax_plot_n) * plot_h

    points = " ".join(f"{map_x(u):.2f},{map_y(f):.2f}" for u, f in rows)

    final_u, final_f = rows[-1]
    final_stress = final_f / 25.0

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">')
    svg.append('<rect width="100%" height="100%" fill="#ffffff"/>')

    svg.append(svg_text(60, 52, "Lab 006 — C3D10 elastoplastic tensile specimen", size=30, weight="bold"))
    svg.append(svg_text(60, 86, "CalculiX 2.23 | EN ISO 6892-1 flat dogbone specimen | simplified steel material", size=18, color="#333333"))

    # Plot area
    svg.append(f'<rect x="{MARGIN_LEFT}" y="{MARGIN_TOP}" width="{plot_w}" height="{plot_h}" fill="#fbfbfb" stroke="#dddddd"/>')

    # Y grid and labels
    y_ticks_kn = [0, 2, 4, 6, 8] if ymax_plot_n <= 8000 else [i * ymax_plot_n / 5000 for i in range(6)]
    for tick_kn in y_ticks_kn:
        tick_n = tick_kn * 1000.0
        y = map_y(tick_n)
        svg.append(f'<line x1="{MARGIN_LEFT}" y1="{y:.2f}" x2="{MARGIN_LEFT + plot_w}" y2="{y:.2f}" stroke="#e6e6e6"/>')
        svg.append(svg_text(MARGIN_LEFT - 18, y + 5, f"{tick_kn:.1f}", size=15, anchor="end", color="#333333"))

    # X grid and labels
    x_ticks = [0.0, 0.5, 1.0, 1.5, 2.0]
    for tick in x_ticks:
        x = map_x(tick)
        svg.append(f'<line x1="{x:.2f}" y1="{MARGIN_TOP}" x2="{x:.2f}" y2="{MARGIN_TOP + plot_h}" stroke="#eeeeee"/>')
        svg.append(svg_text(x, MARGIN_TOP + plot_h + 34, f"{tick:.1f}", size=15, anchor="middle", color="#333333"))

    # Axes
    svg.append(f'<line x1="{MARGIN_LEFT}" y1="{MARGIN_TOP + plot_h}" x2="{MARGIN_LEFT + plot_w}" y2="{MARGIN_TOP + plot_h}" stroke="#111111" stroke-width="1.5"/>')
    svg.append(f'<line x1="{MARGIN_LEFT}" y1="{MARGIN_TOP}" x2="{MARGIN_LEFT}" y2="{MARGIN_TOP + plot_h}" stroke="#111111" stroke-width="1.5"/>')

    # Curve and points
    svg.append(f'<polyline points="{points}" fill="none" stroke="#1f5fbf" stroke-width="3.2"/>')

    for u, f in rows:
        svg.append(f'<circle cx="{map_x(u):.2f}" cy="{map_y(f):.2f}" r="3.2" fill="#1f5fbf"/>')

    # Final marker
    svg.append(f'<circle cx="{map_x(final_u):.2f}" cy="{map_y(final_f):.2f}" r="6.5" fill="#cc3333"/>')

    # Axis titles
    svg.append(svg_text(MARGIN_LEFT + plot_w / 2, SVG_HEIGHT - 42, "Right grip displacement Ux [mm]", size=19, anchor="middle"))
    svg.append(
        f'<text x="34" y="{MARGIN_TOP + plot_h / 2}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="19" fill="#111111" text-anchor="middle" '
        f'transform="rotate(-90 34 {MARGIN_TOP + plot_h / 2})">Tensile force [kN]</text>'
    )

    # Summary box
    box_w = 340
    box_h = 132
    box_x = MARGIN_LEFT + plot_w - box_w - 36
    box_y = MARGIN_TOP + 36

    svg.append(f'<rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="12" fill="#ffffff" stroke="#cfcfcf"/>')
    svg.append(svg_text(box_x + 22, box_y + 34, "Final result", size=17, weight="bold"))
    svg.append(svg_text(box_x + 22, box_y + 64, f"U = {final_u:.3f} mm", size=16, color="#333333"))
    svg.append(svg_text(box_x + 22, box_y + 91, f"F = {final_f/1000:.3f} kN", size=16, color="#333333"))
    svg.append(svg_text(box_x + 22, box_y + 118, f"σ_eng ≈ {final_stress:.1f} MPa", size=16, color="#333333"))

    # Footer note
    svg.append(svg_text(60, SVG_HEIGHT - 18, "Note: demonstration material law, not calibrated steel data.", size=14, color="#666666"))

    svg.append("</svg>")

    out_file.write_text("\n".join(svg), encoding="utf-8")

    print(f"Read: {csv_file}")
    print(f"Written: {out_file}")
    print(f"Points: {len(rows)}")
    print(f"Final displacement: {final_u:.6f} mm")
    print(f"Final force: {final_f:.6f} N")
    print(f"Final engineering stress: {final_stress:.6f} MPa")


if __name__ == "__main__":
    main()
