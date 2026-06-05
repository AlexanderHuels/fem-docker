#!/usr/bin/env python3
"""
Create SVG plots for the S355MC material curve conversion.

No external Python packages required.
"""

from pathlib import Path
import csv
import math


MATERIAL = "S355MC"
SVG_WIDTH = 1400
SVG_HEIGHT = 760


def read_converted_curve(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "eng_strain_percent": float(row["engineering_strain_percent"]),
                "eng_stress": float(row["engineering_stress_MPa"]),
                "true_strain": float(row["true_strain"]),
                "true_stress": float(row["true_stress_MPa"]),
                "plastic_strain": float(row["plastic_strain"]),
            })
    return rows


def read_plastic_curve(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "true_stress": float(row["true_stress_MPa"]),
                "plastic_strain": float(row["plastic_strain"]),
            })
    return rows


def text(x, y, value, size=16, weight="normal", anchor="start", color="#111"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{value}</text>'
    )


def polyline(points, color, width=3):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def plot_area(svg, x0, y0, w, h, title, xlabel, ylabel, x_values, y_values, curve_points, color):
    xmax = max(x_values)
    ymax = max(y_values)

    # Add 5% headroom
    xmax_plot = xmax * 1.05 if xmax > 0 else 1.0
    ymax_plot = ymax * 1.10 if ymax > 0 else 1.0

    def mx(x):
        return x0 + (x / xmax_plot) * w

    def my(y):
        return y0 + h - (y / ymax_plot) * h

    svg.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#fbfbfb" stroke="#dddddd"/>')
    svg.append(text(x0, y0 - 18, title, size=20, weight="bold"))

    # Grid
    for i in range(6):
        xt = xmax_plot * i / 5
        xp = mx(xt)
        svg.append(f'<line x1="{xp:.2f}" y1="{y0}" x2="{xp:.2f}" y2="{y0+h}" stroke="#eeeeee"/>')
        svg.append(text(xp, y0 + h + 26, f"{xt:.3g}", size=13, anchor="middle", color="#333"))

        yt = ymax_plot * i / 5
        yp = my(yt)
        svg.append(f'<line x1="{x0}" y1="{yp:.2f}" x2="{x0+w}" y2="{yp:.2f}" stroke="#e6e6e6"/>')
        svg.append(text(x0 - 12, yp + 5, f"{yt:.3g}", size=13, anchor="end", color="#333"))

    # Axes
    svg.append(f'<line x1="{x0}" y1="{y0+h}" x2="{x0+w}" y2="{y0+h}" stroke="#111" stroke-width="1.5"/>')
    svg.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0+h}" stroke="#111" stroke-width="1.5"/>')

    mapped = [(mx(x), my(y)) for x, y in curve_points]
    svg.append(polyline(mapped, color=color, width=3))

    # Final marker
    fx, fy = mapped[-1]
    svg.append(f'<circle cx="{fx:.2f}" cy="{fy:.2f}" r="5.5" fill="#cc3333"/>')

    svg.append(text(x0 + w / 2, y0 + h + 58, xlabel, size=15, anchor="middle"))
    svg.append(
        f'<text x="{x0 - 72}" y="{y0 + h/2}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="15" fill="#111" text-anchor="middle" '
        f'transform="rotate(-90 {x0 - 72} {y0 + h/2})">{ylabel}</text>'
    )


def main():
    lab_dir = Path(__file__).resolve().parents[1]
    mat_dir = lab_dir / "materials" / MATERIAL

    converted_file = mat_dir / "s355mc_engineering_true_plastic_curve.csv"
    plastic_file = mat_dir / "s355mc_ccx_plastic_curve.csv"
    out_file = lab_dir / "figures" / "s355mc_material_curve.svg"

    converted = read_converted_curve(converted_file)
    plastic = read_plastic_curve(plastic_file)

    eng_points = [(r["eng_strain_percent"], r["eng_stress"]) for r in converted]
    ccx_points = [(r["plastic_strain"], r["true_stress"]) for r in plastic]

    final_eng_strain, final_eng_stress = eng_points[-1]
    final_pl_strain, final_true_stress = ccx_points[-1]

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">')
    svg.append('<rect width="100%" height="100%" fill="#ffffff"/>')

    svg.append(text(60, 50, "S355MC material curve preparation for CalculiX", size=30, weight="bold"))
    svg.append(text(60, 84, "Engineering stress-strain curve converted to true stress / plastic strain", size=18, color="#333"))

    plot_area(
        svg,
        x0=105,
        y0=145,
        w=540,
        h=420,
        title="Input curve: engineering stress-strain",
        xlabel="Engineering strain [%]",
        ylabel="Engineering stress [MPa]",
        x_values=[p[0] for p in eng_points],
        y_values=[p[1] for p in eng_points],
        curve_points=eng_points,
        color="#1f5fbf",
    )

    plot_area(
        svg,
        x0=805,
        y0=145,
        w=500,
        h=420,
        title="CalculiX input: true stress / plastic strain",
        xlabel="Plastic strain [-]",
        ylabel="True stress [MPa]",
        x_values=[p[0] for p in ccx_points],
        y_values=[p[1] for p in ccx_points],
        curve_points=ccx_points,
        color="#26843a",
    )

    # Summary
    box_x = 105
    box_y = 625
    svg.append(f'<rect x="{box_x}" y="{box_y}" width="1200" height="82" rx="12" fill="#ffffff" stroke="#cccccc"/>')
    svg.append(text(box_x + 22, box_y + 32, "Summary", size=17, weight="bold"))
    svg.append(text(box_x + 22, box_y + 60, f"Engineering UTS ≈ {final_eng_stress:.1f} MPa at {final_eng_strain:.2f} % engineering strain", size=15, color="#333"))
    svg.append(text(box_x + 610, box_y + 60, f"Last CCX plastic point: {final_true_stress:.1f} MPa at εpl = {final_pl_strain:.4f}", size=15, color="#333"))

    svg.append(text(60, SVG_HEIGHT - 20, "Curve is trimmed at engineering UTS to avoid using post-necking engineering data directly as homogeneous plastic material data.", size=14, color="#666"))

    svg.append("</svg>")

    out_file.write_text("\n".join(svg), encoding="utf-8")

    print(f"Read: {converted_file}")
    print(f"Read: {plastic_file}")
    print(f"Written: {out_file}")
    print(f"Engineering points used: {len(converted)}")
    print(f"Plastic points written: {len(plastic)}")
    print(f"Engineering UTS: {final_eng_stress:.6f} MPa at {final_eng_strain:.6f} %")
    print(f"Last plastic point: true stress {final_true_stress:.6f} MPa, plastic strain {final_pl_strain:.10f}")


if __name__ == "__main__":
    main()
