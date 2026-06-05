#!/usr/bin/env python3
"""
Create an SVG preview of the Gmsh dogbone mesh.

No external Python packages are required.
"""

from pathlib import Path


CASE_NAME = "tensile_dogbone_iso6892_form1"

SVG_WIDTH = 1400
SVG_HEIGHT = 700
MARGIN = 80


def read_msh2(msh_file: Path):
    lines = msh_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    nodes = {}
    elements = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line == "$Nodes":
            n_nodes = int(lines[i + 1].strip())
            i += 2
            for _ in range(n_nodes):
                parts = lines[i].split()
                nid = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                nodes[nid] = (x, y, z)
                i += 1
            continue

        if line == "$Elements":
            n_elements = int(lines[i + 1].strip())
            i += 2
            for _ in range(n_elements):
                parts = lines[i].split()
                eid = int(parts[0])
                etype = int(parts[1])
                ntags = int(parts[2])
                conn = [int(v) for v in parts[3 + ntags:]]

                # Gmsh MSH2:
                # 1 = 2-node line
                # 2 = 3-node triangle
                # 3 = 4-node quadrangle
                if etype in (1, 2, 3):
                    elements.append((eid, etype, conn))

                i += 1
            continue

        i += 1

    return nodes, elements


def make_mapper(nodes):
    xs = [p[0] for p in nodes.values()]
    ys = [p[1] for p in nodes.values()]

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    span_x = xmax - xmin
    span_y = ymax - ymin

    sx = (SVG_WIDTH - 2 * MARGIN) / span_x
    sy = (SVG_HEIGHT - 2 * MARGIN) / span_y
    s = min(sx, sy)

    x_offset = MARGIN + 0.5 * ((SVG_WIDTH - 2 * MARGIN) - s * span_x)
    y_offset = MARGIN + 0.5 * ((SVG_HEIGHT - 2 * MARGIN) - s * span_y)

    def map_xy(x, y):
        px = x_offset + (x - xmin) * s
        py = SVG_HEIGHT - (y_offset + (y - ymin) * s)
        return px, py

    return map_xy, (xmin, xmax, ymin, ymax)


def edge_set(elements):
    edges = set()

    for _eid, etype, conn in elements:
        if etype == 1 and len(conn) == 2:
            edges.add(tuple(sorted((conn[0], conn[1]))))

        elif etype == 2 and len(conn) == 3:
            for a, b in [(conn[0], conn[1]), (conn[1], conn[2]), (conn[2], conn[0])]:
                edges.add(tuple(sorted((a, b))))

        elif etype == 3 and len(conn) == 4:
            for a, b in [(conn[0], conn[1]), (conn[1], conn[2]), (conn[2], conn[3]), (conn[3], conn[0])]:
                edges.add(tuple(sorted((a, b))))

    return sorted(edges)


def svg_text(x, y, text, size=22, weight="normal"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="#111111">{text}</text>'
    )


def main():
    lab_dir = Path(__file__).resolve().parents[1]
    msh_file = lab_dir / "mesh" / f"{CASE_NAME}.msh"
    out_file = lab_dir / "figures" / "dogbone_mesh_preview.svg"

    nodes, elements = read_msh2(msh_file)

    if not nodes:
        raise RuntimeError(f"No nodes found in {msh_file}")

    if not elements:
        raise RuntimeError(f"No elements found in {msh_file}")

    map_xy, bounds = make_mapper(nodes)
    xmin, xmax, ymin, ymax = bounds

    mesh_edges = edge_set(elements)

    n_lines = sum(1 for _eid, etype, _conn in elements if etype == 1)
    n_tris = sum(1 for _eid, etype, _conn in elements if etype == 2)
    n_quads = sum(1 for _eid, etype, _conn in elements if etype == 3)

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">')
    svg.append('<rect width="100%" height="100%" fill="#ffffff"/>')

    svg.append(svg_text(60, 55, "Lab 006 — ISO 6892-1 flat dogbone tensile specimen", size=30, weight="bold"))
    svg.append(svg_text(60, 88, "Gmsh 2D mesh preview before nonlinear CalculiX setup", size=20))

    # mesh edges
    for n1, n2 in mesh_edges:
        x1, y1, _z1 = nodes[n1]
        x2, y2, _z2 = nodes[n2]
        p1 = map_xy(x1, y1)
        p2 = map_xy(x2, y2)
        svg.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" '
            f'x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="#9a9a9a" stroke-width="0.8"/>'
        )

    # centerline
    x_left, y_mid = map_xy(xmin, 0.0)
    x_right, _ = map_xy(xmax, 0.0)
    svg.append(
        f'<line x1="{x_left:.2f}" y1="{y_mid:.2f}" '
        f'x2="{x_right:.2f}" y2="{y_mid:.2f}" '
        f'stroke="#cc3333" stroke-width="1.5" stroke-dasharray="8,8"/>'
    )

    info_y = SVG_HEIGHT - 120
    svg.append(svg_text(60, info_y, f"Nodes: {len(nodes)}", size=20))
    svg.append(svg_text(60, info_y + 28, f"Line elements: {n_lines} | Triangles: {n_tris} | Quads: {n_quads}", size=20))
    svg.append(svg_text(60, info_y + 56, f"Bounding box: X = {xmin:.1f} ... {xmax:.1f} mm, Y = {ymin:.1f} ... {ymax:.1f} mm", size=20))

    svg.append(svg_text(860, info_y, "Design:", size=20, weight="bold"))
    svg.append(svg_text(860, info_y + 28, "a0 = 2.0 mm, b0 = 12.5 mm, L0 = 50 mm, Lc = 75 mm", size=20))
    svg.append(svg_text(860, info_y + 56, "B = 25 mm, transition target radius >= 30 mm", size=20))

    svg.append("</svg>")

    out_file.write_text("\n".join(svg), encoding="utf-8")

    print(f"Read mesh: {msh_file}")
    print(f"Written: {out_file}")
    print(f"Nodes: {len(nodes)}")
    print(f"Line elements: {n_lines}")
    print(f"Triangles: {n_tris}")
    print(f"Quads: {n_quads}")
    print(f"Bounds: x=({xmin:.3f}, {xmax:.3f}), y=({ymin:.3f}, {ymax:.3f})")


if __name__ == "__main__":
    main()
