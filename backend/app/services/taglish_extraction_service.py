"""Evidence-linked Taglish NLP extraction service for news articles.

Extracts Pasig places, flood mentions, canonical depth, condition, and event time
while preserving source text offsets, evidence sentences, and explicit uncertainty.
Does NOT activate public zones or alter routing.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.news_extraction import (
    CanonicalDepth,
    ExtractedClaim,
    FloodCondition,
    NewsArticleExtractorInput,
    NewsExtractionResult,
    PlaceType,
)
from app.services.flood_depth import FLOOD_DEPTH_SEVERITIES
from app.services.philippine_location_service import (
    COMMON_ALIASES,
    get_philippine_location_service,
)

# Dynamic geographic reference data loaded from official PSA PSGC dataset.
# Eliminates hardcoded barangay and place tuples in Python application code.
_loc_service = get_philippine_location_service()
PASIG_BARANGAYS_CANONICAL: tuple[str, ...] = _loc_service.get_pasig_barangay_tuple()
BARANGAY_ALIASES: dict[str, str] = COMMON_ALIASES

OUT_OF_PASIG_CITIES: tuple[str, ...] = (
    "Quezon City", "QC", "Manila", "Maynila", "Marikina", "Mandaluyong",
    "Taguig", "Makati", "San Juan", "Parañaque", "Paranaque", "Las Piñas", "Las Pinas",
    "Muntinlupa", "Caloocan", "Malabon", "Navotas", "Valenzuela", "Pateros",
    "Cainta", "Taytay", "Antipolo",
)

PASIG_LANDMARKS: tuple[str, ...] = (
    "Pasig City Hall", "Pasig Mega Market", "Rizal High School", "Capitol Commons",
    "The Medical City", "Pasig Rainforest Park",
)

PASIG_KNOWN_STREETS: tuple[str, ...] = (
    "C. Raymundo Avenue", "C. Raymundo Ave",
    "Ortigas Avenue", "Ortigas Ave",
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
    "España Boulevard", "Espana Boulevard",
    "Commonwealth Avenue",
)

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

# Condition indicators
CONDITION_RISING = re.compile(r"\b(?:patuloy\s+na\s+tumataas|tumataas|rising|risen\s+to|increasing)\b", re.I)
CONDITION_RECEDING = re.compile(r"\b(?:nagsisimula\s+nang\s+humupa|bumababa\s+na|bumababa|humuhupa|receding|subsiding)\b", re.I)
CONDITION_SUBSIDED = re.compile(r"\b(?:humupa\s+na|completely\s+subsided|subsided|clear\s+na\s+sa\s+baha|wala\s+nang\s+baha)\b", re.I)

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
    r"\d+\s*(?:centimeters?|cm|meters?|m|feet|foot|ft|inches|in)|"
    r"mataas\s+na\s+(?:pagbaha|baha)|deep\s+(?:floodwaters?|flood|waters?|flooding)|abot[-\s]bubong"
    r")\b",
    re.I,
)

# Event time expressions
TIME_EXPRESSIONS = re.compile(
    r"\b(?:"
    r"kaninang\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)|"
    r"as\s+of\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)|"
    r"around\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)|"
    r"at\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)|"
    r"bandang\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)|"
    r"simula\s+kaninang\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)|"
    r"kaninang\s+(?:tanghali|umaga|hapon|gabi)|"
    r"kaninang\s+alas-[a-z]+(?:\s+ng\s+(?:hapon|gabi|umaga))?|"
    r"alas-[a-z]+(?:\s+ng\s+(?:hapon|gabi|umaga))?|"
    r"this\s+afternoon|this\s+morning|later\s+tonight|mamayang\s+gabi|ngayong\s+araw|"
    r"noong\s+nakaraang\s+taon|taong\s+20\d\d|in\s+20\d\d"
    r")\b",
    re.I,
)


KNOWN_ABBREVIATIONS = (
    "brgy.", "bgy.", "st.", "ave.", "blvd.", "rd.", "dr.", "no.",
    "p.m.", "a.m.", "sta.", "sto.", "gen.", "gov.", "pagasa.",
    "inc.", "co.", "approx.",
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
    """Locate all place candidates within a sentence with exact character offsets."""
    mentions: list[dict[str, Any]] = []

    # 1. Landmarks
    for landmark in PASIG_LANDMARKS:
        for m in re.finditer(r"\b" + re.escape(landmark) + r"\b", sentence, re.I):
            mentions.append({
                "raw_place_name": m.group(0),
                "canonical_barangay": None,
                "place_type": "landmark",
                "char_start": sent_offset_start + m.start(),
                "char_end": sent_offset_start + m.end(),
            })

    # 2. Known Streets
    for street in PASIG_KNOWN_STREETS:
        for m in re.finditer(r"\b" + re.escape(street) + r"\b", sentence, re.I):
            mentions.append({
                "raw_place_name": m.group(0),
                "canonical_barangay": None,
                "place_type": "street",
                "char_start": sent_offset_start + m.start(),
                "char_end": sent_offset_start + m.end(),
            })

    # 2b. Generic Nationwide Streets/Avenues/Boulevards/Highways
    generic_street_pattern = re.compile(
        r"\b([A-Z][a-zA-Z0-9\.\'\s]{1,35}?\s+(?:Street|St\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Highway|Hwy\.?|Road|Rd\.?|Way|Drive|Dr\.?))\b",
        re.I,
    )
    for m in generic_street_pattern.finditer(sentence):
        st_name = m.group(1).strip()
        if not any(st_name.lower() == existing["raw_place_name"].lower() for existing in mentions):
            mentions.append({
                "raw_place_name": st_name,
                "canonical_barangay": None,
                "place_type": "street",
                "char_start": sent_offset_start + m.start(1),
                "char_end": sent_offset_start + m.end(1),
            })

    # 3. Out-of-Pasig Cities
    for city in OUT_OF_PASIG_CITIES:
        for m in re.finditer(r"\b" + re.escape(city) + r"\b", sentence, re.I):
            mentions.append({
                "raw_place_name": m.group(0),
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

    # 5. Barangays (with or without Barangay/Brgy. prefix, including Sta./Sto. variations)
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
        if m["char_start"] >= last_end:
            unique_mentions.append(m)
            last_end = m["char_end"]

    return unique_mentions


def extract_depth_from_text(text: str) -> tuple[str | None, CanonicalDepth | None, str | None, list[str]]:
    """Extract depth raw phrase and map to canonical gauge keys.
    Returns (depth_raw, depth_canonical, depth_rule, uncertainty_reasons).
    """
    reasons: list[str] = []

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
    if has_active_flood or ACTIVE_FLOOD_WORDS.search(text):
        return "active"
    return "unknown"


def extract_event_time_from_text(text: str) -> tuple[str | None, datetime | None]:
    """Extract explicit event time string."""
    m = TIME_EXPRESSIONS.search(text)
    if m:
        return m.group(0), None
    return None, None


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
) -> list[ExtractedClaim]:
    """Extract structured claims from a single sentence, associating facts per clause/place."""
    claims: list[ExtractedClaim] = []
    place_mentions = find_place_mentions(sentence, sent_start)
    if not place_mentions:
        return claims

    # Break sentence into clauses for fine-grained multi-location attribution
    clauses = split_clauses(sentence)

    for place in place_mentions:
        local_place_start = place["char_start"] - sent_start
        target_clause_text = sentence
        for clause_text, c_start, c_end in clauses:
            if c_start <= local_place_start < c_end:
                target_clause_text = clause_text
                break

        # Check negation in the clause
        clause_negated = bool(NEGATION_PATTERNS.search(target_clause_text))
        is_forecast = bool(FORECAST_PATTERNS.search(target_clause_text) or FORECAST_PATTERNS.search(sentence))
        is_historical = bool(HISTORICAL_PATTERNS.search(target_clause_text) or HISTORICAL_PATTERNS.search(sentence))

        uncertainties: list[str] = []
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
                ACTIVE_FLOOD_WORDS.search(target_clause_text)
                or ACTIVE_FLOOD_WORDS.search(sentence)
            )

        # Depth extraction (prefer target clause, fallback to sentence if only one place)
        d_raw, d_canon, d_rule, d_reasons = extract_depth_from_text(target_clause_text)
        if not d_raw and len(place_mentions) == 1:
            d_raw, d_canon, d_rule, d_reasons = extract_depth_from_text(sentence)
        uncertainties.extend(d_reasons)

        # If explicit depth is present and not negated/forecast/historical, flood is mentioned!
        if d_raw and not clause_negated and not is_forecast and not is_historical:
            flood_mentioned = True

        # Condition
        condition = extract_condition_from_text(target_clause_text, flood_mentioned, clause_negated)
        if condition == "unknown" and len(place_mentions) == 1:
            condition = extract_condition_from_text(sentence, flood_mentioned, clause_negated)

        # Event time
        t_raw, t_res = extract_event_time_from_text(target_clause_text)
        if not t_raw:
            t_raw, t_res = extract_event_time_from_text(sentence)

        if not t_raw:
            uncertainties.append("event_time_unknown")

        claim = ExtractedClaim(
            raw_place_name=place["raw_place_name"],
            canonical_barangay=place["canonical_barangay"],
            place_type=place["place_type"],
            place_char_start=place["char_start"],
            place_char_end=place["char_end"],
            flood_mentioned=flood_mentioned,
            is_negated=clause_negated,
            is_forecast=is_forecast,
            is_historical=is_historical,
            depth_raw=d_raw,
            depth_canonical=d_canon,
            depth_rule=d_rule,
            condition=condition,
            event_time_raw=t_raw,
            event_time_resolved=t_res,
            evidence_sentence=sentence,
            evidence_sentence_offset=(sent_start, sent_end),
            uncertainty_reasons=uncertainties,
            confidence_score=0.9 if place["canonical_barangay"] else 0.7,
        )
        claims.append(claim)

    return claims


def extract_taglish_flood_facts(article_input: NewsArticleExtractorInput) -> NewsExtractionResult:
    """Execute evidence-linked Taglish extraction on an article.
    Handles full text when present, or marks metadata-only leads when absent.
    """
    has_full_text = bool(article_input.article_text and article_input.article_text.strip())
    is_metadata_only = not has_full_text

    text_to_process = (
        article_input.article_text.strip()
        if has_full_text
        else f"{article_input.title}. {article_input.excerpt}".strip()
    )

    sentences = split_sentences_with_offsets(text_to_process)
    all_claims: list[ExtractedClaim] = []

    for sent_text, sent_start, sent_end in sentences:
        claims = extract_claims_from_sentence(sent_text, sent_start, sent_end, article_input)
        for claim in claims:
            if is_metadata_only and "metadata_only_lead" not in claim.uncertainty_reasons:
                claim.uncertainty_reasons.append("metadata_only_lead")
            all_claims.append(claim)

    return NewsExtractionResult(
        article_id=article_input.article_id,
        canonical_url=article_input.canonical_url,
        is_metadata_only=is_metadata_only,
        processed_text_length=len(text_to_process),
        claims=all_claims,
        extracted_at=datetime.now(timezone.utc),
        extractor_version="taglish-rules-v1.0",
        errors=[],
    )
