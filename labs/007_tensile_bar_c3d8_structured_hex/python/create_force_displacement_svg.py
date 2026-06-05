#!/usr/bin/env python3
"""
Create force-displacement SVG for Lab 007 using the common plotter.
"""

from pathlib import Path
import subprocess
import sys


def main():
    repo_dir = Path(__file__).resolve().parents[3]

    common_plotter = repo_dir / "labs" / "common" / "python" / "create_force_displacement_svg.py"

    csv_file = repo_dir / "labs" / "007_tensile_bar_c3d8_structured_hex" / "results" / "s355mc_force_displacement_curve.csv"
    out_svg = repo_dir / "labs" / "007_tensile_bar_c3d8_structured_hex" / "figures" / "s355mc_force_displacement_curve.svg"
    summary_file = repo_dir / "labs" / "007_tensile_bar_c3d8_structured_hex" / "results" / "s355mc_force_displacement_plot_summary.txt"

    cmd = [
        sys.executable,
        str(common_plotter),
        "--csv", str(csv_file),
        "--out", str(out_svg),
        "--summary", str(summary_file),
        "--title", "Lab 007 — C3D8 structured hex tensile specimen",
        "--subtitle", "S355MC elastoplastic material, displacement-controlled tensile loading",
        "--note", "Structured C3D8 full dogbone mesh; equivalent plastic strain requested as PEEQ and stored in FRD as PE.",
    ]

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
