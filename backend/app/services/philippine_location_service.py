"""Philippine Location and Administrative Hierarchy Service.

Provides dynamic, database/CSV-backed geographic resolution across the Philippines
(Provinces, Cities/Municipalities, and Barangays) using official PSA PSGC data.
Eliminates hardcoded place names in Python code files.
"""

from __future__ import annotations

import csv
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
NATIONWIDE_PSGC_CSV = REPO_ROOT / "data" / "philippines_psgc_reference.csv"
PASIG_FALLBACK_CSV = REPO_ROOT / "data" / "pasig_barangay_reference.csv"

# Common spelling variants and abbreviations for Philippine administrative entities
COMMON_ALIASES: dict[str, str] = {
    "sta. cruz": "Santa Cruz",
    "sta cruz": "Santa Cruz",
    "sta. rosa": "Santa Rosa",
    "sta rosa": "Santa Rosa",
    "sta. lucia": "Santa Lucia",
    "sta lucia": "Santa Lucia",
    "sto. tomas": "Santo Tomas",
    "sto tomas": "Santo Tomas",
    "maybunnga": "Maybunga",
    "qc": "Quezon City",
    "manila city": "City of Manila",
    "maynila": "City of Manila",
    "pasig city": "City of Pasig",
}


class PhilippineLocationService:
    """In-memory indexed provider of official PSA PSGC administrative units.

    Loads and indexes 82 provinces, 1,600+ cities/municipalities, and 42,000+ barangays.
    Enables instant (sub-millisecond) hierarchical lookups and disambiguation without
    hardcoding names in application code.
    """

    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or (
            NATIONWIDE_PSGC_CSV if NATIONWIDE_PSGC_CSV.exists() else PASIG_FALLBACK_CSV
        )
        self.provinces: dict[str, dict[str, Any]] = {}
        self.cities: dict[str, list[dict[str, Any]]] = {}
        self.barangays: dict[str, list[dict[str, Any]]] = {}
        self.pasig_barangays: set[str] = set()
        self._loaded = False
        self._load_reference_data()

    def _load_reference_data(self) -> None:
        """Load and index PSGC reference records from CSV."""
        if not self.data_path.exists():
            logger.warning("PSGC reference file not found at %s. Location lookups will be empty.", self.data_path)
            return

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = set(reader.fieldnames or [])

                if "level" in fieldnames:
                    # Nationwide PSGC schema
                    for row in reader:
                        lvl = row.get("level", "").strip()
                        name = row.get("name", "").strip()
                        code = row.get("psgc_code", "").strip()
                        corr = row.get("correspondence_code", "").strip()
                        region = row.get("region", "").strip()
                        province = row.get("province", "").strip()
                        city_mun = row.get("city_municipality", "").strip()

                        if not name:
                            continue

                        name_key = name.lower()

                        if lvl == "Prov":
                            self.provinces[name_key] = {
                                "name": name,
                                "psgc_code": code,
                                "correspondence_code": corr,
                                "region": region,
                            }
                        elif lvl in ("City", "Mun"):
                            entry = {
                                "name": name,
                                "psgc_code": code,
                                "correspondence_code": corr,
                                "region": region,
                                "province": province,
                                "is_city": lvl == "City",
                            }
                            self.cities.setdefault(name_key, []).append(entry)
                            # Index bidirectional variants: 'City of X' <-> 'X' <-> 'X City'
                            if name_key.startswith("city of "):
                                short_key = name_key[8:].strip()
                                self.cities.setdefault(short_key, []).append(entry)
                                self.cities.setdefault(f"{short_key} city", []).append(entry)
                            elif lvl == "City" and not name_key.endswith(" city"):
                                self.cities.setdefault(f"{name_key} city", []).append(entry)
                                self.cities.setdefault(f"city of {name_key}", []).append(entry)
                        elif lvl == "Bgy":
                            entry = {
                                "name": name,
                                "psgc_code": code,
                                "correspondence_code": corr,
                                "region": region,
                                "province": province,
                                "city_municipality": city_mun,
                            }
                            self.barangays.setdefault(name_key, []).append(entry)
                            if city_mun.lower() in ("city of pasig", "pasig"):
                                self.pasig_barangays.add(name)

                elif "barangay_name" in fieldnames:
                    # Pasig-only fallback schema
                    for row in reader:
                        bgy_name = row.get("barangay_name", "").strip()
                        code = row.get("psgc_10_digit_code", "").strip()
                        corr = row.get("psgc_correspondence_code", "").strip()
                        if bgy_name:
                            self.pasig_barangays.add(bgy_name)
                            self.barangays.setdefault(bgy_name.lower(), []).append({
                                "name": bgy_name,
                                "psgc_code": code,
                                "correspondence_code": corr,
                                "region": "National Capital Region (NCR)",
                                "province": "",
                                "city_municipality": "City of Pasig",
                            })

            self._loaded = True
            logger.info(
                "Indexed Philippine geographic references: %d provinces, %d cities/municipalities, %d barangay names (%d in Pasig).",
                len(self.provinces),
                len(self.cities),
                len(self.barangays),
                len(self.pasig_barangays),
            )
        except Exception as exc:
            logger.error("Failed to load PSGC reference dataset from %s: %s", self.data_path, exc)

    def get_pasig_barangays(self) -> set[str]:
        """Return the set of official Pasig City barangays loaded from reference data."""
        return set(self.pasig_barangays)

    def get_pasig_barangay_tuple(self) -> tuple[str, ...]:
        """Return sorted tuple of Pasig barangays for backward compatibility."""
        return tuple(sorted(self.pasig_barangays))

    def normalize_barangay_name(self, raw_name: str, city_context: str | None = "Pasig") -> str | None:
        """Normalize a barangay mention against aliases and reference data.

        If city_context is specified (defaults to 'Pasig'), verifies that the
        barangay exists in that target city.
        """
        if not raw_name:
            return None

        cleaned = raw_name.strip()
        cleaned = re.sub(r"^(?:brgy\.?|bgy\.?|barangay)\s+", "", cleaned, flags=re.I).strip()
        lowered = cleaned.lower()

        # Check Sta / Sto replacements
        norm_sta = re.sub(r"^sta\.?\s+", "santa ", lowered)
        norm_sto = re.sub(r"^sto\.?\s+", "santo ", lowered)

        # Check aliases first
        for candidate in (lowered, norm_sta, norm_sto):
            if candidate in COMMON_ALIASES:
                canonical_alias = COMMON_ALIASES[candidate]
                if city_context:
                    if city_context.lower() in ("pasig", "city of pasig"):
                        if canonical_alias in self.pasig_barangays:
                            return canonical_alias
                    else:
                        return canonical_alias
                return canonical_alias

        # Direct Pasig check if Pasig context is requested
        if city_context and city_context.lower() in ("pasig", "city of pasig"):
            for b in self.pasig_barangays:
                b_lower = b.lower()
                if b_lower in (lowered, norm_sta, norm_sto):
                    return b
            return None

        # General nationwide check
        for candidate in (lowered, norm_sta, norm_sto):
            if candidate in self.barangays:
                entries = self.barangays[candidate]
                if city_context:
                    ctx_lower = city_context.lower()
                    for e in entries:
                        if ctx_lower in e.get("city_municipality", "").lower():
                            return e["name"]
                return entries[0]["name"]

        return None

    def resolve_location_hierarchy(
        self,
        mention: str,
        text_context: str = "",
    ) -> dict[str, Any] | None:
        """Resolve a detected location mention using article text context.

        Disambiguates duplicate barangay or town names by checking if parent
        province or city is mentioned in surrounding text.
        """
        if not mention:
            return None

        lowered = mention.strip().lower()

        # Check if province
        if lowered in self.provinces:
            p = self.provinces[lowered]
            return {
                "matched_name": p["name"],
                "level": "Prov",
                "psgc_code": p["psgc_code"],
                "region": p["region"],
                "province": p["name"],
                "city_municipality": None,
                "confidence": 0.95,
            }

        # Check if city/municipality
        if lowered in self.cities:
            matches = self.cities[lowered]
            if len(matches) == 1:
                c = matches[0]
                return {
                    "matched_name": c["name"],
                    "level": "City" if c.get("is_city") else "Mun",
                    "psgc_code": c["psgc_code"],
                    "region": c["region"],
                    "province": c["province"],
                    "city_municipality": c["name"],
                    "confidence": 0.90,
                }
            # Multi-match: disambiguate using text_context
            for c in matches:
                prov = c.get("province", "").lower()
                if prov and prov in text_context.lower():
                    return {
                        "matched_name": c["name"],
                        "level": "City" if c.get("is_city") else "Mun",
                        "psgc_code": c["psgc_code"],
                        "region": c["region"],
                        "province": c["province"],
                        "city_municipality": c["name"],
                        "confidence": 0.92,
                    }
            return {
                "matched_name": matches[0]["name"],
                "level": "City" if matches[0].get("is_city") else "Mun",
                "psgc_code": matches[0]["psgc_code"],
                "region": matches[0]["region"],
                "province": matches[0]["province"],
                "city_municipality": matches[0]["name"],
                "confidence": 0.60,
                "ambiguity": [m["province"] for m in matches],
            }

        # Check if barangay
        cleaned_bgy = re.sub(r"^(?:brgy\.?|bgy\.?|barangay)\s+", "", mention, flags=re.I).strip().lower()
        if cleaned_bgy in self.barangays:
            bgy_matches = self.barangays[cleaned_bgy]
            ctx_lower = text_context.lower()
            for b in bgy_matches:
                city = b.get("city_municipality", "").lower()
                prov = b.get("province", "").lower()
                city_short = re.sub(r"^(?:city of\s+|lungsod ng\s+)", "", city)
                if city_short.endswith(" city"):
                    city_short = city_short[:-5]
                city_short = city_short.strip()

                if (city and city in ctx_lower) or (city_short and city_short in ctx_lower) or (prov and prov in ctx_lower):
                    return {
                        "matched_name": b["name"],
                        "level": "Bgy",
                        "psgc_code": b["psgc_code"],
                        "region": b["region"],
                        "province": b["province"],
                        "city_municipality": b["city_municipality"],
                        "confidence": 0.90,
                    }
            # Fallback to Pasig if text mentions Pasig
            if "pasig" in ctx_lower:
                for b in bgy_matches:
                    if "pasig" in b.get("city_municipality", "").lower():
                        return {
                            "matched_name": b["name"],
                            "level": "Bgy",
                            "psgc_code": b["psgc_code"],
                            "region": b["region"],
                            "province": b["province"],
                            "city_municipality": b["city_municipality"],
                            "confidence": 0.85,
                        }
            return {
                "matched_name": bgy_matches[0]["name"],
                "level": "Bgy",
                "psgc_code": bgy_matches[0]["psgc_code"],
                "region": bgy_matches[0]["region"],
                "province": bgy_matches[0]["province"],
                "city_municipality": bgy_matches[0]["city_municipality"],
                "confidence": 0.50,
                "ambiguous_parents": [b["city_municipality"] for b in bgy_matches[:5]],
            }

        return None


@lru_cache(maxsize=1)
def get_philippine_location_service() -> PhilippineLocationService:
    """Return singleton cached instance of PhilippineLocationService."""
    return PhilippineLocationService()
