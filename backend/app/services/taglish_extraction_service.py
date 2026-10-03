"""Evidence-linked Taglish NLP extraction service for news articles.

Extracts Pasig places, flood mentions, canonical depth, condition, and event time
while preserving source text offsets, evidence sentences, and explicit uncertainty.
Does NOT activate public zones or alter routing.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.schemas.news_extraction import (
    CanonicalDepth,
    ExtractedClaim,
    FloodCondition,
    NewsArticleExtractorInput,
    NewsExtractionResult,
    PlaceType,
)
from app.services.flood_depth import (
    FLOOD_DEPTH_SEVERITIES,
    get_flood_depth_measurement,
)
from app.services.news_evidence_policy import HYPOTHETICAL_FLOOD_PATTERN, NON_OBSERVATION_PATTERN, non_observation_only
from app.services.philippine_location_service import (
    COMMON_ALIASES,
    get_philippine_location_service,
)
from app.services.pasig_historical_service import (
    get_pasig_historical_service,
)

# Dynamic geographic reference data loaded from official PSA PSGC dataset.
# Eliminates hardcoded barangay and place tuples in Python application code.
_loc_service = get_philippine_location_service()
_historical_service = get_pasig_historical_service()

PASIG_BARANGAYS_CANONICAL: tuple[str, ...] = _loc_service.get_pasig_barangay_tuple()
BARANGAY_ALIASES: dict[str, str] = COMMON_ALIASES

# Base Pasig landmarks augmented dynamically with 301 verified clean DRRMO historical landmarks
PASIG_BASE_LANDMARKS: tuple[str, ...] = (
    "Pasig City Hall", "Pasig Mega Market", "Rizal High School", "Capitol Commons",
    "The Medical City", "Pasig Rainforest Park",
)
_hist_lms = [
    lm for lm in _historical_service.get_known_landmarks_list()
    if len(lm) >= 4 and not lm.isdigit()
]
PASIG_LANDMARKS: tuple[str, ...] = tuple(
    sorted(set(list(PASIG_BASE_LANDMARKS) + _hist_lms), key=len, reverse=True)
)

# Base Pasig streets augmented dynamically with 304 verified clean DRRMO historical streets
PASIG_BASE_STREETS: tuple[str, ...] = (
    "C. Raymundo Avenue", "C. Raymundo Ave",
    "Ortigas Avenue", "Ortigas Ave", "Ortigas Ext", "Ortigas Extension",
    "Sandoval Avenue", "Sandoval Ave",
    "Caruncho Avenue", "Caruncho Ave",
    "Shaw Boulevard", "Shaw Blvd",
    "Mercedes Avenue", "Mercedes Ave",
    "Eusebio Avenue", "Eusebio Ave",
    "Dr. Sixto Antonio Avenue", "Dr. Sixto Antonio Ave",
    "Amang Rodriguez Avenue", "Amang Rodriguez Ave",
    "Julia Vargas Avenue", "Julia Vargas Ave",
    "Market Avenue", "Market Ave",
    "F. Manalo Street", "F. Manalo St",
    "Ilaya Street", "Ilaya St",
    "A. Mabini Street", "A. Mabini St",
    "Urbano Velasco Avenue", "Urbano Velasco Ave",
    "Elisco Road", "Elisco Rd",
    "C5 Road", "C5",
)
_hist_sts = [
    st for st in _historical_service.get_known_streets_list()
    if len(st) >= 4 and not st.isdigit()
]
PASIG_KNOWN_STREETS: tuple[str, ...] = tuple(
    sorted(set(list(PASIG_BASE_STREETS) + _hist_sts), key=len, reverse=True)
)

# Major Philippine national expressways and arterial thoroughfares
MAJOR_PHILIPPINE_CORRIDORS: tuple[str, ...] = (
    "EDSA", "Epifanio de los Santos Avenue",
    "MacArthur Highway", "McArthur Highway",
    "Maharlika Highway",
    "Osmeña Highway", "Osmena Highway",
    "Osmeña Boulevard", "Osmena Boulevard",
    "Colon Street", "Colon St",
    "Roxas Boulevard", "Roxas Blvd", "Roxas Avenue", "Roxas Ave",
    "España Boulevard", "Espana Boulevard",
    "Commonwealth Avenue", "Commonwealth Ave",
    "Quezon Avenue", "Quezon Ave",
    "SLEX", "South Luzon Expressway",
    "NLEX", "North Luzon Expressway",
    "SCTEX", "Subic-Clark-Tarlac Expressway",
    "TPLEX", "Tarlac-Pangasinan-La Union Expressway",
    "CAVITEX", "CALAX",
)

# 82 Official PSA Philippine Provinces
PHILIPPINE_PROVINCES: tuple[str, ...] = tuple(
    sorted([p["name"] for p in _loc_service.provinces.values()], key=len, reverse=True)
)

# Major chartered cities and regional hubs across Luzon, Visayas, Mindanao
PHILIPPINE_MAJOR_CITIES: tuple[str, ...] = (
    # Metro Manila
    "Quezon City", "QC", "Manila", "Maynila", "City of Manila", "Marikina", "Mandaluyong",
    "Taguig", "Makati", "San Juan", "Parañaque", "Paranaque", "Las Piñas", "Las Pinas",
    "Muntinlupa", "Caloocan", "Malabon", "Navotas", "Valenzuela", "Pateros",
    # Greater Manila / Calabarzon / Central Luzon
    "Cainta", "Taytay", "Antipolo", "Antipolo City", "San Mateo", "Rodriguez",
    "San Fernando", "San Fernando City", "Angeles", "Angeles City", "Mabalacat", "Mabalacat City",
    "Malolos", "Malolos City", "Meycauayan", "Meycauayan City", "San Jose del Monte", "San Jose del Monte City",
    "Tarlac City", "Cabanatuan City", "Olongapo", "Olongapo City", "Balanga City",
    "Calamba", "Calamba City", "Santa Rosa", "Santa Rosa City", "Biñan", "Binan", "Cabuyao", "San Pedro",
    "Batangas City", "Lipa", "Lipa City", "Lucena", "Lucena City", "San Pablo", "San Pablo City",
    "Tagaytay", "Tagaytay City", "Bacoor", "Bacoor City", "Imus", "Imus City", "Dasmariñas", "Dasmarinas",
    # Northern Luzon
    "Baguio", "Baguio City", "Dagupan", "Dagupan City", "Laoag", "Laoag City", "Vigan", "Vigan City",
    "Tuguegarao", "Tuguegarao City", "Santiago", "Santiago City", "Ilagan", "Cauayan",
    # Bicol
    "Legazpi", "Legazpi City", "Naga", "Naga City", "Sorsogon City",
    # Visayas
    "Cebu City", "City of Cebu", "Mandaue", "Mandaue City", "Lapu-Lapu", "Lapu-Lapu City",
    "Iloilo City", "City of Iloilo", "Bacolod", "Bacolod City", "Tacloban", "Tacloban City",
    "Ormoc", "Ormoc City", "Dumaguete", "Dumaguete City", "Tagbilaran", "Tagbilaran City",
    "Roxas City", "Calbayog City", "Catbalogan", "Maasin",
    # Mindanao
    "Davao City", "City of Davao", "Cagayan de Oro", "Cagayan de Oro City",
    "Zamboanga City", "General Santos", "General Santos City", "Butuan", "Butuan City",
    "Iligan", "Iligan City", "Cotabato City", "Tagum", "Tagum City", "Digos", "Digos City",
    "Koronadal", "Koronadal City", "Surigao City", "Puerto Princesa", "Puerto Princesa City",
    "Malaybalay", "Valencia", "Ozamiz", "Panabo", "Mati", "Kidapawan", "Marawi",
)
OUT_OF_PASIG_CITIES: tuple[str, ...] = PHILIPPINE_MAJOR_CITIES


def get_island_group_for_region(region: str | None) -> str | None:
    """Map Philippine administrative region to major island group (Luzon, Visayas, Mindanao)."""
    if not region:
        return None
    reg = region.lower()
    if any(k in reg for k in ("ncr", "ilocos", "cagayan", "central luzon", "calabarzon", "mimaropa", "bicol", "car")):
        return "Luzon"
    if any(k in reg for k in ("western visayas", "central visayas", "eastern visayas", "negros")):
        return "Visayas"
    if any(k in reg for k in ("zamboanga", "northern mindanao", "davao", "soccsksargen", "caraga", "barmm", "bangsamoro")):
        return "Mindanao"
    return None

# Precompiled single-pass patterns for high-performance CPU tokenization
LANDMARK_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(lm) for lm in PASIG_LANDMARKS) + r")\b", re.I)
GENERIC_LANDMARK_PATTERN = re.compile(
    r"\b(?:[A-Z][\wÀ-ÿ.'-]*\s+){0,3}"
    r"(?:Circle|Rotunda|Junction|Plaza|Bridge|Park|Terminal|Market|Mall)\b"
)
STREET_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(st) for st in PASIG_KNOWN_STREETS) + r")\b", re.I)
CORRIDOR_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(co) for co in MAJOR_PHILIPPINE_CORRIDORS) + r")\b", re.I)
CITY_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(c) for c in PHILIPPINE_MAJOR_CITIES) + r")\b", re.I)

_prov_patterns = []
for prov in PHILIPPINE_PROVINCES:
    if prov.lower() == "quezon":
        _prov_patterns.append(r"(?:Probinsya\s+ng\s+|Province\s+of\s+)?Quezon(?!\s+City)")
    else:
        _prov_patterns.append(r"(?:Probinsya\s+ng\s+|Province\s+of\s+)?" + re.escape(prov))
PROVINCE_PATTERN = re.compile(r"\b(?:" + "|".join(_prov_patterns) + r")\b", re.I)

# Negation indicators
NEGATION_PATTERNS = re.compile(
    r"\b(?:walang\s+baha|wala\s+namang\s+naitalang\s+pagbaha|hindi\s+binaha|hindi\s+naman\s+binaha|"
    r"no\s+flooding|not\s+flooded|passable\s+sa\s+lahat\s+ng\s+uri\s+ng\s+sasakyan|passable\s+sa\s+lahat|"
    r"totally\s+passable|clear\s+na\s+sa\s+baha|wala\s+nang\s+baha|zero\s+flooding|itinanggi\s+ng.*na\s+may\s+baha)\b",
    re.I,
)

# Forecast and Warning indicators
FORECAST_PATTERNS = re.compile(
    r"\b(?:babala\s+ng\s+pagasa|babala|warning|posibleng\s+bahain|possible\s+flooding|"
    r"maaaring\s+bahain|potential\s+flooding|flash\s+flood\s+warning|flood\s+advisory|"
    r"advisory|forecast|inaasahan\s+ang\s+pagbaha|advised\s+to\s+prepare\s+for\s+potential\s+flooding)\b",
    re.I,
)

# Historical indicators
HISTORICAL_PATTERNS = re.compile(
    r"\b(?:noong\s+nakaraang\s+taon|noong\s+bagyong|during\s+typhoon|taong\s+20\d\d|"
    r"in\s+20\d\d|matatandaang|huling\s+makaranas)\b",
    re.I,
)

# Active flood indicators
ACTIVE_FLOOD_WORDS = re.compile(
    r"\b(?:baha|binaha|binabaha|pagbaha|bumaha|bumabaha|floods?|flooded|flooding|"
    r"nalubog|lubog|submerged|inundated|inundation|water\s+levels?|floodwaters?|tubig)\b",
    re.I,
)

# Infrastructure/program names do not describe water on the ground. Mask only
# these phrases when testing evidence words; keep the source text and offsets.
NON_OBSERVATION_FLOOD_TERMS = re.compile(NON_OBSERVATION_PATTERN, re.I)
OBSERVATION_DEPTH_WORDS = re.compile(
    r"\b(?:(?:gutter|ankle|calf|half[-\s]knee|half[-\s]tire|knee|tire|waist|chest|neck)[-\s]+deep|"
    r"(?:abot|lagpas|lampas|hanggang)[-\s]+(?:sakong|binti|tuhod|gulong|baywang|bewang|dibdib|leeg))\b",
    re.I,
)


def _has_flood_evidence_word(text: str) -> bool:
    evidence_text = NON_OBSERVATION_FLOOD_TERMS.sub(lambda match: " " * len(match.group()), text)
    return bool(ACTIVE_FLOOD_WORDS.search(evidence_text))


def _is_flood_control_only(text: str) -> bool:
    return non_observation_only(text)


# Publisher photo credits and rainfall observations are article context, not
# evidence that every named place in those lines has a reported road flood.
PHOTO_CREDIT = re.compile(r"\b(?:photo(?:graph)?\s+(?:by|from)|image\s+(?:by|from)|PNA\s+photo)\b|^\s*Courtesy\s*:", re.I)
WEATHER_ONLY = re.compile(r"\b(?:rainfall\s+warning|rainfall\s+was\s+recorded|rain\s+fell|weather\s+bureau|rainfall\s+advisory|zero\s+visibility)\b", re.I)
ARTICLE_DATELINE = re.compile(r"^[A-Z][A-Z ]{2,30}(?:,\s*Philippines)?\s*[—–-]\s")

# Condition indicators
CONDITION_RISING = re.compile(r"\b(?:patuloy\s+na\s+tumataas|tumataas|rising|risen\s+to|increasing)\b", re.I)
CONDITION_RECEDING = re.compile(r"\b(?:nagsisimula\s+nang\s+humupa|bumababa\s+na|bumababa|humuhupa|receding|receded|subsiding)\b", re.I)
CONDITION_SUBSIDED = re.compile(r"\b(?:humupa\s+na|completely\s+subsided|subsided|cleared|clear\s+na\s+sa\s+baha|wala\s+nang\s+baha)\b", re.I)

# Explicit Canonical Depth Rules
# ORDER IS CRITICAL: Compounds (half-tire, half-knee) must precede generic words (tires, knee)
DEPTH_RULES: list[tuple[CanonicalDepth, re.Pattern, str]] = [
    (
        "neck",
        re.compile(r"\b(?:abot[-\s]leeg|lagpas\s+leeg|lampas\s+leeg|hanggang\s+leeg|neck[-\s]deep|neck)\b", re.I),
        "rule_neck_deep",
    ),
    (
        "chest",
        re.compile(r"\b(?:abot[-\s]dibdib|lagpas\s+dibdib|lampas\s+dibdib|hanggang\s+dibdib|chest[-\s]deep|chest)\b", re.I),
        "rule_chest_deep",
    ),
    (
        "waist",
        re.compile(r"\b(?:abot[-\s]baywang|lagpas\s+baywang|lampas\s+baywang|hanggang\s+baywang|abot[-\s]bewang|lagpas\s+bewang|waist[-\s]deep|waist)\b", re.I),
        "rule_waist_deep",
    ),
    (
        "half-tire",
        re.compile(r"\b(?:half[-\s]tire(?:[-\s]deep)?|kalahati\s+ng\s+gulong|kalahating\s+gulong|abot[-\s]kalahati\s+ng\s+gulong)\b", re.I),
        "rule_half_tire_deep",
    ),
    (
        "tires",
        re.compile(r"(?<!half[-\s])\b(?:abot[-\s]gulong|lubog\s+ang\s+gulong|tire[-\s]deep|tire-deep|tires?|gulong)\b", re.I),
        "rule_tire_deep",
    ),
    (
        "half-knee",
        re.compile(r"\b(?:half[-\s]knee(?:[-\s]deep)?|abot[-\s]half\s+knee|calf[-\s]deep|lampas\s+sakong|lagpas\s+sakong|abot[-\s]binti|binti)\b", re.I),
        "rule_half_knee_deep",
    ),
    (
        "knee",
        re.compile(r"(?<!half[-\s])\b(?:abot[-\s]tuhod|lagpas\s+tuhod|lampas\s+tuhod|hanggang\s+tuhod|knee[-\s]deep|knee|tuhod)\b", re.I),
        "rule_knee_deep",
    ),
    (
        "gutter",
        re.compile(r"\b(?:gutter[-\s]deep|gutter\s+level|gutter\s+deep|gutter|abot[-\s]sakong|ankle[-\s]deep|ankle\s+deep|sakong)\b", re.I),
        "rule_gutter_deep",
    ),
]

# Unmapped / ambiguous depth expressions (centimeters, feet, meters, generic phrases)
AMBIGUOUS_DEPTH_PATTERN = re.compile(
    r"\b(?:"
    r"\d+\s*(?:to|-)\s*\d+\s*(?:feet|foot|ft|meters?|m|inches|in|centimeters?|cm)|"
    r"\d+\s*(?:centimeters?|cm|meters?|m|feet|foot|ft|inches)|"
    r"mataas\s+na\s+(?:pagbaha|baha)|deep\s+(?:floodwaters?|flood|waters?|flooding)|thigh[-\s]deep|abot[-\s]bubong|"
    r"(?:exceeded|above)\s+a\s+man'?s\s+height|lagpas[-\s]tao"
    r")\b",
    re.I,
)

# Event time expressions
TIME_EXPRESSIONS = re.compile(
    r"\b(?:"
    r"kaninang\s+\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|"
    r"as\s+of\s+\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|"
    r"around\s+\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|"
    r"at\s+\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|"
    r"by\s+\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|"
    r"bandang\s+\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|"
    r"simula\s+kaninang\s+\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|"
    r"kaninang\s+(?:tanghali|umaga|hapon|gabi)|"
    r"kaninang\s+alas-[a-z]+(?:\s+ng\s+(?:hapon|gabi|umaga))?|"
    r"alas-[a-z]+(?:\s+ng\s+(?:hapon|gabi|umaga))?|"
    r"this\s+afternoon|this\s+morning|later\s+tonight|mamayang\s+gabi|ngayong\s+araw|"
    r"noong\s+nakaraang\s+taon|taong\s+20\d\d|in\s+20\d\d"
    r")\b",
    re.I,
)
PHILIPPINE_TIMEZONE = ZoneInfo("Asia/Manila")
OBSERVATION_CLOCK = re.compile(r"^(?:as\s+of|by)\s+(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?$", re.I)
EXPLICIT_OTHER_DATE = re.compile(
    r"\b(?:yesterday|kahapon|last\s+night|previous\s+day|prior\s+day|a\s+day\s+earlier|"
    r"(?:last|on)\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)|"
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b|"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2}|"
    r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{2,4})\b",
    re.I,
)


KNOWN_ABBREVIATIONS = (
    "brgy.", "bgy.", "st.", "ave.", "blvd.", "rd.", "dr.", "no.",
    "p.m.", "a.m.", "sta.", "sto.", "gen.", "gov.", "pagasa.",
    "inc.", "co.", "approx.", "cor.", "svc.",
)

ROAD_SUFFIX = r"(?:Street|St\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Highway|Hwy\.?|Road|Rd\.?|Way|Drive|Dr\.?)"
ROAD_NAME = r"(?:[A-Z][\w-]*\.?|(?:[A-Z]\.){2,3})(?:\s+(?:[A-Z][\w-]*\.?|(?:[A-Z]\.){2,3}|del|de|la|na))*"
GENERIC_ROAD_PATTERN = re.compile(rf"\b{ROAD_NAME}\s+{ROAD_SUFFIX}\b")
INITIAL_ROAD_PATTERN = re.compile(r"\b(?:[A-Z]\.\s*){2,3}[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b")
ROAD_RELATION_PATTERN = re.compile(
    rf"\b(?P<road>{ROAD_NAME}(?:\s+{ROAD_SUFFIX})?)\s+"
    rf"(?P<link>cor\.?|corner|from)\s+"
    rf"(?P<first>{ROAD_NAME}(?:\s+{ROAD_SUFFIX})?)"
    rf"(?:\s+(?:up\s+to|to)\s+(?P<second>{ROAD_NAME}(?:\s+{ROAD_SUFFIX})?))?",
)
# Require two explicit road names for narrative proximity/intersection forms;
# "near a hospital" is a locality qualifier, not another affected road.
NARRATIVE_ROAD_RELATION_PATTERN = re.compile(
    rf"\b(?P<road>{ROAD_NAME}\s+{ROAD_SUFFIX})\s+"
    rf"(?P<link>at\s+the\s+corner\s+of|near|at)\s+"
    rf"(?P<first>{ROAD_NAME}\s+{ROAD_SUFFIX})\b"
)
SERVICE_ROAD_PATTERN = re.compile(
    r"\b(?P<road>[A-Z][\w.-]*(?:\s+[A-Z][\w.-]*){0,2}\s+"
    r"(?:Boulevard|Blvd\.?|Avenue|Ave\.?))\s+"
    r"(?P<site>[A-Z][\w.-]*(?:\s+[A-Z][\w.-]*){0,2}\s+Service\s+Road)\b"
)
ROAD_SEGMENT_PATTERN = re.compile(
    r"\bbetween\s+([A-Z][\w.-]*)\s+and\s+([A-Z][\w.-]*)\s+Streets?\b", re.I
)
NUMERIC_DEPTH_PATTERN = re.compile(
    r"\b(?P<value>\d+(?:\.\d+)?)(?:\s*[-‐‑–]\s*|\s*)(?P<unit>inches|inch|centimeters|centimeter|cm|meters|meter|feet|foot|ft)\b", re.I
)
NUMERIC_DEPTH_RANGE_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:to|-|–)\s*\d+(?:\.\d+)?\s*(?:inches|inch|in|cm|meters?|m|feet|foot|ft)\b", re.I
)


def split_sentences_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """Split text into sentences while tracking start and end character offsets.
    Protects single-letter initials (e.g. C., F.) and common abbreviations.
    """
    sentence_spans: list[tuple[str, int, int]] = []
    current_start = 0
    i = 0
    n = len(text)
    while i < n:
        char = text[i]
        if char in {".", "!", "?", "\n"}:
            is_abbr = False
            if char == ".":
                line_end = text.find("\n", i)
                if line_end < 0:
                    line_end = n
                line_start = text.rfind("\n", 0, i) + 1
                if text[line_start:line_end].lstrip().startswith("--") and i < line_end - 1:
                    is_abbr = True  # An advisory bullet is one reported site.
                # Some publisher copy uses "p.m" without a final period.
                if i >= 1 and text[i - 1].lower() in {"a", "p"} and i + 1 < n and text[i + 1].lower() == "m":
                    is_abbr = True
                # The first dot of p.m./a.m. precedes a lowercase initial.
                if re.search(r"\b[ap]\.m\.$", text[max(0, i - 2):i + 3], re.I):
                    is_abbr = True
                # Check single capital initial like "C." or "F."
                if i >= 1 and text[i - 1].isupper() and (i == 1 or not text[i - 2].isalpha()):
                    is_abbr = True
                else:
                    prefix = text[max(0, i - 12) : i + 1].lower()
                    for abbr in KNOWN_ABBREVIATIONS:
                        if prefix.endswith(abbr):
                            is_abbr = True
                            break

            if not is_abbr:
                sent = text[current_start : i + 1].strip()
                if sent:
                    offset_start = text.find(sent, current_start)
                    offset_end = offset_start + len(sent)
                    sentence_spans.append((sent, offset_start, offset_end))
                current_start = i + 1
        i += 1
    if current_start < n:
        sent = text[current_start:].strip()
        if sent:
            offset_start = text.find(sent, current_start)
            offset_end = offset_start + len(sent)
            sentence_spans.append((sent, offset_start, offset_end))
    return sentence_spans


def normalize_barangay_name(raw_name: str, city_context: str | None = "Pasig") -> str | None:
    """Normalize a place mention to an official PSGC barangay name using PhilippineLocationService."""
    return _loc_service.normalize_barangay_name(raw_name, city_context=city_context)


def find_place_mentions(sentence: str, sent_offset_start: int) -> list[dict[str, Any]]:
    """Locate all place candidates within a sentence with exact character offsets.
    Supports Pasig DRRMO historical gazetteer, official PSGC provinces/cities/barangays,
    major corridors, and generic road patterns without requiring ML NER.
    """
    mentions: list[dict[str, Any]] = []
    relation_spans: list[tuple[int, int]] = []

    # An intersection or named span is one bounded road claim. The crossing
    # road is evidence for its geometry, not a second flooded road.
    for match in [*ROAD_RELATION_PATTERN.finditer(sentence), *NARRATIVE_ROAD_RELATION_PATTERN.finditer(sentence)]:
        primary = match.group("road")
        if primary.lower() in {"barangay", "brgy", "in"}:
            continue
        if match.group("link") == "from" and not (
            re.search(rf"\s+{ROAD_SUFFIX}$", primary)
            or len(primary.split()) > 1
            or primary.lower() in {name.lower() for name in MAJOR_PHILIPPINE_CORRIDORS}
        ):
            continue
        directional_tail = re.match(
            r"\s*\((?:northbound|southbound)\)", sentence[match.end():], re.I,
        )
        relation_text = match.group(0) + (directional_tail.group(0) if directional_tail else "")
        relation_spans.append((sent_offset_start + match.start(), sent_offset_start + match.end()))
        mentions.append({
            "raw_place_name": primary,
            "canonical_barangay": None,
            "place_type": "street",
            "road_segment_raw": relation_text,
            "relation_primary": True,
            "char_start": sent_offset_start + match.start("road"),
            "char_end": sent_offset_start + match.end("road"),
        })
    for match in SERVICE_ROAD_PATTERN.finditer(sentence):
        relation_spans.append((sent_offset_start + match.start(), sent_offset_start + match.end()))
        mentions.append({
            "raw_place_name": match.group("road"),
            "canonical_barangay": None,
            "place_type": "street",
            "road_segment_raw": match.group(0),
            "local_area_raw": match.group("site"),
            "relation_primary": True,
            "char_start": sent_offset_start + match.start("road"),
            "char_end": sent_offset_start + match.end("road"),
        })

    # Road lists often omit suffixes: "These included Burgos and Sto. Niño in
    # Concepcion; ...". Keep the list's locality as evidence, not a geocode.
    list_lead = re.search(r"\bThese included\b", sentence, re.I)
    if list_lead:
        for group in re.finditer(r"[^;]+", sentence[list_lead.end():]):
            group_text = group.group(0)
            area_match = re.search(r"\s+in\s+([A-Z][\wÀ-ÿ.-]*(?:\s+(?:and\s+)?[A-Z][\wÀ-ÿ.-]*){0,2})", group_text)
            if not area_match:
                continue
            area_raw = area_match.group(1).strip().rstrip(".")
            names_text = re.split(r"\s+near\s+", group_text[:area_match.start()])[0]
            for name_match in re.finditer(r"[A-Z][\wÀ-ÿ.-]*(?:\s+[A-Z][\wÀ-ÿ.-]*)*", names_text):
                raw = name_match.group(0).strip().rstrip(".")
                if raw.lower() in ("these", "included", "and"):
                    continue
                start = list_lead.end() + group.start() + name_match.start()
                mentions.append({
                    "raw_place_name": raw,
                    "canonical_barangay": None,
                    "place_type": "street",
                    "local_area_raw": area_raw,
                    "listed_road": True,
                    "char_start": sent_offset_start + start,
                    "char_end": sent_offset_start + start + len(raw),
                })

    # A separate list may name flooded roads that are still passable. These
    # must remain individual claims with their passability, not closures.
    passable_lead = re.search(r"\bincluding\s+portions\s+of\s+", sentence, re.I)
    unnamed_streets = re.search(r",\s+and\s+other\s+streets\s+in\s+", sentence, re.I)
    if passable_lead and unnamed_streets and passable_lead.end() < unnamed_streets.start():
        names_text = sentence[passable_lead.end():unnamed_streets.start()]
        for item in re.finditer(r"[^,]+", names_text):
            raw = item.group(0).strip()
            if not raw:
                continue
            leading_space = len(item.group(0)) - len(item.group(0).lstrip())
            start = passable_lead.end() + item.start() + leading_space
            mentions.append({
                "raw_place_name": raw,
                "canonical_barangay": None,
                "place_type": "street",
                "listed_road": True,
                "char_start": sent_offset_start + start,
                "char_end": sent_offset_start + start + len(raw),
            })

        areas_text = sentence[unnamed_streets.end():].rstrip(".")
        for item in re.finditer(r"[^,]+", areas_text):
            raw = re.sub(r"^and\s+", "", item.group(0).strip(), flags=re.I)
            if not raw:
                continue
            start_in_item = item.group(0).find(raw)
            start = unnamed_streets.end() + item.start() + start_in_item
            mentions.append({
                "raw_place_name": raw,
                "canonical_barangay": None,
                "place_type": "barangay",
                "unnamed_street_area": True,
                "char_start": sent_offset_start + start,
                "char_end": sent_offset_start + start + len(raw),
            })

    # 1. Landmarks (Pasig DRRMO Historical + Base Landmarks)
    for m in LANDMARK_PATTERN.finditer(sentence):
        # Gazetteer homonyms need a named spatial mention. An "interior
        # ministry" or an uppercase MARKET section heading is not a site.
        if m.group(0).casefold() in {"interior", "market", "hypermarket"} and not (
            m.group(0)[0].isupper()
            and re.search(r"\b(?:at|in|on|near|sa)\s+$", sentence[:m.start()], re.I)
        ):
            continue
        mentions.append({
            "raw_place_name": m.group(0),
            "canonical_barangay": None,
            "place_type": "landmark",
            "char_start": sent_offset_start + m.start(),
            "char_end": sent_offset_start + m.end(),
        })

    # A small nationwide landmark suffix rule catches named sites outside the
    # Pasig DRRMO gazetteer (for example, Maysilo Circle) without treating
    # ordinary lowercase phrases as place names. Keep exact mention offsets.
    for m in GENERIC_LANDMARK_PATTERN.finditer(sentence):
        raw = m.group(0).strip()
        if any(
            existing["place_type"] in {"street", "landmark"}
            and existing["char_start"] < sent_offset_start + m.end()
            and existing["char_end"] > sent_offset_start + m.start()
            for existing in mentions
        ):
            continue
        if raw.split()[0].casefold() in {"in", "at", "on", "the", "and", "but", "near"}:
            continue
        mentions.append({
            "raw_place_name": raw,
            "canonical_barangay": None,
            "place_type": "landmark",
            "char_start": sent_offset_start + m.start(),
            "char_end": sent_offset_start + m.end(),
        })

    # 2. Known Pasig Historical Streets
    for m in STREET_PATTERN.finditer(sentence):
        mentions.append({
            "raw_place_name": m.group(0),
            "canonical_barangay": None,
            "place_type": "street",
            "char_start": sent_offset_start + m.start(),
            "char_end": sent_offset_start + m.end(),
        })

    # 2b. Major Philippine National Corridors & Expressways
    for m in CORRIDOR_PATTERN.finditer(sentence):
        mentions.append({
            "raw_place_name": m.group(0),
            "canonical_barangay": None,
            "place_type": "street",
            "char_start": sent_offset_start + m.start(),
            "char_end": sent_offset_start + m.end(),
        })

    # 2c. Generic Nationwide Streets/Avenues/Boulevards/Highways
    for m in list(GENERIC_ROAD_PATTERN.finditer(sentence)) + list(INITIAL_ROAD_PATTERN.finditer(sentence)):
        st_name = m.group(0).strip()
        leading_word = re.match(r"(?:While|In|On|Along|At|The|And|But|Meanwhile|As)\s+", st_name, re.I)
        name_start = m.start() + (leading_word.end() if leading_word else 0)
        if leading_word:
            st_name = st_name[leading_word.end():]
        full_match_name = st_name
        road_suffixes = [
            suffix for suffix in re.finditer(rf"\b{ROAD_SUFFIX}\b", st_name, re.I)
            if suffix.start() > 0 and st_name[suffix.start() - 1].isspace()
        ]
        trailing_area = None
        if len(road_suffixes) > 1:
            first_end = road_suffixes[0].end()
            trailing_area = st_name[first_end:].strip(" .-")
            st_name = st_name[:first_end].rstrip(".")
        if not any(st_name.lower() == existing["raw_place_name"].lower() for existing in mentions):
            road_mention = {
                "raw_place_name": st_name,
                "canonical_barangay": None,
                "place_type": "street",
                "char_start": sent_offset_start + name_start,
                "char_end": sent_offset_start + name_start + len(st_name),
            }
            if trailing_area:
                road_mention["road_segment_raw"] = full_match_name
                road_mention["local_area_raw"] = trailing_area
            mentions.append(road_mention)

    for pattern in (r"\bSitio\s+\d+\b", r"\bCentral Market(?:\s+area)?\b", r"\bDr\.\s+[A-Z][a-z]+\b"):
        for m in re.finditer(pattern, sentence, re.I):
            mentions.append({
                "raw_place_name": m.group(0),
                "canonical_barangay": None,
                "place_type": "landmark",
                "char_start": sent_offset_start + m.start(),
                "char_end": sent_offset_start + m.end(),
            })

    # List entries may identify flood sites by a local landmark or numbered
    # address instead of a road suffix. Keep the full phrase as a candidate.
    for pattern in (
        r"\b(?:West|W\.?)\s+Riverside\s+Interior\b",
        r"\b(?:[A-Z][\w.-]*\s+){1,4}(?:Cloverleaf|Hilltop|Alley|National High School)\b",
        r"\b(?:[A-Z][\w.-]*\s+){1,3}(?:Junction|Bridge)\b",
        r"\b(?:[A-Z][\w.-]*\s+){1,3}Valley\s+\d+\b",
        r"\b[A-Z]{2,4}\s+Embassy\b",
        r"\b\d{1,3}\s+[A-Z][a-z]{3,}\b",
    ):
        if pattern.startswith(r"\b\d") and not NUMERIC_DEPTH_PATTERN.search(sentence):
            continue
        for match in re.finditer(pattern, sentence):
            raw = match.group(0)
            leading = re.match(r"(?:In|At|On|The)\s+", raw)
            if leading:
                raw = raw[leading.end():]
            mentions.append({
                "raw_place_name": raw,
                "canonical_barangay": None,
                "place_type": "landmark",
                "char_start": sent_offset_start + match.start() + (leading.end() if leading else 0),
                "char_end": sent_offset_start + match.end(),
            })

    # In agency road-status lists, the place before " - " is a site name,
    # even when it has no road suffix. Keep names such as "Espana Antipolo"
    # together rather than resolving Antipolo/Rodriguez as a separate city.
    listed_status = re.match(
        r"^\s*(?:--\s*)?(?P<site>.+?)\s+[-–—]\s+(?P<status>.+)$",
        sentence,
    )
    if listed_status and not sentence.lstrip().startswith("--") and not re.match(
        r"(?:\d|(?:Brgy\.?|Barangay|Bgy\.?)\s)", listed_status.group("site"), re.I,
    ) and re.search(
        r"\b(?:flood(?:ed|ing)?|subsided|deep|inches|passable|level)\b",
        listed_status.group("status"), re.I,
    ):
        site = listed_status.group("site")
        site_start = listed_status.start("site")
        lead = re.match(r"(?:Along|At|On)\s+", site, re.I)
        if lead:
            site_start += lead.end()
            site = site[lead.end():]
        site_end = listed_status.end("site")
        site_mentions = [
            mention for mention in mentions
            if mention["place_type"] in {"street", "landmark"}
            and site_start <= mention["char_start"] - sent_offset_start < site_end
        ]
        first = min(site_mentions, key=lambda mention: mention["char_start"]) if site_mentions else None
        if first and first["char_start"] - sent_offset_start <= site_start + 1:
            first["relation_primary"] = True
            first.setdefault("road_segment_raw", site)
        else:
            mentions.append({
                "raw_place_name": site,
                "canonical_barangay": None,
                "place_type": "street",
                "road_segment_raw": site,
                "listed_road": True,
                "relation_primary": True,
                "char_start": sent_offset_start + site_start,
                "char_end": sent_offset_start + site_end,
            })
        relation_spans.append((sent_offset_start + site_start, sent_offset_start + site_end))

    # Road advisories also list comma-separated names without road suffixes.
    # Preserve each complete list item as bounded evidence rather than losing
    # "Araneta E. Rodriguez" or reducing "EDSA White Plains" to EDSA.
    roads_lead = re.search(r"\bother\s+flooded\s+roads\s+in\s+.+?\s+included\s+", sentence, re.I)
    if roads_lead:
        list_tail = sentence[roads_lead.end():]
        list_tail = re.split(r",\s*all\s+of\s+which\b", list_tail, maxsplit=1, flags=re.I)[0]
        for item in re.finditer(r"[^,]+", list_tail):
            item_text = item.group(0).strip()
            item_text = re.sub(r"^and\s+", "", item_text, flags=re.I)
            if not item_text:
                continue
            item_start = roads_lead.end() + item.start() + item.group(0).find(item_text)
            item_end = item_start + len(item_text)
            contained = [
                mention for mention in mentions
                if mention["place_type"] == "street"
                and item_start <= mention["char_start"] - sent_offset_start < item_end
            ]
            if contained:
                first_road = min(contained, key=lambda mention: mention["char_start"])
                first_road.setdefault("road_segment_raw", item_text)
                near = re.search(r"\bnear\s+(.+)$", item_text, re.I)
                if near:
                    first_road["local_area_raw"] = near.group(1).strip()
            else:
                road_name = re.sub(
                    r"\s+(?:northbound|southbound)(?:\s+and\s+(?:northbound|southbound))?$",
                    "", item_text, flags=re.I,
                )
                mentions.append({
                    "raw_place_name": road_name,
                    "canonical_barangay": None,
                    "place_type": "street",
                    "road_segment_raw": item_text,
                    "listed_road": True,
                    "char_start": sent_offset_start + item_start,
                    "char_end": sent_offset_start + item_start + len(road_name),
                })

    # 3. Nationwide Philippine Cities and Municipalities
    for m in CITY_PATTERN.finditer(sentence):
        if any(start <= m.start() < end for start, end in (
            (agency.start(), agency.end()) for agency in re.finditer(
                r"\b(?:Metropolitan|Metro)\s+Manila\s+Development\s+Authority\b", sentence, re.I,
            )
        )):
            continue
        if m.group(0).lower() == "manila" and sentence[max(0, m.start() - 6):m.start()].lower() == "metro ":
            continue  # Metro Manila names the region, not the City of Manila.
        # A homonymous city inside a road or road-segment name is not an admin mention.
        road_context = sentence[m.end():]
        if re.match(r"\s+Streets?\b", road_context, re.I):
            continue
        mentions.append({
            "raw_place_name": m.group(0),
            "canonical_barangay": None,
            "place_type": "city",
            "char_start": sent_offset_start + m.start(),
            "char_end": sent_offset_start + m.end(),
        })

    # 3b. Dynamic '<Name> City' pattern
    city_suffix_pattern = re.compile(r"\b([A-Z][a-zA-Z\s\.\-]{2,25})\s+City\b", re.I)
    for m in city_suffix_pattern.finditer(sentence):
        full_city_name = m.group(0)
        c_prefix = m.group(1).strip().lower()
        if c_prefix in _loc_service.cities or f"{c_prefix} city" in _loc_service.cities:
            mentions.append({
                "raw_place_name": full_city_name,
                "canonical_barangay": None,
                "place_type": "city",
                "char_start": sent_offset_start + m.start(),
                "char_end": sent_offset_start + m.end(),
            })

    # 3c. Administrative Prefix Pattern: City of / Lungsod ng / Bayan ng / Municipality of
    admin_city_pattern = re.compile(
        r"\b(?:City\s+of|Lungsod\s+ng|Bayan\s+ng|Municipality\s+of)\s+([A-Z][a-zA-Z\s\.\-]{2,25})\b",
        re.I,
    )
    for m in admin_city_pattern.finditer(sentence):
        full_mention = m.group(0)
        target_name = m.group(1).strip().lower()
        if target_name in _loc_service.cities:
            mentions.append({
                "raw_place_name": full_mention,
                "canonical_barangay": None,
                "place_type": "city",
                "char_start": sent_offset_start + m.start(),
                "char_end": sent_offset_start + m.end(),
            })

    # 4. Pasig City general mention
    for m in re.finditer(r"\bPasig(?:\s+City)?\b", sentence, re.I):
        mentions.append({
            "raw_place_name": m.group(0),
            "canonical_barangay": None,
            "place_type": "city",
            "char_start": sent_offset_start + m.start(),
            "char_end": sent_offset_start + m.end(),
        })

    # 4b. All 82 Philippine Provinces
    for m in PROVINCE_PATTERN.finditer(sentence):
        mentions.append({
            "raw_place_name": m.group(0),
            "canonical_barangay": None,
            "place_type": "province",
                "char_start": sent_offset_start + m.start(),
                "char_end": sent_offset_start + m.end(),
            })

    # 5. Pasig Barangays (with or without Barangay/Brgy. prefix, including Sta./Sto. variations)
    barangay_candidates = list(PASIG_BARANGAYS_CANONICAL) + list(BARANGAY_ALIASES.keys())
    for b_name in barangay_candidates:
        pattern = re.compile(r"\b(?:(?:Barangay|Brgy\.?|Bgy\.?)\s+)?" + re.escape(b_name) + r"\b", re.I)
        for m in pattern.finditer(sentence):
            raw = m.group(0)
            canonical = normalize_barangay_name(raw)
            mentions.append({
                "raw_place_name": raw,
                "canonical_barangay": canonical,
                "place_type": "barangay",
                "char_start": sent_offset_start + m.start(),
                "char_end": sent_offset_start + m.end(),
            })

    # 5b. Nationwide Prefixed Barangays outside Pasig (e.g. Brgy. Matina Crossing, Barangay Balibago)
    nationwide_bgy_pattern = re.compile(
        r"\b(?:Barangay|Brgy\.?|Bgy\.?)\s+([A-Z][a-zA-Z0-9\.\']*(?:\s+(?:del\s+|de\s+|la\s+)?[A-Z0-9][a-zA-Z0-9\.\']*){0,3})\b"
    )
    for m in nationwide_bgy_pattern.finditer(sentence):
        full_raw = m.group(0)
        candidate = m.group(1).strip()
        words = candidate.split()
        found_candidate = None
        for i in range(len(words), 0, -1):
            sub_cand = " ".join(words[:i])
            if sub_cand.lower() in _loc_service.barangays or _loc_service.normalize_barangay_name(sub_cand, city_context=None):
                found_candidate = sub_cand
                break

        if found_candidate:
            canonical = _loc_service.normalize_barangay_name(found_candidate, city_context=None)
            if not canonical:
                b_entries = _loc_service.barangays.get(found_candidate.lower(), [])
                canonical = b_entries[0]["name"] if b_entries else found_candidate

            match_start = sent_offset_start + m.start()
            prefix_len = len(full_raw) - len(candidate)
            actual_end = match_start + prefix_len + len(found_candidate)
            actual_raw = sentence[m.start() : m.start() + prefix_len + len(found_candidate)]

            mentions.append({
                "raw_place_name": actual_raw,
                "canonical_barangay": canonical,
                "place_type": "barangay",
                "char_start": match_start,
                "char_end": actual_end,
            })

    # Also search for Sta. and Sto. patterns specifically: Sta. Rosa, Sto. Tomas, Sta. Lucia, Sta. Cruz
    for saint_pattern in (r"\b(?:Brgy\.?\s+)?(?:Sta\.?|Sto\.?)\s+[A-Z][a-z]+\b",):
        for m in re.finditer(saint_pattern, sentence, re.I):
            raw = m.group(0)
            canonical = normalize_barangay_name(raw)
            if canonical:
                mentions.append({
                    "raw_place_name": raw,
                    "canonical_barangay": canonical,
                    "place_type": "barangay",
                    "char_start": sent_offset_start + m.start(),
                    "char_end": sent_offset_start + m.end(),
                })

    # Deduplicate overlapping spans (prefer longer match)
    mentions.sort(key=lambda x: (x["char_start"], -(x["char_end"] - x["char_start"])))
    unique_mentions: list[dict[str, Any]] = []
    last_end = -1
    for m in mentions:
        if not m.get("relation_primary"):
            if any(start <= m["char_start"] < end for start, end in relation_spans):
                continue
        local_start = m["char_start"] - sent_offset_start
        if re.search(r"\bnear\s+$", sentence[:local_start], re.I):
            continue
        if m["char_start"] >= last_end:
            unique_mentions.append(m)
            last_end = m["char_end"]

    return unique_mentions


def extract_depth_from_text(text: str) -> tuple[str | None, CanonicalDepth | None, str | None, list[str]]:
    """Extract depth raw phrase and map to canonical gauge keys.
    Returns (depth_raw, depth_canonical, depth_rule, uncertainty_reasons).
    """
    reasons: list[str] = []

    # A measured value is stronger evidence than a body-part adjective. Only
    # assign a gauge key for an exact configured gauge value; retain all others.
    depth_range = NUMERIC_DEPTH_RANGE_PATTERN.search(text)
    if depth_range:
        return depth_range.group(0), None, "numeric_depth_range", ["depth_range_not_point_value"]
    numeric = NUMERIC_DEPTH_PATTERN.search(text)
    if numeric:
        qualifier_match = re.search(
            r"\b(about|around|approximately|roughly|up to|as high as)\s+$",
            text[max(0, numeric.start() - 22):numeric.start()], re.I,
        )
        qualifier = qualifier_match.group(1).lower() if qualifier_match else None
        raw_start = numeric.start() - len(qualifier_match.group(0)) if qualifier_match else numeric.start()
        numeric_raw = text[raw_start:numeric.end()]
        if qualifier in ("up to", "as high as"):
            reasons.append("upper_bound_depth")
        elif qualifier:
            reasons.append("approximate_depth")
        value = float(numeric.group("value"))
        unit = numeric.group("unit").lower()
        inches = value if unit.startswith("in") else (value / 2.54 if unit.startswith("centimeter") or unit == "cm" else (value * 39.37007874 if unit.startswith("meter") or unit == "m" else value * 12))
        for key in FLOOD_DEPTH_SEVERITIES:
            gauge = get_flood_depth_measurement(key)
            if gauge and abs(inches - gauge.inches) < 0.05:
                return numeric_raw, key, "numeric_gauge_match", reasons
        return numeric_raw, None, "numeric_depth_without_exact_gauge", reasons + ["numeric_depth_not_canonical"]

    # 1. Collect all canonical matches
    raw_matches: list[tuple[int, int, str, CanonicalDepth, str]] = []
    for canon_key, pattern, rule_name in DEPTH_RULES:
        for m in pattern.finditer(text):
            raw_matches.append((m.start(), m.end(), m.group(0), canon_key, rule_name))

    # Deduplicate overlapping spans (prefer longer span, e.g. "Lampas sakong" over "sakong")
    raw_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    matches: list[tuple[int, int, str, CanonicalDepth, str]] = []
    last_end = -1
    for m in raw_matches:
        if m[0] >= last_end:
            matches.append(m)
            last_end = m[1]

    if matches:
        # If any match is preceded by "naging" (became) or "down to", prefer that current state
        for start, end, raw, canon_key, rule_name in matches:
            prefix = text[max(0, start - 15) : start].lower()
            if "naging" in prefix or "down to" in prefix:
                return raw, canon_key, rule_name, reasons
        # If any match is preceded by "mula" (from), avoid selecting it if another match exists
        non_mula = [
            m for m in matches
            if "mula" not in text[max(0, m[0] - 15) : m[0]].lower()
        ]
        chosen = non_mula[-1] if non_mula else matches[-1]
        return chosen[2], chosen[3], chosen[4], reasons

    # 2. Check ambiguous or unmapped depths
    m_ambig = AMBIGUOUS_DEPTH_PATTERN.search(text)
    if m_ambig:
        raw = m_ambig.group(0)
        reasons.append("ambiguous_depth")
        return raw, None, "unsupported_or_ambiguous_scale", reasons

    return None, None, None, reasons


def extract_condition_from_text(text: str, has_active_flood: bool, is_negated: bool) -> FloodCondition:
    """Determine flood condition: active, rising, receding, subsided, or unknown."""
    if is_negated:
        if "clear" in text.lower() or "humupa" in text.lower() or "wala nang baha" in text.lower():
            return "subsided"
        return "unknown"

    if CONDITION_RISING.search(text):
        return "rising"
    if CONDITION_RECEDING.search(text):
        return "receding"
    if CONDITION_SUBSIDED.search(text):
        return "subsided"
    if has_active_flood or _has_flood_evidence_word(text):
        return "active"
    return "unknown"


def extract_event_time_from_text(text: str) -> tuple[str | None, datetime | None]:
    """Extract explicit event time string."""
    m = TIME_EXPRESSIONS.search(text)
    if m:
        raw = m.group(0)
        if m.end() < len(text) and text[m.end()] == "." and re.search(r"[ap]\.m$", raw, re.I):
            raw += "."
        return raw, None
    return None, None


def resolve_observation_time(raw: str | None, context: str, published_at: datetime | None,
                             event_day: datetime | None = None) -> datetime | None:
    """Anchor an explicit flood observation clock only to a nearby publication time."""
    if not raw or published_at is None or published_at.tzinfo is None or published_at.utcoffset() is None:
        return None
    match = OBSERVATION_CLOCK.fullmatch(raw.strip())
    if not match or EXPLICIT_OTHER_DATE.search(context):
        return None
    hour, minute = int(match.group(1)), int(match.group(2) or "0")
    if not 1 <= hour <= 12 or minute > 59:
        return None
    hour = (hour % 12) + (12 if match.group(3).casefold() == "p" else 0)
    published_local = published_at.astimezone(PHILIPPINE_TIMEZONE)
    if event_day is not None:
        observed_local = event_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return observed_local if timedelta(0) <= published_local - observed_local <= timedelta(hours=36) else None
    observed_local = published_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if observed_local > published_local:
        observed_local -= timedelta(days=1)
    if published_local - observed_local > timedelta(hours=12):
        return None
    return observed_local


def article_weekday_event_day(article: NewsArticleExtractorInput) -> datetime | None:
    """Resolve a sole recent weekday explicitly attached to observed flooding.

    Publication is only a calendar anchor. No fetched/current date is used;
    ambiguous dates and reports more than 36 hours after the event stay unknown.
    """
    from app.services.news_evidence_policy import has_flood_observation

    publication = article.published_at
    if publication is None or publication.tzinfo is None:
        return None
    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    found: set[int] = set()
    for sentence, _, _ in split_sentences_with_offsets(article.article_text or ""):
        if (not has_flood_observation(sentence) or PHOTO_CREDIT.search(sentence)
                or FORECAST_PATTERNS.search(sentence) or HISTORICAL_PATTERNS.search(sentence)):
            continue
        without_weekdays = re.sub(r"\b(?:on\s+)?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
                                  "", sentence, flags=re.I)
        if EXPLICIT_OTHER_DATE.search(without_weekdays):
            return None  # An explicit date/relative day needs its own resolver.
        for match in re.finditer(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
                                r"(?:morning|afternoon|evening|night)\b", sentence, re.I):
            found.add(weekdays.index(match.group(1).lower()))
    if len(found) != 1:
        return None
    local = publication.astimezone(PHILIPPINE_TIMEZONE)
    day = local - timedelta(days=(local.weekday() - next(iter(found))) % 7)
    return day.replace(hour=0, minute=0, second=0, microsecond=0)


def split_clauses(sentence: str) -> list[tuple[str, int, int]]:
    """Split a sentence on contrasting or sequential conjunctions (habang, pero, whereas, etc.)."""
    clause_delimiters = re.compile(r"\b(?:habang|pero|samantala|whereas|while|meanwhile)\b|;", re.I)
    matches = list(clause_delimiters.finditer(sentence))
    if not matches:
        return [(sentence, 0, len(sentence))]

    clauses: list[tuple[str, int, int]] = []
    last_idx = 0
    for match in matches:
        clause_text = sentence[last_idx : match.start()].strip()
        if clause_text:
            clauses.append((clause_text, last_idx, match.start()))
        last_idx = match.start()
    clause_text = sentence[last_idx:].strip()
    if clause_text:
        clauses.append((clause_text, last_idx, len(sentence)))
    return clauses


def extract_claims_from_sentence(
    sentence: str,
    sent_start: int,
    sent_end: int,
    article_input: NewsArticleExtractorInput,
    inherited_depth_raw: str | None = None,
    inherited_passability: str | None = None,
    section_city: str | None = None,
    section_barangay: str | None = None,
    section_time_raw: str | None = None,
    section_flood_reported: bool = False,
    section_time_context: str | None = None,
    event_day: datetime | None = None,
) -> list[ExtractedClaim]:
    """Extract structured claims from a single sentence, associating facts per clause/place."""
    claims: list[ExtractedClaim] = []
    if _is_flood_control_only(sentence):
        return claims
    place_mentions = find_place_mentions(sentence, sent_start)
    dateline = ARTICLE_DATELINE.match(sentence)
    if dateline:
        place_mentions = [
            place for place in place_mentions
            if place["char_start"] - sent_start >= dateline.end()
        ]
    if not place_mentions:
        return claims

    sentence_cities = [p for p in place_mentions if p["place_type"] == "city"]
    title_cities = find_place_mentions(article_input.title, 0)
    title_city_mentions = [p for p in title_cities if p["place_type"] == "city"]
    # A sentence can report separate sites from separate cities. Keep each
    # site's city inside its local coordinated phrase (for example,
    # "Barangay Plainview, Mandaluyong City, as well as Caruncho Avenue,
    # Pasig City"). If several cities remain in one phrase, do not guess.
    city_scope_ranges: list[tuple[int, int]] = []
    if len(sentence_cities) > 1:
        scope_start = 0
        for separator in re.finditer(r";|\b(?:as\s+well\s+as|while|whereas|but|and)\b", sentence, re.I):
            city_scope_ranges.append((scope_start, separator.start()))
            scope_start = separator.end()
        city_scope_ranges.append((scope_start, len(sentence)))
    else:
        city_scope_ranges.append((0, len(sentence)))

    def city_context_for(place_start: int) -> tuple[str | None, bool]:
        """Resolve only an unambiguous local city; return ambiguity separately."""
        scope = next(
            ((start, end) for start, end in city_scope_ranges if start <= place_start <= end),
            (0, len(sentence)),
        )
        local_cities = [
            city for city in sentence_cities
            if scope[0] <= city["char_start"] - sent_start < scope[1]
        ]
        if len(local_cities) == 1:
            return local_cities[0]["raw_place_name"], False
        if len(local_cities) > 1 or len(sentence_cities) > 1:
            return None, True
        if section_city:
            return section_city, False
        if len(title_city_mentions) == 1:
            return title_city_mentions[0]["raw_place_name"], False
        return None, False

    def barangay_context_for(place_start: int, city_lookup: str | None) -> str | None:
        """Attach a sole local barangay only when it belongs to this city scope."""
        scope = next(
            ((start, end) for start, end in city_scope_ranges if start <= place_start <= end),
            (0, len(sentence)),
        )
        local_barangays = [
            candidate for candidate in place_mentions
            if candidate["place_type"] == "barangay"
            and scope[0] <= candidate["char_start"] - sent_start < scope[1]
        ]
        if len(local_barangays) != 1:
            return None
        raw = local_barangays[0]["raw_place_name"]
        raw = re.sub(r"^(?:Barangay|Brgy\.?)\s+", "", raw, flags=re.I).strip()
        if not city_lookup:
            return None
        return _loc_service.normalize_barangay_name(raw, city_context=city_lookup) or raw

    inline_barangay = re.match(r"^\s*(?:Brgy\.?|Barangay)\s+([A-Za-zÀ-ÿ. ]+?)(?=\s*[,(-]|$)", sentence, re.I)
    effective_barangay = inline_barangay.group(1).strip() if inline_barangay else section_barangay

    # Break sentence into clauses for fine-grained multi-location attribution
    clauses = split_clauses(sentence)
    road_segment_match = ROAD_SEGMENT_PATTERN.search(sentence)
    nearby_sites: dict[int, tuple[str, int, int]] = {}
    for candidate in place_mentions:
        if candidate["place_type"] != "street" or candidate.get("road_segment_raw"):
            continue
        candidate_end = candidate["char_end"] - sent_start
        site_match = re.match(
            r"(?:\s*\.?\s*(?:NB|SB)?\s*[-–]\s*|\s*\.?\s*\(\s*|\s*\.\s+)"
            r"(?P<site>[A-Z][\wÀ-ÿ.-]*(?:\s+(?:[A-Z0-9][\wÀ-ÿ.-]*)){0,4})",
            sentence[candidate_end:],
        )
        if not site_match:
            continue
        site = site_match.group("site").strip().rstrip(".,-")
        if not site or site.lower() in {"the", "a", "an", "and", "while"}:
            continue
        site_start = candidate_end + site_match.start("site")
        site_end = site_start + len(site)
        if "(" in site_match.group(0) and site_end < len(sentence) and sentence[site_end] == ")":
            site_end += 1
        nearby_sites[candidate["char_start"]] = (site, site_start, site_end)

    for place in place_mentions:
        local_place_start = place["char_start"] - sent_start
        local_place_end = place["char_end"] - sent_start
        if any(
            site_start <= local_place_start < site_end
            for site, site_start, site_end in nearby_sites.values()
        ):
            continue  # The crossing road/landmark is attached to its main road.
        if place["place_type"] == "barangay" and any(
            other["place_type"] in {"street", "landmark"} for other in place_mentions
        ) and not sentence[:local_place_start].strip() and re.match(
            r"\s*(?:\([^)]*\))?\s*,", sentence[local_place_end:]
        ):
            continue  # The leading barangay qualifies the following road/site.
        city_lookup, city_context_ambiguous = city_context_for(local_place_start)
        if city_lookup and city_lookup.casefold() == "maynila":
            city_lookup = "Manila"
        scoped_barangay = barangay_context_for(local_place_start, city_lookup)
        city_res = _loc_service.resolve_location_hierarchy(city_lookup) if city_lookup else None
        directional_suffix = re.match(
            r"\s+(?:northbound|southbound)(?:\s+and\s+(?:northbound|southbound))?\b",
            sentence[local_place_end:], re.I,
        )
        local_area_match = re.match(
            r"\s+in\s+((?:Sitio\s+\d+)|(?:[A-Z][\wÀ-ÿ.-]*(?:\s+[A-Z][\wÀ-ÿ.-]*){0,2}))\b",
            sentence[local_place_end:],
        )
        local_area_raw = (
            place.get("local_area_raw")
            or (local_area_match.group(1) if local_area_match else None)
            or (nearby_sites[place["char_start"]][0] if place["char_start"] in nearby_sites else None)
            or (scoped_barangay if place["place_type"] in ("street", "landmark") else None)
            or (effective_barangay if place["place_type"] in ("street", "landmark") else None)
        )
        target_clause_text = sentence
        for clause_text, c_start, c_end in clauses:
            if c_start <= local_place_start < c_end:
                target_clause_text = clause_text
                break

        if _is_flood_control_only(target_clause_text):
            continue

        # Check negation in the clause
        clause_negated = bool(NEGATION_PATTERNS.search(target_clause_text))
        is_forecast = bool(FORECAST_PATTERNS.search(target_clause_text) or FORECAST_PATTERNS.search(sentence)
            or re.search(HYPOTHETICAL_FLOOD_PATTERN, target_clause_text, re.I))
        if is_forecast and re.search(
            r"\b(?:flooding|floodwaters?|baha)\s+(?:was|were|is|are)\s+(?:also\s+)?(?:reported|recorded|observed)\b",
            target_clause_text, re.I,
        ):
            is_forecast = False  # A past advisory can describe a measured flood.
        is_historical = bool(HISTORICAL_PATTERNS.search(target_clause_text) or HISTORICAL_PATTERNS.search(sentence))

        uncertainties: list[str] = []
        if city_context_ambiguous and place["place_type"] in {"street", "landmark", "barangay"}:
            uncertainties.append("city_context_ambiguous")
        if clause_negated:
            flood_mentioned = False
            uncertainties.append("negated_flood_report")
        elif is_forecast:
            flood_mentioned = False
            uncertainties.append("forecast_or_warning_only")
        elif is_historical:
            flood_mentioned = False
            uncertainties.append("historical_reference_only")
        else:
            flood_mentioned = bool(
                _has_flood_evidence_word(target_clause_text)
                or _has_flood_evidence_word(sentence)
                or section_flood_reported
            )

        # Depth extraction (prefer target clause, fallback to sentence if only one place)
        d_raw, d_canon, d_rule, d_reasons = extract_depth_from_text(target_clause_text)
        if not d_raw and len(place_mentions) == 1:
            d_raw, d_canon, d_rule, d_reasons = extract_depth_from_text(sentence)
        if not d_raw and inherited_depth_raw:
            d_raw, d_canon, d_rule = inherited_depth_raw, None, "inherited_group_depth_range"
            d_reasons = ["shared_depth_range_not_individual_measurement"]
        uncertainties.extend(d_reasons)
        if place.get("local_area_raw"):
            uncertainties.append("listed_road_requires_geometry_check")
        if place.get("unnamed_street_area"):
            uncertainties.append("unnamed_street_in_barangay")

        road_passability = "unknown"
        if re.search(r"\b(?:not passable to (?:all|any)(?: kinds? of| types? of)? vehicles?|no longer passable to vehicles?|impassable to all(?: types? of)? vehicles?)\b", target_clause_text, re.I):
            road_passability = "impassable_all"
        elif re.search(r"\b(?:closed to (?:light|small) vehicles|not passable to (?:light|small) vehicles|hindi na passable sa mga maliliit na sasakyan)\b", target_clause_text, re.I):
            road_passability = "light_vehicle_closed"
        elif re.search(r"\bpassable to all(?: types of)? vehicles\b", target_clause_text, re.I):
            road_passability = "passable_all"
        elif inherited_passability:
            road_passability = inherited_passability

        # If explicit depth is present and not negated/forecast/historical, flood is mentioned!
        if d_raw and not clause_negated and not is_forecast and not is_historical:
            flood_mentioned = True

        # Condition
        condition = extract_condition_from_text(target_clause_text, flood_mentioned, clause_negated)
        if condition == "unknown" and len(place_mentions) == 1:
            condition = extract_condition_from_text(sentence, flood_mentioned, clause_negated)

        # Event time
        time_context = target_clause_text
        t_raw, t_res = extract_event_time_from_text(target_clause_text)
        if not t_raw:
            t_raw, t_res = extract_event_time_from_text(sentence)
            time_context = sentence
        has_listed_time = False
        if not t_raw:
            listed_time = re.match(
                r"^\s*(?:--|[-–•])\s*(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)\b",
                sentence, re.I,
            )
            if listed_time:
                t_raw = listed_time.group(1)
                has_listed_time = True
        if not t_raw and section_time_raw:
            t_raw = section_time_raw
            time_context = section_time_context or sentence

        if not t_raw:
            uncertainties.append("event_time_unknown")
        time_kind = "unspecified"
        if t_raw and (t_raw.lower().startswith("as of") or (
                t_raw.lower().startswith("by ") and condition == "subsided")):
            time_kind = "observation"
        elif has_listed_time:
            time_kind = "report"
        elif t_raw and re.search(r"\breported\b", target_clause_text, re.I):
            time_kind = "report"
        if time_kind == "observation":
            t_res = resolve_observation_time(t_raw, time_context, article_input.published_at, event_day)

        depth_meas = get_flood_depth_measurement(d_canon) if d_canon else None

        # Resolve geographic hierarchy
        hierarchy_context = (
            f"{sentence} {city_res['city_municipality']}"
            if city_res and city_res.get("city_municipality") else sentence
        )
        lookup_name = place["raw_place_name"]
        if place["place_type"] == "barangay" and city_res:
            normalized_name = _loc_service.normalize_barangay_name(
                lookup_name, city_context=city_res.get("city_municipality"),
            )
            if normalized_name:
                lookup_name = f"Barangay {normalized_name}"
        res = _loc_service.resolve_location_hierarchy(lookup_name, text_context=hierarchy_context)
        if (place["place_type"] == "barangay" and city_res and res
                and res.get("city_municipality") != city_res.get("city_municipality")):
            res = None
            uncertainties.append("barangay_parent_mismatch")
        if place.get("unnamed_street_area"):
            area_key = place["raw_place_name"].lower().replace("‑", "-")
            matches = _loc_service.barangays.get(area_key, [])
            city_name = city_res.get("city_municipality", "").lower() if city_res else ""
            matching_area = next((entry for entry in matches if entry.get("city_municipality", "").lower() == city_name), None)
            res = ({
                "matched_name": matching_area["name"],
                "level": "Bgy",
                "psgc_code": matching_area["psgc_code"],
                "province": matching_area.get("province"),
                "city_municipality": matching_area["city_municipality"],
                "region": matching_area.get("region"),
            } if matching_area else None)

        canonical_bgy = place["canonical_barangay"] if place["place_type"] == "barangay" and res else None
        if place["place_type"] == "barangay" and res and res.get("level") == "Bgy":
            canonical_bgy = res.get("matched_name")
        if not canonical_bgy and place["place_type"] in ("street", "landmark"):
            canonical_bgy = _loc_service.normalize_barangay_name(
                local_area_raw or effective_barangay,
                city_context=city_res.get("city_municipality") if city_res else None,
            )
        canonical_city = None
        canonical_prov = None
        canonical_rd = None
        psgc = None
        island = None

        if res:
            psgc = res.get("psgc_code")
            canonical_prov = res.get("province")
            canonical_city = res.get("city_municipality")
            reg = str(res.get("region", "")).lower()
            island = get_island_group_for_region(reg)
            if place["place_type"] == "barangay" and not canonical_bgy and res.get("level") == "Bgy":
                canonical_bgy = res.get("matched_name")
        elif place["place_type"] == "barangay" and city_res:
            canonical_city = city_res.get("city_municipality")
            canonical_prov = city_res.get("province")
            island = get_island_group_for_region(city_res.get("region"))
            uncertainties.append("barangay_unverified")
        elif place["place_type"] == "barangay" and canonical_bgy:
            # Pasig canonical barangay default
            canonical_city = "City of Pasig"
            canonical_prov = "NCR, Second District"
            island = "Luzon"
        elif place.get("unnamed_street_area") and city_res:
            canonical_city = city_res.get("city_municipality")
            canonical_prov = city_res.get("province")
            island = get_island_group_for_region(city_res.get("region"))
            uncertainties.append("barangay_unverified")

        if place["place_type"] in ("street", "landmark"):
            if place["place_type"] == "street":
                canonical_rd = place["raw_place_name"]
            if city_res and city_res.get("city_municipality"):
                canonical_city = city_res["city_municipality"]
                canonical_prov = city_res.get("province")
                island = get_island_group_for_region(city_res.get("region"))
                # Resolving a road's raw name as a homonymous barangay/town
                # cannot override its explicit parent city (e.g. Roxas Blvd
                # in Manila). PSGC identifies that city, not the road itself.
                psgc = city_res.get("psgc_code")
        elif place["place_type"] == "city" and not canonical_city:
            canonical_city = city_res.get("city_municipality") if city_res else place["raw_place_name"]
        elif place["place_type"] == "province" and not canonical_prov:
            canonical_prov = place["raw_place_name"]

        confidence = 0.90 if canonical_bgy or place["place_type"] in ("street", "landmark") else (0.75 if place["place_type"] == "city" else 0.65)
        if place.get("local_area_raw") or place.get("listed_road"):
            confidence = 0.50
        if place.get("unnamed_street_area"):
            confidence = 0.35

        claim = ExtractedClaim(
            raw_place_name=place["raw_place_name"],
            canonical_barangay=canonical_bgy,
            canonical_city=canonical_city,
            canonical_province=canonical_prov,
            canonical_road=canonical_rd,
            local_area_raw=local_area_raw,
            road_segment_raw=(
                place.get("road_segment_raw") or (
                    sentence[local_place_start:nearby_sites[place["char_start"]][2]]
                    if place["char_start"] in nearby_sites else None
                ) or (
                    sentence[local_place_start:local_place_end] + directional_suffix.group(0)
                    if directional_suffix and place["place_type"] in {"street", "landmark"} else None
                ) or (road_segment_match.group(0)
                if canonical_rd and road_segment_match
                and re.fullmatch(r"\s*", sentence[local_place_end:road_segment_match.start()])
                else None)
            ),
            island_group=island,
            psgc_code=psgc,
            place_type=place["place_type"],
            place_char_start=place["char_start"],
            place_char_end=place["char_end"],
            flood_mentioned=flood_mentioned,
            is_negated=clause_negated,
            is_forecast=is_forecast,
            is_historical=is_historical,
            road_passability=road_passability,
            depth_raw=d_raw,
            depth_canonical=d_canon,
            depth_rule=d_rule,
            depth_meters=depth_meas.meters if depth_meas else None,
            depth_inches=depth_meas.inches if depth_meas else None,
            depth_formatted=depth_meas.formatted if depth_meas else None,
            condition=condition,
            event_time_raw=t_raw,
            event_time_resolved=t_res,
            event_time_kind=time_kind,
            evidence_sentence=sentence,
            evidence_sentence_offset=(sent_start, sent_end),
            uncertainty_reasons=uncertainties,
            confidence_score=confidence,
        )
        # Preserve the reported carriageway alongside its intersection rather
        # than treating the opposite direction as an affected road.
        if claim.road_segment_raw:
            direction_prefix = re.search(
                r"\b(?:(?:northbound|southbound|eastbound|westbound)(?:\s+and\s+"
                r"(?:northbound|southbound|eastbound|westbound))?\s+lanes?\s+of)\s+$",
                sentence[:local_place_start], re.I,
            )
            if direction_prefix:
                claim.road_segment_raw = direction_prefix.group(0) + claim.road_segment_raw
        # Administrative names attached to a road are retained for provenance,
        # but are not additional flooded sites. Standalone city reports remain
        # observations, as do separately coordinated cities without a road.
        if place["place_type"] == "city":
            scope_start, scope_end = next(
                ((start, end) for start, end in city_scope_ranges
                 if start <= local_place_start <= end), (0, len(sentence)),
            )
            if any(other["place_type"] in {"street", "landmark"}
                   and scope_start <= other["char_start"] - sent_start < scope_end
                   for other in place_mentions):
                claim.flood_mentioned = False
                claim.uncertainty_reasons.append("location_context_only")
        elif place["place_type"] == "landmark" and any(
            other["place_type"] == "street" and re.match(
                r"\s+in\s+" + re.escape(place["raw_place_name"]) + r"\b",
                sentence[other["char_end"] - sent_start:], re.I,
            ) for other in place_mentions
        ):
            claim.flood_mentioned = False
            claim.uncertainty_reasons.append("location_context_only")
        if place.get("listed_road") and local_area_raw and " and " in local_area_raw:
            for area_name in local_area_raw.split(" and "):
                claims.append(claim.model_copy(update={"local_area_raw": area_name}))
        else:
            claims.append(claim)

    return claims


def mark_contradictory_updates(claims: list[ExtractedClaim]) -> None:
    """Flag active and cleared claims for the same bounded place.

    Publishers may put the latest update before the older report. Article
    order alone cannot establish observation time, so both claims keep their
    original evidence and require a human to reconcile the update.
    """
    def plain(value: str) -> str:
        return "".join(
            char for char in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(char)
        )

    by_place: dict[tuple[str, str, str], list[ExtractedClaim]] = {}
    for claim in claims:
        if claim.place_type not in {"street", "landmark"}:
            continue
        key = (
            plain(claim.canonical_city or ""),
            plain(claim.raw_place_name),
            plain(claim.road_segment_raw or claim.local_area_raw or ""),
        )
        if not key[0]:
            continue
        by_place.setdefault(key, []).append(claim)
    for place_claims in by_place.values():
        has_active = any(c.condition in {"active", "rising"} and c.flood_mentioned for c in place_claims)
        has_cleared = any(c.condition == "subsided" or c.is_negated for c in place_claims)
        if has_active and has_cleared:
            for claim in place_claims:
                if "contradictory_update" not in claim.uncertainty_reasons:
                    claim.uncertainty_reasons.append("contradictory_update")

def mark_city_summaries_as_context(claims: list[ExtractedClaim]) -> None:
    """Keep broad city evidence without counting it again as a flood site.

    Only specific observations from this article in the same resolved city
    qualify. Preserve distinct explicit observation times and do not promote
    speculative, caption-only or ambiguous places into replacements.
    """
    from app.services.news_evidence_policy import has_flood_observation, non_observation_only

    def observation(claim: ExtractedClaim) -> bool:
        return (claim.flood_mentioned and not (claim.is_forecast or claim.is_negated or claim.is_historical)
                and not set(claim.uncertainty_reasons).intersection({
                    "location_context_only", "photo_caption_only", "city_context_ambiguous",
                    "metadata_only_lead", "contradictory_update",
                })
                and has_flood_observation(claim.evidence_sentence)
                and not non_observation_only(claim.evidence_sentence))

    by_city: dict[str, list[ExtractedClaim]] = {}
    for claim in claims:
        if (claim.place_type in {"street", "landmark", "barangay"}
                and claim.canonical_city and observation(claim)):
            by_city.setdefault(claim.canonical_city.strip().casefold(), []).append(claim)
    for claim in claims:
        if claim.place_type != "city" or not claim.canonical_city or not observation(claim):
            continue
        for specific in by_city.get(claim.canonical_city.strip().casefold(), []):
            if (claim.event_time_resolved is not None and specific.event_time_resolved is not None
                    and claim.event_time_resolved != specific.event_time_resolved):
                continue
            claim.uncertainty_reasons.append("location_context_only")
            claim.flood_mentioned = False
            break


def extract_taglish_flood_facts(article_input: NewsArticleExtractorInput) -> NewsExtractionResult:
    """Execute evidence-linked Taglish extraction on an article.
    Handles full text when present, or marks metadata-only leads when absent.
    """
    from app.services.news_evidence_policy import has_flood_observation

    has_full_text = bool(article_input.article_text and article_input.article_text.strip())
    is_metadata_only = not has_full_text

    text_to_process = (
        article_input.article_text.strip()
        if has_full_text
        else f"{article_input.title}. {article_input.excerpt}".strip()
    )

    sentences = split_sentences_with_offsets(text_to_process)
    event_day = article_weekday_event_day(article_input)
    all_claims: list[ExtractedClaim] = []
    previous_claims: list[ExtractedClaim] = []
    previous_sentence = ""
    section_city: str | None = None
    section_barangay: str | None = None
    section_passability: str | None = None
    section_time_raw: str | None = None
    section_time_context: str | None = None
    section_flood_reported = False
    section_list_mode = False

    dateline_start = next(
        (start for sentence, start, _ in sentences if start < 1500 and ARTICLE_DATELINE.match(sentence)),
        None,
    )
    for sent_text, sent_start, sent_end in sentences:
        if has_full_text and dateline_start is not None and sent_start < dateline_start:
            if _has_flood_evidence_word(sent_text) and not PHOTO_CREDIT.search(sent_text):
                caption_claims = extract_claims_from_sentence(
                    sent_text, sent_start, sent_end, article_input,
                )
                for claim in caption_claims:
                    if claim.place_type in {"street", "landmark"}:
                        claim.uncertainty_reasons.append("photo_caption_only")
                        all_claims.append(claim)
            continue
        if PHOTO_CREDIT.search(sent_text):
            continue
        if _is_flood_control_only(sent_text):
            continue
        if WEATHER_ONLY.search(sent_text) and not _has_flood_evidence_word(sent_text):
            continue
        heading = sent_text.strip().rstrip(".").strip()
        heading_city = _loc_service.resolve_location_hierarchy(heading)
        is_city_heading = bool(heading_city and heading_city.get("level") in {"City", "Mun"})
        is_list_intro = bool(re.search(
            r"\b(?:following\s+(?:road\s+status|routes|areas)|list\s+of\s+roads)\b",
            sent_text, re.I,
        ))
        is_list_entry = bool(
            sent_text.lstrip().startswith("--")
            or (
                re.match(r"^\s*.+?\s+[-–—]\s+.+$", sent_text)
                and re.search(r"\b(?:subsided|deep|passable|level|inches|flooded)\b", sent_text, re.I)
            )
            or (
                section_list_mode and len(sent_text) < 130
                and not re.match(r"^(?:In\s|As\s+of\s|Earlier\b|The\s|At\s|According\b)", sent_text, re.I)
                and any(p["place_type"] in {"street", "landmark"} for p in find_place_mentions(sent_text, sent_start))
            )
        )
        is_list_heading = bool(re.fullmatch(
            r"(?:Impassable to (?:all|light)(?: types of)? vehicles|Passable with caution|Gutter-deep|"
            r"(?:Brgy\.?|Barangay)\s+[A-Za-zÀ-ÿ. ]+(?:\s*\([A-Za-zÀ-ÿ. ]+\))?)", heading, re.I,
        ))
        if is_list_intro:
            section_list_mode = True
            section_city = None
            section_barangay = None
            observed_time, _ = extract_event_time_from_text(sent_text)
            section_time_raw = observed_time
            section_time_context = sent_text if observed_time else None
        elif section_list_mode and not (is_list_entry or is_city_heading or is_list_heading):
            section_list_mode = False
            section_city = None
            section_barangay = None
            section_passability = None
            section_time_raw = None
            section_time_context = None
            section_flood_reported = False
        if (re.search(r"\bflood(?:ing|waters?|ed)?\b", sent_text, re.I)
                and _has_flood_evidence_word(sent_text)) and not any(
            place["place_type"] in {"street", "landmark"}
            for place in find_place_mentions(sent_text, sent_start)
        ):
            observed_time, _ = extract_event_time_from_text(sent_text)
            if observed_time and observed_time.lower().startswith("as of"):
                section_time_raw = observed_time
                section_time_context = sent_text
                if re.search(r"\b(?:reported|affected|following|several)\b", sent_text, re.I):
                    section_flood_reported = True
            if re.search(r"\ball passable\b", sent_text, re.I):
                section_passability = "passable_all"
        if re.fullmatch(r"Impassable to all(?: types of)? vehicles", heading, re.I):
            section_passability = "impassable_all"
            continue
        if re.fullmatch(r"Impassable to light vehicles", heading, re.I):
            section_passability = "light_vehicle_closed"
            continue
        if re.fullmatch(r"Passable with caution", heading, re.I):
            section_passability = "passable_all"
            continue
        if is_city_heading:
            section_city = heading
            section_barangay = None
            continue
        city_intro = re.match(r"^In\s+([A-Z][A-Za-zÀ-ÿ ]{1,30}?),\s", sent_text)
        if city_intro:
            intro_location = _loc_service.resolve_location_hierarchy(city_intro.group(1))
            if intro_location and intro_location.get("level") in {"City", "Mun"}:
                section_city = city_intro.group(1)
                section_barangay = None
        # Narrative updates can introduce their city at the end of a sentence,
        # e.g. "floodwaters receded ... Quezon City". A following road update
        # belongs to that sole explicit city, not an earlier "In Manila".
        if not section_list_mode and has_flood_observation(sent_text):
            narrative_cities = [p for p in find_place_mentions(sent_text, sent_start)
                                if p["place_type"] == "city"]
            if len(narrative_cities) == 1 and not (
                FORECAST_PATTERNS.search(sent_text) or HISTORICAL_PATTERNS.search(sent_text)
            ):
                section_city = narrative_cities[0]["raw_place_name"]
                section_barangay = None
            elif len(narrative_cities) > 1:
                section_city = None
                section_barangay = None
        barangay_heading = (
            re.fullmatch(r"(?:Brgy\.?|Barangay)\s+([A-Za-zÀ-ÿ. ]+?)(?:\s*\([A-Za-zÀ-ÿ. ]+\))?", heading, re.I)
            if not re.search(r"[,\d-]|\b(?:cor\.?|corner|from)\b", heading, re.I)
            else None
        )
        if barangay_heading:
            section_barangay = barangay_heading.group(1)
            continue
        inherited_depth = None
        inherited_passability = None
        if previous_sentence and re.match(r"These included\b", sent_text, re.I):
            if "flood" in previous_sentence.lower():
                depth_range = NUMERIC_DEPTH_RANGE_PATTERN.search(previous_sentence)
                if depth_range:
                    inherited_depth = depth_range.group(0)
                if re.search(r"\b(?:closed to light vehicles|not passable to light vehicles)\b", previous_sentence, re.I):
                    inherited_passability = "light_vehicle_closed"
        # Only an immediately adjacent sentence in the same paragraph can
        # qualify "the road"; multiple possible roads remain unresolved.
        if re.fullmatch(r"(?:Officials confirmed (?:that )?)?[Tt]he road remained passable to all"
                        r"(?: types of| kinds of)? vehicles\.?", sent_text):
            prior_roads = [c for c in previous_claims if c.place_type == "street"]
            if len(prior_roads) == 1:
                road = prior_roads[0]
                start, end = road.evidence_sentence_offset
                if re.fullmatch(r"[ \t]*", text_to_process[end:sent_start]):
                    road.road_passability = "passable_all"
                    road.evidence_sentence = text_to_process[start:sent_end]
                    road.evidence_sentence_offset = (start, sent_end)
        claims = extract_claims_from_sentence(
            sent_text,
            sent_start,
            sent_end,
            article_input,
            inherited_depth,
            inherited_passability or section_passability,
            section_city,
            section_barangay,
            section_time_raw,
            section_flood_reported,
            section_time_context,
            event_day,
        )
        for claim in claims:
            if is_metadata_only and "metadata_only_lead" not in claim.uncertainty_reasons:
                claim.uncertainty_reasons.append("metadata_only_lead")
            all_claims.append(claim)
        previous_sentence = sent_text
        previous_claims = claims

    mark_contradictory_updates(all_claims)
    mark_city_summaries_as_context(all_claims)
    return NewsExtractionResult(
        article_id=article_input.article_id,
        canonical_url=article_input.canonical_url,
        is_metadata_only=is_metadata_only,
        processed_text_length=len(text_to_process),
        claims=all_claims,
        extracted_at=datetime.now(timezone.utc),
        extractor_version="taglish-rules-v1.4",
        errors=[],
    )
