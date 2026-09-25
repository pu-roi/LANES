"""Regression tests for the Pasig flood-history cleaning dataset."""

import csv
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "backend" / "scripts" / "clean_pasig_flood_history.py"
SPEC = spec_from_file_location("clean_pasig_flood_history", SCRIPT_PATH)
assert SPEC and SPEC.loader
cleaner = module_from_spec(SPEC)
sys.modules[SPEC.name] = cleaner
SPEC.loader.exec_module(cleaner)


def test_raw_csv_has_expected_record_counts() -> None:
    rows = cleaner.read_raw_rows(cleaner.DEFAULT_INPUT)

    assert len(rows) == 726
    assert {year: sum(row["source_year"] == year for row in rows) for year in cleaner.EXPECTED_YEAR_COUNTS} == cleaner.EXPECTED_YEAR_COUNTS


def test_cleaner_resolves_psgc_barangays_and_preserves_raw_values() -> None:
    reference = cleaner.load_barangay_reference(cleaner.DEFAULT_REFERENCE)
    cleaned_rows = cleaner.clean_rows(cleaner.read_raw_rows(cleaner.DEFAULT_INPUT), reference)
    cleaner.validate_cleaned_rows(cleaned_rows)

    san_miguel = next(row for row in cleaned_rows if row["barangay_raw"] == "San Miguel")
    maybunnga = next(row for row in cleaned_rows if row["barangay_raw"] == "Maybunnga")
    pala = next(row for row in cleaned_rows if row["barangay_raw"] == "Pala")

    assert len(reference) == 30
    assert san_miguel["barangay_canonical"] == "San Miguel"
    assert san_miguel["barangay_psgc_10_digit_code"] == "1381200022"
    assert maybunnga["barangay_canonical"] == "Maybunga"
    assert maybunnga["barangay_status"] == "corrected_typo"
    assert pala["barangay_canonical"] == "Palatiw"
    assert pala["barangay_psgc_10_digit_code"] == "1381200014"
    assert pala["barangay_status"] == "corrected_manual"
    assert pala["barangay_review_reason"] == ""


def test_cleaner_normalizes_aliases_and_parses_depths() -> None:
    reference = cleaner.load_barangay_reference(cleaner.DEFAULT_REFERENCE)
    canonical, code, status, reason = cleaner.resolve_barangay("Sta. Lucia", reference)

    assert (canonical, code, status, reason) == ("Santa Lucia", "1381200030", "normalized_alias", "")
    assert cleaner.parse_depth("3-4 inches") == ("7.62", "10.16", "parsed")
    assert cleaner.parse_depth("1 inch") == ("2.54", "2.54", "parsed")
    assert cleaner.parse_depth("2 Feet") == ("60.96", "60.96", "parsed")
    assert cleaner.parse_depth("1.5 meters") == ("150.00", "150.00", "parsed")
    assert cleaner.parse_depth("") == ("", "", "missing")
    assert cleaner.parse_depth("1 leg deep") == ("", "", "unparsed")


def test_cleaner_writes_a_traceable_output(tmp_path: Path) -> None:
    reference = cleaner.load_barangay_reference(cleaner.DEFAULT_REFERENCE)
    raw_rows = cleaner.read_raw_rows(cleaner.DEFAULT_INPUT)
    cleaned_rows = cleaner.clean_rows(raw_rows, reference)
    output_path = tmp_path / "flooded_areas_pasig_clean.csv"

    cleaner.write_cleaned_rows(cleaned_rows, output_path)
    with output_path.open(encoding="utf-8", newline="") as output_file:
        written_rows = list(csv.DictReader(output_file))

    assert output_path.exists()
    assert len(written_rows) == len(cleaned_rows)
    assert written_rows[0]["street_raw"] == raw_rows[0]["street_raw"]
    assert written_rows[0]["source_year"] == raw_rows[0]["source_year"]
