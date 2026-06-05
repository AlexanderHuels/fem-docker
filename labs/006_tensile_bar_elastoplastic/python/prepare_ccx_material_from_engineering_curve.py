#!/usr/bin/env python3
"""
Prepare a CalculiX elastoplastic material card from an engineering stress-strain curve.

Input:
- Engineering stress / engineering strain CSV
- Datasheet metadata CSV

Output:
- converted engineering/true/plastic curve CSV
- CalculiX-compatible plastic curve CSV
- CalculiX material include file
- material summary text

Expected raw curve columns can be named flexibly, e.g.:
- engineering_stress_MPa, engineering_strain_percent
- sigma_eng_MPa, epsilon_eng_percent
- σ-tech [MPa], ε-technisch [%]

CalculiX *PLASTIC expects:
    true stress [MPa], plastic strain [-]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import math
import re
from typing import Dict, List, Tuple


DEFAULT_MAX_PLASTIC_POINTS = 80


def parse_number(value: str) -> float:
    text = str(value).strip()
    text = text.replace("%", "")
    text = text.replace(",", ".")
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.strip()

    if not text:
        raise ValueError("empty numeric value")

    return float(text)


def normalize_header(text: str) -> str:
    s = text.strip().lower()
    s = s.replace("σ", "sigma")
    s = s.replace("ε", "epsilon")
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    s = s.replace("ß", "ss")
    s = re.sub(r"[^a-z0-9_%\[\]-]+", "_", s)
    return s


def split_line_whitespace(line: str) -> List[str]:
    return re.split(r"\s+", line.strip())


def read_flexible_table(path: Path) -> Tuple[List[str], List[List[str]]]:
    raw_lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not raw_lines:
        raise RuntimeError(f"No usable lines found in {path}")

    sample = "\n".join(raw_lines[:20])

    delimiter = None
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = None

    rows: List[List[str]] = []

    if delimiter is not None:
        reader = csv.reader(raw_lines, delimiter=delimiter)
        for row in reader:
            clean = [cell.strip() for cell in row if cell.strip()]
            if clean:
                rows.append(clean)
    else:
        for line in raw_lines:
            rows.append(split_line_whitespace(line))

    if not rows:
        raise RuntimeError(f"No rows parsed from {path}")

    # Detect header: if first two columns are not both numeric, first row is header.
    first = rows[0]
    has_header = True
    if len(first) >= 2:
        try:
            parse_number(first[0])
            parse_number(first[1])
            has_header = False
        except ValueError:
            has_header = True

    if has_header:
        headers = first
        data_rows = rows[1:]
    else:
        headers = ["col1", "col2"]
        data_rows = rows

    return headers, data_rows


def find_column(headers: List[str], kind: str) -> int:
    normalized = [normalize_header(h) for h in headers]

    if kind == "stress":
        candidates = ["stress", "spannung", "sigma", "mpa", "tech"]
    elif kind == "strain":
        candidates = ["strain", "dehnung", "epsilon", "eps", "%"]
    else:
        raise ValueError(kind)

    scores = []
    for idx, h in enumerate(normalized):
        score = sum(1 for c in candidates if c in h)
        scores.append((score, idx, h))

    scores.sort(reverse=True)

    if scores and scores[0][0] > 0:
        return scores[0][1]

    # Fallback: first two columns
    return 0 if kind == "stress" else 1


def read_engineering_curve(path: Path) -> List[Tuple[float, float]]:
    """
    Return list of:
        engineering_strain_fraction, engineering_stress_MPa
    """
    headers, rows = read_flexible_table(path)

    stress_col = find_column(headers, "stress")
    strain_col = find_column(headers, "strain")

    points = []

    for row in rows:
        if len(row) <= max(stress_col, strain_col):
            continue

        try:
            stress_mpa = parse_number(row[stress_col])
            strain_raw = parse_number(row[strain_col])
        except ValueError:
            continue

        # If the column header indicates percent, divide by 100.
        # Your data uses e.g. 0.006 for 0.006 %, so this becomes 0.00006.
        h = normalize_header(headers[strain_col]) if headers else ""
        if "%" in h or "percent" in h or "prozent" in h:
            strain_fraction = strain_raw / 100.0
        else:
            # Heuristic: values above 1 are almost certainly percent.
            strain_fraction = strain_raw / 100.0 if strain_raw > 1.0 else strain_raw

        if stress_mpa <= 0.0:
            continue
        if strain_fraction < 0.0:
            continue

        points.append((strain_fraction, stress_mpa))

    if len(points) < 5:
        raise RuntimeError(f"Too few engineering curve points parsed from {path}")

    # Sort by engineering strain and remove exact duplicate strain entries.
    points.sort(key=lambda p: p[0])

    dedup = []
    seen = set()
    for eps, sig in points:
        key = round(eps, 12)
        if key in seen:
            continue
        seen.add(key)
        dedup.append((eps, sig))

    return dedup


def read_datasheet(path: Path) -> Dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(path)

    result: Dict[str, str] = {}

    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get("key", "").strip()
            value = row.get("value", "").strip()
            if key:
                result[key] = value

    return result


def as_float(datasheet: Dict[str, str], key: str, default: float | None = None) -> float:
    if key not in datasheet or datasheet[key] == "":
        if default is None:
            raise KeyError(f"Missing required datasheet key: {key}")
        return default
    return parse_number(datasheet[key])


def trim_to_uts(points: List[Tuple[float, float]]) -> Tuple[List[Tuple[float, float]], int]:
    """
    Trim engineering curve to the maximum engineering stress.

    This avoids using post-necking engineering data directly as homogeneous
    plastic material data.
    """
    max_idx = max(range(len(points)), key=lambda i: points[i][1])
    return points[: max_idx + 1], max_idx


def convert_to_true_plastic(
    engineering_points: List[Tuple[float, float]],
    E_MPa: float,
    YS_MPa: float,
) -> List[Tuple[float, float, float, float]]:
    """
    Return list:
        engineering_strain, engineering_stress, true_strain, true_stress, plastic_strain
    """
    converted = []

    for eps_eng, sig_eng in engineering_points:
        eps_true = math.log1p(eps_eng)
        sig_true = sig_eng * (1.0 + eps_eng)
        eps_pl = eps_true - sig_true / E_MPa

        converted.append((eps_eng, sig_eng, eps_true, sig_true, eps_pl))

    return converted


def build_plastic_curve(
    converted: List[Tuple[float, float, float, float, float]],
    YS_MPa: float,
    max_points: int,
) -> List[Tuple[float, float]]:
    """
    Build monotonic CalculiX plastic curve:
        true_stress_MPa, plastic_strain
    """
    raw_plastic: List[Tuple[float, float]] = []

    # First point: yield stress at zero plastic strain.
    raw_plastic.append((YS_MPa, 0.0))

    last_stress = YS_MPa
    last_eps_pl = 0.0

    for eps_eng, sig_eng, eps_true, sig_true, eps_pl in converted:
        if sig_eng < YS_MPa:
            continue

        if eps_pl <= last_eps_pl + 1e-10:
            continue

        # CalculiX plastic stress should not decrease with plastic strain.
        if sig_true < last_stress:
            continue

        raw_plastic.append((sig_true, eps_pl))
        last_stress = sig_true
        last_eps_pl = eps_pl

    if len(raw_plastic) < 2:
        raise RuntimeError("Plastic curve has fewer than two points after conversion.")

    if len(raw_plastic) <= max_points:
        return raw_plastic

    # Uniform index downsampling preserving first and last point.
    selected = {0, len(raw_plastic) - 1}
    for i in range(max_points):
        idx = round(i * (len(raw_plastic) - 1) / (max_points - 1))
        selected.add(idx)

    return [raw_plastic[i] for i in sorted(selected)]


def write_material_card(
    path: Path,
    material_name: str,
    E_MPa: float,
    nu: float,
    plastic_curve: List[Tuple[float, float]],
) -> None:
    lines = []
    lines.append(f"*MATERIAL, NAME={material_name}")
    lines.append("*ELASTIC")
    lines.append(f"{E_MPa:.6f}, {nu:.6f}")
    lines.append("*PLASTIC")
    for true_stress, plastic_strain in plastic_curve:
        lines.append(f"{true_stress:.6f}, {plastic_strain:.10f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--curve", required=True, type=Path, help="Engineering stress-strain curve CSV")
    parser.add_argument("--datasheet", required=True, type=Path, help="Material datasheet CSV")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory")
    parser.add_argument("--max-points", type=int, default=DEFAULT_MAX_PLASTIC_POINTS)
    parser.add_argument("--include-post-uts", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    datasheet = read_datasheet(args.datasheet)

    material_name = datasheet.get("material_name", "MATERIAL").strip() or "MATERIAL"
    E_MPa = as_float(datasheet, "E_MPa")
    nu = as_float(datasheet, "nu", 0.3)
    YS_MPa = as_float(datasheet, "YS_MPa")

    UTS_LOW = as_float(datasheet, "UTS_LOW_MPa", float("nan"))
    UTS_HIGH = as_float(datasheet, "UTS_HIGH_MPa", float("nan"))
    total_elongation_low = as_float(datasheet, "total_elongation_LOW_percent", float("nan"))

    engineering_points_all = read_engineering_curve(args.curve)

    if args.include_post_uts:
        engineering_points_used = engineering_points_all
        uts_index = max(range(len(engineering_points_all)), key=lambda i: engineering_points_all[i][1])
    else:
        engineering_points_used, uts_index = trim_to_uts(engineering_points_all)

    converted_all = convert_to_true_plastic(engineering_points_used, E_MPa, YS_MPa)
    plastic_curve = build_plastic_curve(converted_all, YS_MPa, args.max_points)

    raw_uts_eps, raw_uts_sig = engineering_points_all[uts_index]

    # Write converted full table.
    converted_csv = args.out_dir / f"{material_name.lower()}_engineering_true_plastic_curve.csv"
    with converted_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "engineering_strain_fraction",
            "engineering_strain_percent",
            "engineering_stress_MPa",
            "true_strain",
            "true_stress_MPa",
            "plastic_strain",
        ])
        for eps_eng, sig_eng, eps_true, sig_true, eps_pl in converted_all:
            writer.writerow([eps_eng, eps_eng * 100.0, sig_eng, eps_true, sig_true, eps_pl])

    plastic_csv = args.out_dir / f"{material_name.lower()}_ccx_plastic_curve.csv"
    with plastic_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["true_stress_MPa", "plastic_strain"])
        writer.writerows(plastic_curve)

    material_inc = args.out_dir / f"{material_name.lower()}_ccx_material.inc"
    write_material_card(material_inc, material_name, E_MPa, nu, plastic_curve)

    summary_file = args.out_dir / f"{material_name.lower()}_material_summary.txt"
    summary = f"""Material conversion summary
===========================

Material:
{material_name}

Input files:
Engineering curve: {args.curve}
Datasheet:         {args.datasheet}

Datasheet values:
E:   {E_MPa:.3f} MPa
nu:  {nu:.6f}
YS:  {YS_MPa:.3f} MPa
UTS range: {UTS_LOW:.3f} ... {UTS_HIGH:.3f} MPa
Total elongation lower value: {total_elongation_low:.3f} %

Raw engineering curve:
All raw points: {len(engineering_points_all)}
Used points:    {len(engineering_points_used)}
Post-UTS included: {args.include_post_uts}

Engineering UTS in raw curve:
UTS engineering stress: {raw_uts_sig:.3f} MPa
Engineering strain at UTS: {raw_uts_eps * 100.0:.3f} %

CalculiX plastic curve:
Plastic points before downsampling/filtering: {len(converted_all)}
Plastic points written: {len(plastic_curve)}
First plastic point:
  true stress = {plastic_curve[0][0]:.6f} MPa
  plastic strain = {plastic_curve[0][1]:.10f}
Last plastic point:
  true stress = {plastic_curve[-1][0]:.6f} MPa
  plastic strain = {plastic_curve[-1][1]:.10f}

Output files:
{converted_csv}
{plastic_csv}
{material_inc}

Notes:
- Engineering stress/strain is converted to true stress/true strain.
- Plastic strain is calculated as true_strain - true_stress / E.
- By default, the curve is trimmed at the engineering UTS to avoid using post-necking engineering data directly as homogeneous plastic material data.
"""

    summary_file.write_text(summary, encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
