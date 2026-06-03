#!/usr/bin/env python3
"""
Create a lightweight SVG result card for Lab 003.

No external Python packages are required.
"""

from pathlib import Path


WIDTH = 1200
HEIGHT = 675

analytical = 2.816901
ccx = 2.830381
error = 0.479

nodes = 246
elements = 200


def svg_text(x, y, text, size=28, weight="normal", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="#111111">{text}</text>'
    )


def main() -> None:
    lab_dir = Path(__file__).resolve().parents[1]
    out_file = lab_dir / "figures" / "gmsh_cantilever_result_card.svg"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    svg.append('<rect width="1200" height="675" fill="#ffffff"/>')

    # Header
    svg.append(svg_text(70, 85, "CalculiX 2.23 Docker FEM Lab", size=38, weight="bold"))
    svg.append(svg_text(70, 125, "Lab 003 — Gmsh generated cantilever shell workflow", size=25))

    # Workflow panel
    svg.append('<rect x="70" y="165" width="1060" height="175" rx="18" fill="#f7f7f7" stroke="#d0d0d0"/>')
    svg.append(svg_text(105, 215, "Workflow", size=28, weight="bold"))

    steps = ["Python", "Gmsh CLI", "MSH → INP", "CCX", "Postprocess"]
    x_positions = [150, 360, 570, 780, 990]

    for i, (label, x) in enumerate(zip(steps, x_positions)):
        svg.append(f'<rect x="{x-75}" y="250" width="150" height="50" rx="10" fill="#ffffff" stroke="#222222" stroke-width="2"/>')
        svg.append(svg_text(x, 283, label, size=21, weight="bold", anchor="middle"))
        if i < len(steps) - 1:
            x_next = x_positions[i + 1]
            svg.append(f'<line x1="{x+85}" y1="275" x2="{x_next-90}" y2="275" stroke="#222222" stroke-width="4"/>')
            svg.append(f'<polygon points="{x_next-90},275 {x_next-108},265 {x_next-108},285" fill="#222222"/>')

    # Mesh panel
    svg.append('<rect x="70" y="375" width="500" height="210" rx="18" fill="#f7f7f7" stroke="#d0d0d0"/>')
    svg.append(svg_text(105, 425, "Gmsh mesh", size=28, weight="bold"))

    # Schematic quad mesh
    x0, y0 = 120, 470
    w, h = 360, 70
    svg.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="#222222" stroke-width="3"/>')
    for i in range(1, 9):
        x = x0 + i * w / 9
        svg.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0+h}" stroke="#bbbbbb" stroke-width="2"/>')
    for j in range(1, 3):
        y = y0 + j * h / 3
        svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0+w}" y2="{y:.1f}" stroke="#bbbbbb" stroke-width="2"/>')

    svg.append(svg_text(105, 565, f"{nodes} nodes, {elements} S4 shell elements", size=22))

    # Result panel
    svg.append('<rect x="620" y="375" width="510" height="210" rx="18" fill="#f7f7f7" stroke="#d0d0d0"/>')
    svg.append(svg_text(655, 425, "Result", size=28, weight="bold"))

    svg.append(svg_text(655, 475, f"Analytical: {analytical:.6f} mm", size=24))
    svg.append(svg_text(655, 515, f"CalculiX:   {ccx:.6f} mm", size=24))
    svg.append(svg_text(655, 555, f"Relative error: {error:.3f} %", size=27, weight="bold"))

    # Footer
    svg.append(svg_text(70, 640, "Gmsh CLI runs inside the same Docker image as CalculiX — no local Gmsh installation required.", size=22))

    svg.append("</svg>")

    out_file.write_text("\n".join(svg), encoding="utf-8")
    print(f"Written: {out_file}")


if __name__ == "__main__":
    main()
