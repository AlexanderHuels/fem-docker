#!/usr/bin/env python3
"""
Common CalculiX INP mesh reader for FEM Docker labs.

Supported element types:
- C3D8
- C3D10

This module only parses mesh data.
It does not depend on PyVista.
"""

from dataclasses import dataclass
from pathlib import Path
import argparse


@dataclass
class CcxMesh:
    nodes: dict[int, tuple[float, float, float]]
    elements: list[tuple[int, tuple[int, ...]]]
    element_type: str

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def element_count(self) -> int:
        return len(self.elements)

    @property
    def nodes_per_element(self) -> int:
        if not self.elements:
            return 0
        return len(self.elements[0][1])

    @property
    def bounds(self):
        xs = [p[0] for p in self.nodes.values()]
        ys = [p[1] for p in self.nodes.values()]
        zs = [p[2] for p in self.nodes.values()]
        return (
            min(xs), max(xs),
            min(ys), max(ys),
            min(zs), max(zs),
        )


def parse_keyword_parameters(keyword_line: str) -> dict[str, str | bool]:
    """
    Parse a CalculiX/Abaqus-style keyword line.

    Example:
      *ELEMENT, TYPE=C3D8, ELSET=EALL
    """
    parts = [p.strip() for p in keyword_line.split(",")]
    params: dict[str, str | bool] = {}

    for part in parts[1:]:
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            params[key.strip().upper()] = value.strip().upper()
        else:
            params[part.strip().upper()] = True

    return params


def read_ccx_inp_mesh(inp_file: Path, wanted_element_type: str | None = None) -> CcxMesh:
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: list[tuple[int, tuple[int, ...]]] = []

    mode = None
    active_element_type = None
    selected_element_type = None

    with inp_file.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()

            if not line or line.startswith("**"):
                continue

            if line.startswith("*"):
                upper = line.upper()

                if upper.startswith("*NODE"):
                    mode = "NODE"
                    active_element_type = None
                    continue

                if upper.startswith("*ELEMENT"):
                    params = parse_keyword_parameters(upper)
                    active_element_type = str(params.get("TYPE", "")).upper()

                    if wanted_element_type is None:
                        if active_element_type in {"C3D8", "C3D10"}:
                            mode = "ELEMENT"
                            selected_element_type = active_element_type
                        else:
                            mode = None
                    else:
                        if active_element_type == wanted_element_type.upper():
                            mode = "ELEMENT"
                            selected_element_type = active_element_type
                        else:
                            mode = None
                    continue

                mode = None
                active_element_type = None
                continue

            if mode == "NODE":
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 4:
                    continue
                nid = int(parts[0])
                nodes[nid] = (
                    float(parts[1]),
                    float(parts[2]),
                    float(parts[3]),
                )
                continue

            if mode == "ELEMENT":
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) < 2:
                    continue

                eid = int(parts[0])
                conn = tuple(int(v) for v in parts[1:])

                if active_element_type == "C3D8" and len(conn) != 8:
                    raise RuntimeError(f"Element {eid}: expected 8 nodes for C3D8, got {len(conn)}")

                if active_element_type == "C3D10" and len(conn) != 10:
                    raise RuntimeError(f"Element {eid}: expected 10 nodes for C3D10, got {len(conn)}")

                elements.append((eid, conn))

    if not nodes:
        raise RuntimeError(f"No nodes parsed from {inp_file}")

    if not elements:
        et = wanted_element_type or "C3D8/C3D10"
        raise RuntimeError(f"No {et} elements parsed from {inp_file}")

    return CcxMesh(
        nodes=nodes,
        elements=elements,
        element_type=selected_element_type or "UNKNOWN",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inp", required=True, type=Path)
    parser.add_argument("--type", default=None, choices=["C3D8", "C3D10"])
    args = parser.parse_args()

    mesh = read_ccx_inp_mesh(args.inp, args.type)
    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds

    print("Common CCX INP mesh reader summary")
    print("==================================")
    print()
    print(f"Input: {args.inp}")
    print(f"Element type: {mesh.element_type}")
    print(f"Nodes: {mesh.node_count}")
    print(f"Elements: {mesh.element_count}")
    print(f"Nodes per element: {mesh.nodes_per_element}")
    print()
    print(f"x bounds: {xmin:.6f} ... {xmax:.6f} mm")
    print(f"y bounds: {ymin:.6f} ... {ymax:.6f} mm")
    print(f"z bounds: {zmin:.6f} ... {zmax:.6f} mm")


if __name__ == "__main__":
    main()
