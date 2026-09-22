"""Create a reviewable, normalized Pasig flood-history CSV from the raw export.

The raw source is intentionally kept unchanged. This script only prepares a
historical location-prior dataset; it does not geocode roads or merge events.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
DEFAULT_INPUT = DATA_DIR / "Flooded_Areas_Pasig_City_2020_2025_EDITED_ver2.csv"
DEFAULT_REFERENCE = DATA_DIR / "pasig_barangay_reference.csv"
DEFAULT_OUTPUT = DATA_DIR / "flooded_areas_pasig_clean.csv"
EXPECTED_YEAR_COUNTS = {"2020": 47, "2021": 86, "2022": 142, "2023": 122, "2024": 103, "2025": 226}

YEAR_HEADER = re.compile(r"Flooded Areas within Pasig City (20\d{2})", re.IGNORECASE)
DEPTH_PATTERN = re.compile(
    r"^(?P<minimum>\d+(?:\.\d+)?)\s*(?:(?:-|to)\s*(?P<maximum>\d+(?:\.\d+)?))?\s*(?P<unit>inch(?:es)?|feet|foot|meters?|cm)$",
    re.IGNORECASE,
)
UNIT_TO_CM = {
    "inch": Decimal("2.54"),
    "inches": Decimal("2.54"),
    "foot": Decimal("30.48"),
    "feet": Decimal("30.48"),
    "meter": Decimal("100"),
    "meters": Decimal("100"),
    "cm": Decimal("1"),
}
REVIEWED_CORRECTIONS = {
    "maybunnga": ("Maybunga", "corrected_typo"),
    "pala": ("Palatiw", "corrected_manual"),
}


@dataclass(frozen=True)
class BarangayReference:
    name: str
    psgc_10_digit_code: str


def collapse_whitespace(value: str) -> str:
    """Convert source line breaks and repeated spaces into one display space."""
    return " ".join(value.split())


def barangay_key(value: str) -> str:
    """Build a conservative lookup key without changing the preserved raw value."""
    normalized = collapse_whitespace(value).casefold()
    normalized = re.sub(r"\bsta\.?\s+", "santa ", normalized)
    normalized = re.sub(r"\bsto\.?\s+", "santo ", normalized)
    return re.sub(r"[^\w]+", " ", normalized).strip()


def load_barangay_reference(path: Path) -> dict[str, BarangayReference]:
    with path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    reference = {
        barangay_key(row["barangay_name"]): BarangayReference(
            name=row["barangay_name"],
            psgc_10_digit_code=row["psgc_10_digit_code"],
        )
        for row in rows
    }
    if len(reference) != 30:
        raise ValueError(f"Expected 30 Pasig barangays in {path}, found {len(reference)}.")
    return reference


def read_raw_rows(path: Path) -> list[dict[str, str]]:
    """Read the repeated yearly headers in the raw comma-delimited export."""
    rows: list[dict[str, str]] = []
    current_year: str | None = None

    with path.open(encoding="utf-8-sig", newline="") as source:
        for fields in csv.reader(source):
            if not fields:
                continue
            year_match = YEAR_HEADER.search(fields[0])
            if year_match:
                current_year = year_match.group(1)
                continue
            if not fields[0].strip().isdigit():
                continue
            if current_year is None:
                raise ValueError(f"Found a data row before a year header in {path}.")
            if len(fields) != 5:
                raise ValueError(f"Expected five columns for record {fields[0]} in {path}.")
            rows.append(
                {
                    "source_year": current_year,
                    "source_record_no": fields[0],
                    "barangay_raw": fields[1],
                    "street_raw": fields[2],
                    "landmark_raw": fields[3],
                    "water_level_raw": fields[4],
                }
            )
    return rows


def resolve_barangay(
    raw_value: str, reference: dict[str, BarangayReference]
) -> tuple[str, str, str, str]:
    """Return canonical name, PSGC code, status, and optional review reason."""
    raw_key = barangay_key(raw_value)
    correction = REVIEWED_CORRECTIONS.get(raw_key)
    lookup_key = barangay_key(correction[0]) if correction else raw_key
    match = reference.get(lookup_key)
    if match is None:
        raise ValueError(f"Unknown barangay {raw_value!r}; add an explicit reviewed mapping.")

    display_value = collapse_whitespace(raw_value)
    if correction:
        status = correction[1]
    elif display_value == match.name:
        status = "exact"
    else:
        status = "normalized_alias"
    return match.name, match.psgc_10_digit_code, status, ""


def format_centimeters(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def parse_depth(value: str) -> tuple[str, str, str]:
    """Parse explicit measurement text into an inclusive centimeter range."""
    display_value = collapse_whitespace(value)
    if not display_value:
        return "", "", "missing"
    match = DEPTH_PATTERN.fullmatch(display_value)
    if match is None:
        return "", "", "unparsed"

    try:
        multiplier = UNIT_TO_CM[match.group("unit").casefold()]
        minimum = Decimal(match.group("minimum")) * multiplier
        maximum = Decimal(match.group("maximum") or match.group("minimum")) * multiplier
    except (InvalidOperation, KeyError) as error:
        raise ValueError(f"Could not parse depth {value!r}") from error

    return format_centimeters(minimum), format_centimeters(maximum), "parsed"


def clean_rows(
    raw_rows: Iterable[dict[str, str]], reference: dict[str, BarangayReference]
) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for raw_row in raw_rows:
        canonical_name, psgc_code, barangay_status, review_reason = resolve_barangay(
            raw_row["barangay_raw"], reference
        )
        depth_minimum_cm, depth_maximum_cm, depth_status = parse_depth(raw_row["water_level_raw"])
        cleaned.append(
            {
                **raw_row,
                "barangay_canonical": canonical_name,
                "barangay_psgc_10_digit_code": psgc_code,
                "barangay_status": barangay_status,
                "barangay_review_reason": review_reason,
                "street_normalized": collapse_whitespace(raw_row["street_raw"]),
                "landmark_normalized": collapse_whitespace(raw_row["landmark_raw"]),
                "depth_min_cm": depth_minimum_cm,
                "depth_max_cm": depth_maximum_cm,
                "depth_parse_status": depth_status,
            }
        )
    return cleaned


OUTPUT_FIELDS = [
    "source_year",
    "source_record_no",
    "barangay_raw",
    "barangay_canonical",
    "barangay_psgc_10_digit_code",
    "barangay_status",
    "barangay_review_reason",
    "street_raw",
    "street_normalized",
    "landmark_raw",
    "landmark_normalized",
    "water_level_raw",
    "depth_min_cm",
    "depth_max_cm",
    "depth_parse_status",
]


def validate_cleaned_rows(rows: list[dict[str, str]]) -> None:
    year_counts = Counter(row["source_year"] for row in rows)
    if len(rows) != 726 or dict(sorted(year_counts.items())) != EXPECTED_YEAR_COUNTS:
        raise ValueError(f"Unexpected record totals: {len(rows)} rows, {dict(year_counts)}")
    if any(not row["barangay_canonical"] for row in rows):
        raise ValueError("Every row must resolve to a reviewed Pasig barangay.")


def write_cleaned_rows(rows: Iterable[dict[str, str]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    reference = load_barangay_reference(arguments.reference)
    cleaned_rows = clean_rows(read_raw_rows(arguments.input), reference)
    validate_cleaned_rows(cleaned_rows)
    write_cleaned_rows(cleaned_rows, arguments.output)
    print(f"Wrote {len(cleaned_rows)} cleaned records to {arguments.output}")


if __name__ == "__main__":
    main()
