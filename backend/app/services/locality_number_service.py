"""Deterministic cardinal-number equivalence for numbered Philippine places.

Comparison keys only: source names and evidence offsets are never rewritten.
Vocabulary follows Oxnard College's Filipino number handout, Essential Tagalog
Grammar and Diksiyonaryo.ph (sources recorded in the news evaluation).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterator


def _words(value: str) -> tuple[str, ...]:
    folded = "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                     if not unicodedata.combining(c))
    return tuple(re.findall(r"[a-z0-9]+", folded))


# Exact, reviewed spellings; deliberately no edit-distance guesses.
_UNITS = (
    ("zero", "sero", "cero"), ("one", "isa", "uno"),
    ("two", "dalawa", "dos"), ("three", "tatlo", "tres"),
    ("four", "apat", "kuwatro", "kwatro", "cuatro"),
    ("five", "lima", "singko", "sinko", "cinco"),
    ("six", "anim", "sais", "seis"),
    ("seven", "pito", "siyete", "syete", "siete"),
    ("eight", "walo", "otso", "ocho"),
    ("nine", "siyam", "nuwebe", "nwebe", "nueve"),
)
_TEENS = (
    ("ten", "sampu", "diyes", "dyes", "dies", "diez"),
    ("eleven", "labing isa", "labingisa", "onse", "once"),
    ("twelve", "labing dalawa", "labindalawa", "dose", "doce"),
    ("thirteen", "labing tatlo", "labintatlo", "trese", "trece"),
    ("fourteen", "labing apat", "labingapat", "katorse", "catorce"),
    ("fifteen", "labing lima", "labinlima", "kinse", "quince"),
    ("sixteen", "labing anim", "labinganim", "disisais", "dieciseis"),
    ("seventeen", "labing pito", "labimpito", "disisiyete", "disisyete", "diecisiete"),
    ("eighteen", "labing walo", "labingwalo", "disiotso", "dieciocho"),
    ("nineteen", "labing siyam", "labinsiyam", "labingsiyam", "disinuwebe", "diecinueve"),
)
_TENS = {
    20: ("twenty", "dalawampu", "bente", "beynte", "beinte", "veinte"),
    30: ("thirty", "tatlumpu", "trenta", "treinta"),
    40: ("forty", "apatnapu", "kuwarenta", "kwarenta", "cuarenta"),
    50: ("fifty", "limampu", "singkuwenta", "singkwenta", "cincuenta"),
    60: ("sixty", "animnapu", "sisenta", "sesenta", "seisenta"),
    70: ("seventy", "pitumpu", "sitenta", "setenta"),
    80: ("eighty", "walumpu", "otsenta", "ochenta"),
    90: ("ninety", "siyamnapu", "nobenta", "noventa"),
}
_SMALL: dict[tuple[str, ...], int] = {}
for _value, _forms in enumerate((*_UNITS, *_TEENS)):
    for _form in _forms:
        _SMALL[_words(_form)] = _value
for _value, _forms in _TENS.items():
    for _form in _forms:
        _SMALL[_words(_form)] = _value
        for _unit in range(1, 10):
            for _unit_form in _UNITS[_unit]:
                # Native 't/at, Spanish y, English hyphen/space, and joined
                # colloquial forms (beyntesingko, kwarentay singko).
                for _join in (" ", " at ", "'t ", " y ", "y ", ""):
                    _SMALL[_words(_form + _join + _unit_form)] = _value + _unit
                if _value == 20:
                    _SMALL[_words("veinti" + _unit_form)] = _value + _unit

_HUNDREDS: dict[tuple[str, ...], int] = {}
_LINKED_UNITS = ("", "isang", "dalawang", "tatlong", "apat na", "limang",
                 "anim na", "pitong", "walong", "siyam na")
_SPANISH_HUNDREDS = ("", "cien", "doscientos", "trescientos", "cuatrocientos",
                     "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos")
for _unit in range(1, 10):
    for _form in (_UNITS[_unit][0] + " hundred", _LINKED_UNITS[_unit] + " daan",
                  _LINKED_UNITS[_unit] + " raan", _SPANISH_HUNDREDS[_unit]):
        _HUNDREDS[_words(_form)] = _unit * 100
    for _form in _UNITS[_unit][1:]:
        for _suffix in (" siyentos", " syentos", " cientos"):
            _HUNDREDS[_words(_form + _suffix)] = _unit * 100
for _form in ("sandaan", "siyento", "syento", "ciento"):
    _HUNDREDS[_words(_form)] = 100
for _form in ("kinyentos",):
    _HUNDREDS[_words(_form)] = 500

_CONNECTORS = {"and", "at", "y", "t"}
_SCALES = {"million": 1_000_000, "milyon": 1_000_000,
           "millon": 1_000_000, "millones": 1_000_000,
           "thousand": 1000, "libo": 1000, "mil": 1000}
_LINKS = {_words(link): unit for unit, link in enumerate(_LINKED_UNITS) if link}
_LINKS[("sampung",)] = 10
_LINKS[("un",)] = 1
for _value, _forms in _TENS.items():
    _LINKS[(_forms[1] + "ng",)] = _value


@lru_cache(maxsize=4096)
def _cardinal(tokens: tuple[str, ...], ceiling: int = 1_000_000_000) -> int | None:
    if not tokens:
        return None
    if tokens[0] == "sanlibo":
        tokens = ("isang", "libo", *tokens[1:])
    if len(tokens) == 1 and tokens[0].isdigit():
        if len(tokens[0]) > 9:
            return None
        value = int(tokens[0])
        return value if value < ceiling else None
    if tokens in _SMALL:
        return _SMALL[tokens] if _SMALL[tokens] < ceiling else None
    for index, token in enumerate(tokens):
        scale = _SCALES.get(token)
        if scale is None:
            continue
        if scale >= ceiling:
            return None
        prefix = tokens[:index]
        factor = _LINKS.get(prefix)
        if factor is None:
            factor = _cardinal(prefix, 1000) if prefix else (1 if token == "mil" else None)
        if factor is None and prefix:
            # Filipino linkers on the last cardinal before libo/milyon:
            # dalawampu't limang libo, apatnapu't apat na libo.
            linked = {"isang": "isa", "dalawang": "dalawa", "tatlong": "tatlo",
                      "limang": "lima", "pitong": "pito", "walong": "walo"}
            if prefix[-1] in linked:
                factor = _cardinal((*prefix[:-1], linked[prefix[-1]]), 1000)
            elif prefix[-1] == "na":
                factor = _cardinal(prefix[:-1], 1000)
        if not factor:
            return None
        remainder = tokens[index + 1:]
        if remainder and remainder[0] in _CONNECTORS:
            remainder = remainder[1:]
            if not remainder:
                return None
        tail = _cardinal(remainder, scale) if remainder else 0
        value = factor * scale + tail if tail is not None else ceiling
        return value if value < ceiling else None
    for prefix, value in _HUNDREDS.items():
        if tokens[:len(prefix)] != prefix or value >= ceiling:
            continue
        remainder = tokens[len(prefix):]
        if not remainder:
            return value
        if remainder[0] in _CONNECTORS:
            remainder = remainder[1:]
        tail = _SMALL.get(remainder)
        if tail is not None and 0 < tail < 100:
            return value + tail if value + tail < ceiling else None
    return None


_PREFIX = re.compile(
    r"\b(?P<kind>sitio|purok|zone|phase|block|barangay|brgy)\.?(?:\s+|(?=#))"
    r"(?:(?:no\.?|number|numero|bilang)(?:\s+|(?=#)))?(?:#\s*)?", re.I,
)
_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
_NUMBER_STARTS = {key[0] for key in (*_SMALL, *_HUNDREDS, *_LINKS)} | set(_SCALES) | {"sanlibo"}


@dataclass(frozen=True)
class NumberedLocality:
    kind: str
    number: int
    start: int
    end: int
    number_start: int
    suffix: str = ""


def numbered_localities(text: str) -> Iterator[NumberedLocality]:
    """Recognize complete cardinals after a place designator, keeping offsets."""
    for prefix in _PREFIX.finditer(text):
        tokens: list[re.Match[str]] = []
        cursor = prefix.end()
        for token in _TOKEN.finditer(text, cursor):
            gap = text[cursor:token.start()]
            if not tokens and gap.strip():
                break
            if len(tokens) == 18 or not re.fullmatch(r"[\s'’\-]*", gap):
                break
            tokens.append(token)
            cursor = token.end()
        for count in range(len(tokens), 0, -1):
            end = tokens[count - 1].end()
            value = _cardinal(_words(text[prefix.end():end]))
            attached_suffix = ""
            if value is None and count == 1:
                code = re.fullmatch(r"(\d{1,9})([a-z])", tokens[0].group(), re.I)
                if code:
                    value, attached_suffix = int(code.group(1)), code.group(2).casefold()
            if value is None:
                continue
            # Never shorten ranges, slash codes, decimals or unsupported
            # numeric continuations into another locality's identity.
            tail = text[end:]
            if re.match(r"\s*[-/]\s*\d|[.,]\d", tail):
                break
            if count < len(tokens):
                next_word = _words(tokens[count].group())[0]
                if next_word.isdigit() or next_word in _NUMBER_STARTS or next_word in _SCALES:
                    break
                if next_word in _CONNECTORS | {"to", "through", "hanggang"} and count + 1 < len(tokens):
                    after = _words(tokens[count + 1].group())[0]
                    if after.isdigit() or after in _NUMBER_STARTS or after in {"half", "media", "medio", "kalahati"}:
                        break
            suffix_match = re.match(r"[\s-]+([A-Za-z])\b", tail) if not attached_suffix else None
            suffix = suffix_match.group(1).casefold() if suffix_match else attached_suffix
            if suffix_match:
                end += suffix_match.end()
            yield NumberedLocality(prefix.group("kind").casefold(), value,
                                   prefix.start(), end, prefix.end(), suffix)
            break


def normalize_locality_numbers(text: str) -> str:
    """Build matching text without mutating raw evidence or displayed labels."""
    for place in reversed(list(numbered_localities(text))):
        kind = "barangay" if place.kind == "brgy" else place.kind
        text = text[:place.start] + f"{kind} {place.number}{place.suffix}" + text[place.end:]
    return text
