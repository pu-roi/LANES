"""Pasig Historical Flood Prior and Gazetteer Service.

Loads, indexes, and queries the 726 verified historical flood records (2020-2025)
from `data/flooded_areas_pasig_clean.csv`.

Provides:
  1. Historical flood recurrence scoring for candidate locations in Pasig.
  2. Grounded street and landmark lookup with recorded water levels and depth ranges.
  3. Dynamic gazetteer export for place extraction and ranking.
"""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PASIG_CLEAN_CSV = REPO_ROOT / "data" / "flooded_areas_pasig_clean.csv"


@dataclass
class HistoricalStreetRecord:
    name: str
    recurrence_count: int = 0
    years: set[int] = field(default_factory=set)
    barangays: set[str] = field(default_factory=set)
    landmarks: set[str] = field(default_factory=set)
    depth_min_cm: float | None = None
    depth_max_cm: float | None = None
    raw_water_levels: list[str] = field(default_factory=list)


@dataclass
class HistoricalLandmarkRecord:
    name: str
    recurrence_count: int = 0
    associated_streets: set[str] = field(default_factory=set)
    associated_barangays: set[str] = field(default_factory=set)
    years: set[int] = field(default_factory=set)


class PasigHistoricalService:
    """In-memory indexed gazetteer of historical Pasig flood recurrence data."""

    def __init__(self, csv_path: Optional[Path] = None) -> None:
        self.csv_path = csv_path or DEFAULT_PASIG_CLEAN_CSV
        self.streets: dict[str, HistoricalStreetRecord] = {}
        self.landmarks: dict[str, HistoricalLandmarkRecord] = {}
        self.barangays: dict[str, int] = {}
        self._loaded = False
        self._load_data()

    def _normalize_key(self, text: str) -> str:
        """Strip punctuation and normalize common street abbreviations for robust matching."""
        lowered = text.lower().strip()
        lowered = re.sub(r"[,\.\(\)\/\-\'\"]+", " ", lowered)
        lowered = re.sub(r"\bavenue\b", "ave", lowered)
        lowered = re.sub(r"\bstreet\b", "st", lowered)
        lowered = re.sub(r"\bboulevard\b", "blvd", lowered)
        lowered = re.sub(r"\broad\b", "rd", lowered)
        lowered = re.sub(r"\bhighway\b", "hwy", lowered)
        lowered = re.sub(r"\bextension\b", "ext", lowered)
        return " ".join(lowered.split())

    def _load_data(self) -> None:
        if not self.csv_path.exists():
            logger.warning("Pasig historical clean CSV not found at %s. Historical priors disabled.", self.csv_path)
            return

        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    year_str = row.get("source_year", "").strip()
                    year = int(year_str) if year_str.isdigit() else 2020
                    bgy = row.get("barangay_canonical", "").strip()
                    street = row.get("street_normalized", "").strip()
                    landmark = row.get("landmark_normalized", "").strip()
                    raw_level = row.get("water_level_raw", "").strip()
                    d_min_str = row.get("depth_min_cm", "").strip()
                    d_max_str = row.get("depth_max_cm", "").strip()

                    d_min = float(d_min_str) if d_min_str else None
                    d_max = float(d_max_str) if d_max_str else None

                    # 1. Index Barangay
                    if bgy:
                        self.barangays[bgy] = self.barangays.get(bgy, 0) + 1

                    # 2. Index Street
                    if street:
                        st_key = self._normalize_key(street)
                        if st_key not in self.streets:
                            self.streets[st_key] = HistoricalStreetRecord(name=street)
                        rec = self.streets[st_key]
                        rec.recurrence_count += 1
                        rec.years.add(year)
                        if bgy:
                            rec.barangays.add(bgy)
                        if landmark:
                            rec.landmarks.add(landmark)
                        if raw_level and raw_level not in rec.raw_water_levels:
                            rec.raw_water_levels.append(raw_level)

                        if d_min is not None:
                            rec.depth_min_cm = d_min if rec.depth_min_cm is None else min(rec.depth_min_cm, d_min)
                        if d_max is not None:
                            rec.depth_max_cm = d_max if rec.depth_max_cm is None else max(rec.depth_max_cm, d_max)

                    # 3. Index Landmark
                    if landmark:
                        lm_key = self._normalize_key(landmark)
                        if lm_key not in self.landmarks:
                            self.landmarks[lm_key] = HistoricalLandmarkRecord(name=landmark)
                        lm_rec = self.landmarks[lm_key]
                        lm_rec.recurrence_count += 1
                        lm_rec.years.add(year)
                        if street:
                            lm_rec.associated_streets.add(street)
                        if bgy:
                            lm_rec.associated_barangays.add(bgy)

            self._loaded = True
            logger.info(
                "Indexed Pasig DRRMO historical flood dataset: %d streets, %d landmarks, %d barangay records across 2020-2025.",
                len(self.streets),
                len(self.landmarks),
                len(self.barangays),
            )
        except Exception as exc:
            logger.error("Failed to index Pasig clean flood history: %s", exc)

    def lookup_street(self, query: str) -> Optional[HistoricalStreetRecord]:
        """Look up street by exact or normalized key, returning highest recurrence match."""
        key = self._normalize_key(query)
        if key in self.streets:
            return self.streets[key]

        matches: list[HistoricalStreetRecord] = []
        for k, rec in self.streets.items():
            if key in k or k in key:
                matches.append(rec)
        if matches:
            return max(matches, key=lambda r: r.recurrence_count)
        return None

    def lookup_landmark(self, query: str) -> Optional[HistoricalLandmarkRecord]:
        """Look up landmark by exact or normalized key, returning highest recurrence match."""
        key = self._normalize_key(query)
        if key in self.landmarks:
            return self.landmarks[key]

        matches: list[HistoricalLandmarkRecord] = []
        for k, rec in self.landmarks.items():
            if key in k or k in key:
                matches.append(rec)
        if matches:
            return max(matches, key=lambda r: r.recurrence_count)
        return None

    def get_recurrence_bonus(
        self,
        place_name: str,
        city_hint: Optional[str] = None,
    ) -> tuple[float, Optional[str]]:
        """Calculate historical recurrence score bonus and rationale for a location mention.
        
        Returns:
            (bonus_score, rationale_string)
        """
        # Only apply Pasig historical prior if city is Pasig or unspecified in a Pasig context
        if city_hint and "pasig" not in city_hint.lower():
            return 0.0, None

        st_match = self.lookup_street(place_name)
        if st_match:
            count = st_match.recurrence_count
            years_str = f"{min(st_match.years)}–{max(st_match.years)}" if st_match.years else "2020–2025"
            depth_str = ""
            if st_match.depth_min_cm and st_match.depth_max_cm:
                depth_str = f"; historical depth {st_match.depth_min_cm:.0f}–{st_match.depth_max_cm:.0f} cm"

            if count >= 15:
                bonus = 0.06
                priority = "Major flood corridor"
            elif count >= 5:
                bonus = 0.04
                priority = "Frequent flood recurrence"
            else:
                bonus = 0.02
                priority = "Documented flood location"

            rationale = (
                f"{priority}: Corroborated by Pasig DRRMO flood history "
                f"('{st_match.name}' recorded {count} times across {years_str}{depth_str})."
            )
            return bonus, rationale

        lm_match = self.lookup_landmark(place_name)
        if lm_match:
            count = lm_match.recurrence_count
            years_str = f"{min(lm_match.years)}–{max(lm_match.years)}" if lm_match.years else "2020–2025"
            bonus = 0.03 if count >= 3 else 0.02
            rationale = (
                f"Historical landmark match: Corroborated by Pasig DRRMO flood records "
                f"('{lm_match.name}' recorded {count} times across {years_str})."
            )
            return bonus, rationale

        return 0.0, None

    def get_known_streets_list(self) -> list[str]:
        """Return list of canonical street names from historical records."""
        return [rec.name for rec in self.streets.values()]

    def get_known_landmarks_list(self) -> list[str]:
        """Return list of canonical landmark names from historical records."""
        return [rec.name for rec in self.landmarks.values()]


_pasig_historical_service: Optional[PasigHistoricalService] = None


def get_pasig_historical_service() -> PasigHistoricalService:
    """Return singleton instance of PasigHistoricalService."""
    global _pasig_historical_service
    if _pasig_historical_service is None:
        _pasig_historical_service = PasigHistoricalService()
    return _pasig_historical_service
