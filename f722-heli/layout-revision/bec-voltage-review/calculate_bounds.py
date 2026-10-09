#!/usr/bin/env python3
"""Reproduce conditional divider arithmetic. Standard library only; no solver/network.

Run normally to write bounds.json and manifest.json. Run --check to verify the
recorded arithmetic and packet hashes without writing. Optional --bom PATH
also verifies the exact original parts.json bytes and selected entries.
"""

import argparse
import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 40
ROOT = Path(__file__).resolve().parent
FILES = ("REPORT.md", "selected-bom.json", "sources.json", "calculate_bounds.py", "bounds.json")


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def number(value):
    return format(value.quantize(Decimal("0.000000000001")), "f")


def calculate(bom):
    expected = {
        "U6": "TPS63070RNMR",
        "R54": "RT0402BRD0753K6L",
        "R55": "RT0402BRD0710KL",
        "C55": "GRM21BR61A476ME15L",
        "C56": "GRM21BR61A476ME15L",
        "C57": "GRM21BR61A476ME15L",
    }
    if {ref: part["mpn"] for ref, part in bom["selected_parts"].items()} != expected:
        raise ValueError("Selected BOM identities differ from the reviewed parts")
    D = Decimal
    r_top, r_bottom = D("53600"), D("10000")
    tolerance, tcr = D("0.001"), D("0.000025")
    vfb_low, vfb_high, leakage = D("0.792"), D("0.808"), D("0.000000100")
    scenarios = (
        ("resistor_bodies_25C", [25, 25]),
        ("resistor_bodies_85C", [85, 85]),
        ("resistor_bodies_105C_sensitivity", [105, 105]),
        ("conditional_resistor_body_interval_minus40_to85C", [-40, 85]),
    )
    rows = []
    for label, temperatures in scenarios:
        delta = max(abs(D(t) - D(25)) for t in temperatures)
        drift = tcr * delta
        low_factor = (1 - tolerance) * (1 - drift)
        high_factor = (1 + tolerance) * (1 + drift)
        top_low, top_high = r_top * low_factor, r_top * high_factor
        bottom_low, bottom_high = r_bottom * low_factor, r_bottom * high_factor
        low = vfb_low * (1 + top_low / bottom_high)
        high = vfb_high * (1 + top_high / bottom_low)
        rows.append({
            "scenario": label,
            "resistor_body_temperature_interval_C": temperatures,
            "maximum_absolute_delta_from_25C": number(delta),
            "independent_tcr_fraction_per_resistor": number(drift),
            "R54_ohm": {"min": number(top_low), "max": number(top_high)},
            "R55_ohm": {"min": number(bottom_low), "max": number(bottom_high)},
            "no_leakage_reference_divider_V": {"min": number(low), "max": number(high)},
            "positive_100nA_endpoint": {
                "upper_shift_V": number(leakage * top_high),
                "upper_setpoint_V": number(high + leakage * top_high),
                "classification": "Conditional application of the printed +100 nA maximum, tested at VFB=0.8 V; not a complete rail guarantee",
            },
            "signed_100nA_engineering_sensitivity_V": {
                "min": number(low - leakage * top_low),
                "max": number(high + leakage * top_high),
                "classification": "The negative leakage endpoint is assumed, not explicitly guaranteed by TI",
            },
        })
    return {
        "schema": "f722-bec-reference-divider-bounds/v1",
        "classification": "Conditional source/divider arithmetic; no board-rail, thermal, lifetime or flight qualification",
        "bom_source_sha256": bom["source"]["sha256"],
        "selected_bom_file_sha256": sha256((ROOT / "selected-bom.json").read_bytes()),
        "sources_file_sha256": sha256((ROOT / "sources.json").read_bytes()),
        "nominal_setpoint_V": number(D("0.8") * (1 + r_top / r_bottom)),
        "nominal_divider_current_A": number(D("0.8") / r_bottom),
        "nominal_resistor_dissipation_W": {
            "R54": number((D("0.8") / r_bottom) ** 2 * r_top),
            "R55": number((D("0.8") / r_bottom) ** 2 * r_bottom),
        },
        "assumptions": {
            "feedback_V": {"min": "0.792", "max": "0.808"},
            "feedback_scope": "TI PWM accuracy row, PS/SYNC=GND; VIN=2..16 V, TJ=-40..125 C; no load-current test point stated",
            "initial_resistor_tolerance_fraction": "0.001",
            "independent_resistor_TCR_per_C": "0.000025",
            "resistor_reference_temperature_C": 25,
            "temperature_model": "Independent opposing TCR magnitude applied multiplicatively to the initial tolerance; no assumed ratio tracking",
            "formula": "V=VFB*(1+R54/R55); R=Rnom*(1 +/- tolerance)*(1 +/- TCR*abs(Tbody-25)); leakage shift=IFB*R54",
            "line_load": "No additive guaranteed line/load term manufactured from typical-only 0.07%/V and 0.2%/A rows",
            "ambient_temperature_requirement": None,
            "board_geometry_or_copper_losses_included": False,
            "ripple_startup_transients_aging_assembly_drift_included": False,
            "minimum_signed_leakage_guarantee": None,
        },
        "scenarios": rows,
    }


def manifest(bom):
    return {
        "schema": "f722-bec-source-review-manifest/v1",
        "review_date_UTC": "2026-10-09",
        "status": "Source-only review; not numerical acceptance or manufacturing release",
        "original_bom": bom["source"],
        "hash_algorithm": "SHA-256",
        "manifest_note": "Manifest does not hash itself; its SHA-256 is reported separately at handoff",
        "files": {name: {"sha256": sha256((ROOT / name).read_bytes()), "bytes": (ROOT / name).stat().st_size} for name in FILES},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--bom", type=Path, help="Optional original parts.json to verify; never modified")
    args = parser.parse_args()
    bom = json.loads((ROOT / "selected-bom.json").read_text())
    if args.bom:
        raw = args.bom.read_bytes()
        if sha256(raw) != bom["source"]["sha256"]:
            raise SystemExit("FAIL: original parts.json byte hash differs")
        actual = json.loads(raw)
        if any(actual.get(ref) != part for ref, part in bom["selected_parts"].items()):
            raise SystemExit("FAIL: selected BOM entries differ")
    result = encoded(calculate(bom))
    if args.check:
        if (ROOT / "bounds.json").read_bytes() != result:
            raise SystemExit("FAIL: bounds.json is not reproducible")
        if (ROOT / "manifest.json").read_bytes() != encoded(manifest(bom)):
            raise SystemExit("FAIL: packet manifest differs")
        print("PASS: exact arithmetic and all five manifest file hashes verified" + ("; original BOM bytes and selected entries verified" if args.bom else ""))
    else:
        (ROOT / "bounds.json").write_bytes(result)
        (ROOT / "manifest.json").write_bytes(encoded(manifest(bom)))
        print("Wrote bounds.json and manifest.json")


if __name__ == "__main__":
    main()
