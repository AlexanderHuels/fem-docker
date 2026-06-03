#!/usr/bin/env python3
"""
Create an animated GIF of the cantilever shell deformation using Pillow only.

Improved LinkedIn-friendly version:
- larger typography
- better use of canvas
- result values shown directly in the GIF
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


CASE_NAME = "cantilever_shell_animation"
OUTPUT_NAME = "cantilever_shell_animation_linkedin.gif"

SCALE = 30.0
WIDTH = 1200
HEIGHT = 675
MARGIN_X = 70
MARGIN_Y = 80

N_FORWARD = 14
N_BACKWARD = 12
FRAME_DURATION_MS = 90

ANALYTICAL_MM = 2.816901
CCX_MM = 2.830381
ERROR_PERCENT = 0.479


def get_font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)

    return ImageFont.load_default()


def parse_inp(inp_file: Path):
    nodes = {}
    elements = []

    lines = inp_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    mode = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line.startswith("*"):
            upper = line.upper()
            if upper == "*NODE" or upper.startswith("*NODE,"):
                mode = "NODE"
            elif upper.startswith("*ELEMENT"):
                mode = "ELEMENT"
            else:
                mode = None
            continue

        if mode == "NODE":
            parts = [p.strip() for p in line.split(",")]
            nid = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])
            nodes[nid] = (x, y, z)

        elif mode == "ELEMENT":
            parts = [p.strip() for p in line.split(",")]
            eid = int(parts[0])
            conn = tuple(int(p) for p in parts[1:5])
            elements.append((eid, conn))

    if not nodes:
        raise RuntimeError(f"No nodes found in {inp_file}")
    if not elements:
        raise RuntimeError(f"No elements found in {inp_file}")

    return nodes, elements


def parse_allnodes_displacements(dat_file: Path):
    lines = dat_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    in_block = False
    displacements = {}

    for raw in lines:
        line = raw.strip()
        lower = raw.lower()

        if "displacements" in lower and "set allnodes" in lower:
            in_block = True
            continue

        if in_block:
            if line == "":
                continue

            if ("displacements" in lower and "set allnodes" not in lower) or "stresses" in lower or "forces" in lower:
                break

            parts = line.split()
            if len(parts) == 4:
                try:
                    nid = int(parts[0])
                    u1 = float(parts[1])
                    u2 = float(parts[2])
                    u3 = float(parts[3])
                except ValueError:
                    continue
                displacements[nid] = (u1, u2, u3)

    if not displacements:
        raise RuntimeError(f"No ALLNODES displacement block found in {dat_file}")

    return displacements


def build_edges(elements):
    edges = set()
    for _eid, conn in elements:
        n1, n2, n3, n4 = conn
        for a, b in [(n1, n2), (n2, n3), (n3, n4), (n4, n1)]:
            edges.add(tuple(sorted((a, b))))
    return sorted(edges)


def compute_bounds(nodes, displacements, scale):
    xs = []
    zs = []

    for nid, (x, _y, z) in nodes.items():
        u1, _u2, u3 = displacements.get(nid, (0.0, 0.0, 0.0))
        xs.append(x)
        zs.append(z)
        xs.append(x + scale * u1)
        zs.append(z + scale * u3)

    return min(xs), max(xs), min(zs), max(zs)


def make_mapper(xmin, xmax, zmin, zmax):
    span_x = xmax - xmin
    span_z = zmax - zmin

    # Reserve upper area for header/info
    top_reserved = 185
    bottom_reserved = 55

    usable_w = WIDTH - 2 * MARGIN_X
    usable_h = HEIGHT - top_reserved - bottom_reserved

    sx = usable_w / span_x if span_x > 0 else 1.0
    sz = usable_h / span_z if span_z > 0 else 1.0
    s = min(sx, sz)

    x_offset = MARGIN_X + 0.5 * (usable_w - s * span_x)
    y_offset = bottom_reserved + 0.5 * (usable_h - s * span_z)

    def map_point(x, z):
        px = x_offset + (x - xmin) * s
        py = HEIGHT - (y_offset + (z - zmin) * s)
        return px, py

    return map_point


def draw_structure(draw, nodes, edges, map_point, color, width, alpha_scale=0.0, displacements=None):
    for n1, n2 in edges:
        x1, _y1, z1 = nodes[n1]
        x2, _y2, z2 = nodes[n2]

        if displacements is not None and alpha_scale != 0.0:
            u11, _u12, u13 = displacements.get(n1, (0.0, 0.0, 0.0))
            u21, _u22, u23 = displacements.get(n2, (0.0, 0.0, 0.0))
            x1 += alpha_scale * u11
            z1 += alpha_scale * u13
            x2 += alpha_scale * u21
            z2 += alpha_scale * u23

        draw.line([map_point(x1, z1), map_point(x2, z2)], fill=color, width=width)


def create_frame(nodes, edges, displacements, alpha_scale, frame_idx, total_frames):
    xmin, xmax, zmin, zmax = compute_bounds(nodes, displacements, SCALE)
    map_point = make_mapper(xmin, xmax, zmin, zmax)

    img = Image.new("RGB", (WIDTH, HEIGHT), "#fafafa")
    draw = ImageDraw.Draw(img)

    font_title = get_font(30, bold=True)
    font_sub = get_font(17, bold=False)
    font_label = get_font(16, bold=False)
    font_value = get_font(19, bold=True)
    font_small = get_font(15, bold=False)

    # Header
    draw.text((55, 32), "Lab 004 — Animated Cantilever Deformation", fill="#111111", font=font_title)
    draw.text((55, 72), "CalculiX 2.23 in Docker | Pillow GIF animation", fill="#333333", font=font_sub)

    # Info boxes
    box_y = 104
    box_h = 58
    boxes = [
        ("Analytical tip", f"{ANALYTICAL_MM:.4f} mm"),
        ("CalculiX tip", f"{CCX_MM:.4f} mm"),
        ("Rel. error", f"{ERROR_PERCENT:.3f} %"),
        ("Scale factor", f"x{SCALE:.0f}"),
    ]

    x = 55
    for title, value in boxes:
        box_w = 150 if title != "Scale factor" else 135
        # Softer information cards for LinkedIn preview:
        # light fill, no hard border
        draw.rounded_rectangle(
            (x, box_y, x + box_w, box_y + box_h),
            radius=10,
            fill="#f4f4f4",
            outline=None
        )
        draw.text((x + 14, box_y + 11), title, fill="#666666", font=font_label)
        draw.text((x + 14, box_y + 31), value, fill="#111111", font=font_value)
        x += box_w + 12

    # Legend
    legend_y = 150
    draw.line([(820, legend_y), (870, legend_y)], fill=(180, 180, 180), width=4)
    draw.text((880, legend_y - 10), "undeformed", fill="#333333", font=font_label)
    draw.line([(980, legend_y), (1030, legend_y)], fill=(30, 95, 220), width=4)
    draw.text((1040, legend_y - 10), "deformed", fill="#333333", font=font_label)

    # Beam
    draw_structure(draw, nodes, edges, map_point, color=(185, 185, 185), width=3)
    draw_structure(draw, nodes, edges, map_point, color=(30, 95, 220), width=4,
                   alpha_scale=alpha_scale, displacements=displacements)

    # Footer
    draw.text((55, HEIGHT - 34), f"Frame {frame_idx + 1}/{total_frames}", fill="#444444", font=font_small)

    return img


def main():
    lab_dir = Path(__file__).resolve().parents[1]
    results_dir = lab_dir / "results"
    frames_dir = lab_dir / "frames"
    figures_dir = lab_dir / "figures"

    frames_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    inp_file = results_dir / f"{CASE_NAME}.inp"
    dat_file = results_dir / f"{CASE_NAME}.dat"
    gif_file = figures_dir / OUTPUT_NAME

    nodes, elements = parse_inp(inp_file)
    displacements = parse_allnodes_displacements(dat_file)
    edges = build_edges(elements)

    forward = [i / (N_FORWARD - 1) for i in range(N_FORWARD)]
    backward = [i / (N_BACKWARD - 1) for i in range(N_BACKWARD - 2, 0, -1)]
    alphas = forward + backward

    frames = []
    for idx, alpha in enumerate(alphas):
        alpha_scale = SCALE * alpha
        frame = create_frame(nodes, edges, displacements, alpha_scale, idx, len(alphas))
        frame_path = frames_dir / f"frame_{idx:03d}.png"
        frame.save(frame_path)
        frames.append(frame)

    frames[0].save(
        gif_file,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
    )

    print(f"Read input:  {inp_file}")
    print(f"Read dat:    {dat_file}")
    print(f"Nodes:       {len(nodes)}")
    print(f"Elements:    {len(elements)}")
    print(f"Frames:      {len(frames)}")
    print(f"Written GIF: {gif_file}")


if __name__ == "__main__":
    main()
