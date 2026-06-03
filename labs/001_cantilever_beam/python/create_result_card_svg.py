#!/usr/bin/env python3
"""
Create a lightweight SVG result card for Lab 001.

No external Python packages are required.
"""

from pathlib import Path


WIDTH = 1200
HEIGHT = 675

analytical = 2.816901
ccx = 2.830381
error = 0.479


def svg_text(x, y, text, size=28, weight="normal", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="#111111">{text}</text>'
    )


def main() -> None:
    lab_dir = Path(__file__).resolve().parents[1]
    out_file = lab_dir / "figures" / "cantilever_shell_static_result_card.svg"

    # Beam sketch coordinates
    x0, y0 = 120, 370
    beam_len = 620
    beam_h = 70
    x1 = x0 + beam_len

    # Deformed centerline: simple visual approximation, not the FEM mesh
    curve = [
        (x0, y0),
        (x0 + 120, y0 + 5),
        (x0 + 260, y0 + 23),
        (x0 + 420, y0 + 55),
        (x1, y0 + 95),
    ]

    curve_path = "M " + " C ".join(
        [
            f"{curve[0][0]} {curve[0][1]}",
            f"{curve[1][0]} {curve[1][1]}, {curve[2][0]} {curve[2][1]}, {curve[3][0]} {curve[3][1]}",
            f"{curve[3][0]} {curve[3][1]}, {curve[4][0]-80} {curve[4][1]-5}, {curve[4][0]} {curve[4][1]}",
        ]
    )

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    svg.append('<rect width="1200" height="675" fill="#ffffff"/>')

    # Header
    svg.append(svg_text(70, 85, "CalculiX 2.23 Docker FEM Lab", size=38, weight="bold"))
    svg.append(svg_text(70, 125, "Lab 001 — Cantilever shell benchmark", size=25))

    # Model sketch panel
    svg.append('<rect x="70" y="170" width="720" height="410" rx="18" fill="#f7f7f7" stroke="#d0d0d0"/>')
    svg.append(svg_text(105, 220, "Model", size=28, weight="bold"))

    # Fixed wall
    svg.append('<rect x="95" y="285" width="25" height="185" fill="#444444"/>')
    for yy in range(295, 470, 24):
        svg.append(f'<line x1="95" y1="{yy}" x2="70" y2="{yy+18}" stroke="#444444" stroke-width="3"/>')

    # Undeformed beam
    svg.append(f'<rect x="{x0}" y="{y0 - beam_h/2}" width="{beam_len}" height="{beam_h}" fill="none" stroke="#222222" stroke-width="4"/>')
    svg.append(svg_text(x0 + beam_len / 2, y0 - 65, "L = 1000 mm", size=22, anchor="middle"))
    svg.append(svg_text(x0 + 20, y0 + 70, "clamped", size=20))
    svg.append(svg_text(x1 - 30, y0 + 70, "F = 1000 N", size=20, anchor="end"))

    # Load arrows
    for dx in [-18, 18]:
        svg.append(f'<line x1="{x1 + dx}" y1="{y0 - 70}" x2="{x1 + dx}" y2="{y0 - 15}" stroke="#111111" stroke-width="5"/>')
        svg.append(f'<polygon points="{x1 + dx - 10},{y0 - 15} {x1 + dx + 10},{y0 - 15} {x1 + dx},{y0 + 5}" fill="#111111"/>')

    # Deformed visual curve
    svg.append(f'<path d="{curve_path}" fill="none" stroke="#555555" stroke-width="5" stroke-dasharray="10 8"/>')
    svg.append(svg_text(x0 + 360, y0 + 130, "deformed shape, schematic", size=20, anchor="middle"))

    # Result panel
    svg.append('<rect x="830" y="170" width="300" height="410" rx="18" fill="#f7f7f7" stroke="#d0d0d0"/>')
    svg.append(svg_text(865, 220, "Result", size=28, weight="bold"))

    svg.append(svg_text(865, 285, "Analytical", size=22, weight="bold"))
    svg.append(svg_text(865, 320, f"{analytical:.6f} mm", size=30))

    svg.append(svg_text(865, 390, "CalculiX", size=22, weight="bold"))
    svg.append(svg_text(865, 425, f"{ccx:.6f} mm", size=30))

    svg.append(svg_text(865, 495, "Relative error", size=22, weight="bold"))
    svg.append(svg_text(865, 530, f"{error:.3f} %", size=34, weight="bold"))

    # Footer
    svg.append(svg_text(70, 635, "Workflow: Python input generation → CCX in Docker → Python .dat postprocessing", size=22))

    svg.append("</svg>")

    out_file.write_text("\n".join(svg), encoding="utf-8")
    print(f"Written: {out_file}")


if __name__ == "__main__":
    main()
