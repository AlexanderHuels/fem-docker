#!/usr/bin/env python3
"""
Generic force-displacement SVG plotter for FEM Docker labs.

Expected CSV columns by default:
- mean_u1_right_mm
- tensile_force_from_right_N
"""

from pathlib import Path
import argparse
import csv
import html


SVG_WIDTH = 1400
SVG_HEIGHT = 800

MARGIN_LEFT = 115
MARGIN_RIGHT = 90
MARGIN_TOP = 90
MARGIN_BOTTOM = 90


def svg_text(x, y, content, size=16, weight="normal", anchor="start", color="#111111"):
    safe = html.escape(str(content))
    return (
        f'<text x="{x:.3f}" y="{y:.3f}" '
        f'text-anchor="{anchor}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{safe}</text>'
    )


def read_force_displacement(csv_file: Path, x_column: str, y_column: str):
    rows = []
    with csv_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if x_column not in reader.fieldnames:
            raise ValueError(f"Missing x column '{x_column}' in {csv_file}")
        if y_column not in reader.fieldnames:
            raise ValueError(f"Missing y column '{y_column}' in {csv_file}")

        for row in reader:
            rows.append((float(row[x_column]), float(row[y_column])))

    if not rows:
        raise ValueError(f"No data rows found in {csv_file}")

    return rows


def nice_ticks(vmin, vmax, n):
    if vmax <= vmin:
        return [vmin]
    step = (vmax - vmin) / n
    return [vmin + i * step for i in range(n + 1)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--summary", type=Path, default=None)

    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--note", default="")

    parser.add_argument("--x-column", default="mean_u1_right_mm")
    parser.add_argument("--y-column", default="tensile_force_from_right_N")

    parser.add_argument("--x-label", default="Right grip displacement Ux [mm]")
    parser.add_argument("--y-label", default="Tensile force [N]")

    parser.add_argument("--x-pad-factor", type=float, default=0.03)
    parser.add_argument("--y-pad-factor", type=float, default=0.05)

    args = parser.parse_args()

    rows = read_force_displacement(args.csv, args.x_column, args.y_column)

    x_values = [r[0] for r in rows]
    y_values = [r[1] for r in rows]

    x_min = 0.0
    x_max_data = max(x_values)
    x_max = x_max_data * (1.0 + args.x_pad_factor)

    y_min = 0.0
    y_max_data = max(y_values)
    y_max = y_max_data * (1.0 + args.y_pad_factor)

    plot_w = SVG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_h = SVG_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

    def map_x(x):
        return MARGIN_LEFT + (x - x_min) / (x_max - x_min) * plot_w

    def map_y(y):
        return MARGIN_TOP + plot_h - (y - y_min) / (y_max - y_min) * plot_h

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">'
    )
    svg.append('<rect x="0" y="0" width="100%" height="100%" fill="white"/>')

    svg.append(svg_text(60, 48, args.title, size=30, weight="bold"))
    if args.subtitle:
        svg.append(svg_text(60, 74, args.subtitle, size=17, color="#444444"))

    x_ticks = nice_ticks(0.0, x_max_data, 5)
    y_ticks = nice_ticks(0.0, y_max_data * 1.05, 6)

    for yt in y_ticks:
        y = map_y(yt)
        svg.append(
            f'<line x1="{MARGIN_LEFT:.3f}" y1="{y:.3f}" '
            f'x2="{MARGIN_LEFT + plot_w:.3f}" y2="{y:.3f}" '
            f'stroke="#e0e0e0" stroke-width="1"/>'
        )
        svg.append(svg_text(MARGIN_LEFT - 12, y + 5, f"{yt:.0f}", size=14, anchor="end", color="#222222"))

    for xt in x_ticks:
        x = map_x(xt)
        svg.append(
            f'<line x1="{x:.3f}" y1="{MARGIN_TOP:.3f}" '
            f'x2="{x:.3f}" y2="{MARGIN_TOP + plot_h:.3f}" '
            f'stroke="#e0e0e0" stroke-width="1"/>'
        )
        svg.append(svg_text(x, MARGIN_TOP + plot_h + 28, f"{xt:.2f}", size=14, anchor="middle", color="#222222"))

    svg.append(
        f'<line x1="{MARGIN_LEFT:.3f}" y1="{MARGIN_TOP:.3f}" '
        f'x2="{MARGIN_LEFT:.3f}" y2="{MARGIN_TOP + plot_h:.3f}" '
        f'stroke="#111111" stroke-width="2"/>'
    )
    svg.append(
        f'<line x1="{MARGIN_LEFT:.3f}" y1="{MARGIN_TOP + plot_h:.3f}" '
        f'x2="{MARGIN_LEFT + plot_w:.3f}" y2="{MARGIN_TOP + plot_h:.3f}" '
        f'stroke="#111111" stroke-width="2"/>'
    )

    points = " ".join(f"{map_x(x):.3f},{map_y(y):.3f}" for x, y in rows)
    svg.append(f'<polyline fill="none" stroke="#005bbb" stroke-width="3" points="{points}"/>')

    final_x, final_y = rows[-1]
    px = map_x(final_x)
    py = map_y(final_y)
    svg.append(f'<circle cx="{px:.3f}" cy="{py:.3f}" r="6" fill="#d62828"/>')
    svg.append(
        svg_text(
            px - 16,
            py - 14,
            f"({final_x:.3f} mm, {final_y:.1f} N)",
            size=14,
            anchor="end",
            color="#111111",
        )
    )

    svg.append(svg_text(MARGIN_LEFT + plot_w / 2, SVG_HEIGHT - 38, args.x_label, size=19, anchor="middle"))
    svg.append(
        f'<text x="28" y="{MARGIN_TOP + plot_h / 2:.3f}" '
        f'text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="19" fill="#111111" '
        f'transform="rotate(-90, 28, {MARGIN_TOP + plot_h / 2:.3f})">'
        f'{html.escape(args.y_label)}</text>'
    )

    if args.note:
        svg.append(svg_text(60, SVG_HEIGHT - 16, args.note, size=14, color="#666666"))

    svg.append("</svg>")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(svg), encoding="utf-8")

    summary = f"""Force-displacement SVG plot
===========================

Input CSV:
{args.csv}

Output SVG:
{args.out}

Data points:
{len(rows)}

Final displacement:
{final_x:.6f} mm

Final tensile force:
{final_y:.6f} N
"""

    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
