"""Fetch and clean the official Philippine Standard Geographic Code (PSGC) reference dataset.

Downloads the structured PSGC dataset and compiles it into:
data/philippines_psgc_reference.csv

Contains all regions, provinces, cities, municipalities, and barangays
with their hierarchical parent links.
"""

from __future__ import annotations

import csv
import io
import logging
import os
import sys
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PSGC_SOURCE_URL = "https://raw.githubusercontent.com/rguj/psgc-dif/main/src/2023_Q1/psgc.csv"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV_PATH = REPO_ROOT / "data" / "philippines_psgc_reference.csv"


def download_and_clean_psgc(source_url: str = PSGC_SOURCE_URL, output_path: Path = OUTPUT_CSV_PATH) -> int:
    """Download PSGC raw CSV and compile hierarchical reference dataset."""
    logger.info("Downloading raw PSGC data from %s...", source_url)
    req = urllib.request.Request(source_url, headers={"User-Agent": "LANES-PSGC-Fetcher/1.0"})
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw_bytes = resp.read()
    
    logger.info("Downloaded %0.2f MB. Parsing CSV...", len(raw_bytes) / (1024 * 1024))
    content = raw_bytes.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    # Build id lookup for parent resolution
    id_map: dict[str, dict[str, str]] = {r["id"]: r for r in rows if "id" in r}

    out_rows: list[dict[str, str]] = []
    for r in rows:
        lvl = r.get("geographic_level", "").strip()
        if lvl not in ("Reg", "Prov", "Dist", "City", "Mun", "Bgy", "SubMun"):
            continue
        name = r.get("name", "").strip()
        code = r.get("psgc_10digit", "").strip()
        corr_code = r.get("correspondence_code", "").strip()

        parent_reg_name = id_map.get(r.get("parent_reg", ""), {}).get("name", "")
        parent_prov_name = id_map.get(r.get("parent_prov", ""), {}).get("name", "")
        parent_cmss_name = id_map.get(r.get("parent_cmss", ""), {}).get("name", "")

        out_rows.append({
            "psgc_code": code,
            "correspondence_code": corr_code,
            "name": name,
            "level": lvl,
            "region": parent_reg_name,
            "province": parent_prov_name,
            "city_municipality": parent_cmss_name,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["psgc_code", "correspondence_code", "name", "level", "region", "province", "city_municipality"]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("Successfully wrote %d PSGC records to %s (%0.2f MB).", len(out_rows), output_path, file_size_mb)
    return len(out_rows)


if __name__ == "__main__":
    count = download_and_clean_psgc()
    print(f"Done. Cleaned {count} records.")
