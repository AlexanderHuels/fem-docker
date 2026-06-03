#!/usr/bin/env python3
"""
Create a lightweight SVG convergence result card for Lab 002.

No external Python packages are required.
"""

from pathlib import Path
import csv


WIDTH = 1200
HEIGHT = 675


def svg_text(x, y, text, size=28, weight="normal", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="#111111">{text}</text>'
    )


def main() -> None:
    lab_dir = Path(__file__).resolve().parents[1]
    results_file = lab_dir / "results" / "convergence_results.csv"
    out_file = lab_dir / "figures" / "mesh_convergence_result_card.svg"

    with results_file.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    nx = [int(r["nx"]) for r in rows]
    u3 = [float(r["mean_abs_u3_mm"]) for r in rows]
    err_finest = [float(r["error_vs_finest_percent"]) for r in rows]
    analytical = float(rows[0]["analytical_tip_displacement_mm"])
    finest = u3[-1]

    # Plot area
    px0, py0 = 115, 525
    pw, ph = 690, 310

    xmin, xmax = min(nx), max(nx)
    ymin = min(u3) - 0.01
    ymax = max(u3) + 0.01

    def map_x(v):
        return px0 + (v - xmin) / (xmax - xmin) * pw

    def map_y(v):
        return py0 - (v - ymin) / (ymax - ymin) * ph

    points = [(map_x(x), map_y(y)) for x, y in zip(nx, u3)]
    analytical_y = map_y(analytical)

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    svg.append('<rect width="1200" height="675" fill="#ffffff"/>')

    # Header
    svg.append(svg_text(70, 85, "CalculiX 2.23 Docker FEM Lab", size=38, weight="bold"))
    svg.append(svg_text(70, 125, "Lab 002 — Mesh convergence study", size=25))

    # Left panel
    svg.append('<rect x="70" y="160" width="780" height="445" rx="18" fill="#f7f7f7" stroke="#d0d0d0"/>')
    svg.append(svg_text(105, 210, "Tip displacement convergence", size=28, weight="bold"))

    # Axes
    svg.append(f'<line x1="{px0}" y1="{py0}" x2="{px0+pw}" y2="{py0}" stroke="#222222" stroke-width="3"/>')
    svg.append(f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py0-ph}" stroke="#222222" stroke-width="3"/>')

    # Axis labels
    svg.append(svg_text(px0 + pw / 2, py0 + 55, "elements along length nx", size=22, anchor="middle"))
    svg.append(svg_text(px0 - 55, py0 - ph / 2, "|U3| [mm]", size=22, anchor="middle"))

    # Analytical reference line
    svg.append(f'<line x1="{px0}" y1="{analytical_y}" x2="{px0+pw}" y2="{analytical_y}" stroke="#666666" stroke-width="3" stroke-dasharray="10 8"/>')
    svg.append(svg_text(px0 + pw - 8, analytical_y - 10, f"analytical {analytical:.4f} mm", size=18, anchor="end"))

    # Data polyline
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    svg.append(f'<polyline points="{polyline}" fill="none" stroke="#111111" stroke-width="5"/>')

    # Points and labels
    for xval, yval, (sx, sy) in zip(nx, u3, points):
        svg.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="#111111"/>')
        svg.append(svg_text(sx, py0 + 28, str(xval), size=18, anchor="middle"))
        svg.append(svg_text(sx, sy - 14, f"{yval:.4f}", size=17, anchor="middle"))

    # Right panel
    svg.append('<rect x="880" y="160" width="250" height="445" rx="18" fill="#f7f7f7" stroke="#d0d0d0"/>')
    svg.append(svg_text(915, 210, "Key result", size=28, weight="bold"))

    svg.append(svg_text(915, 280, "Coarse mesh", size=21, weight="bold"))
    svg.append(svg_text(915, 315, f"nx=5: {u3[0]:.4f} mm", size=24))
    svg.append(svg_text(915, 345, f"{err_finest[0]:.2f} % vs finest", size=20))

    svg.append(svg_text(915, 415, "Finest mesh", size=21, weight="bold"))
    svg.append(svg_text(915, 450, f"nx=80: {finest:.4f} mm", size=24))

    svg.append(svg_text(915, 520, "Observation", size=21, weight="bold"))
    svg.append(svg_text(915, 552, "coarse mesh", size=20))
    svg.append(svg_text(915, 580, "is too stiff", size=20))

    # Footer
    svg.append(svg_text(70, 640, "Workflow: Python mesh variants → CCX Docker runs → .dat postprocessing → convergence table", size=22))

    svg.append("</svg>")

    out_file.write_text("\n".join(svg), encoding="utf-8")
    print(f"Written: {out_file}")


if __name__ == "__main__":
    main()
