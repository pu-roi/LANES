"""Number variants must match places without changing geographic identities."""

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from shapely.geometry import Polygon

from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services.article_road_context_service import match_article_road_context, _contains_name
from app.services.article_road_match_service import OSMRoadSection, normalize_name
from app.services.locality_number_service import numbered_localities
from app.services.taglish_extraction_service import extract_taglish_flood_facts, find_place_mentions


# Independent expected vocabulary, rather than deriving answers from service constants.
@pytest.mark.parametrize("number,forms", [
    (0, "zero sero cero"), (1, "one uno isa"), (2, "two dos dalawa"),
    (3, "three tres tatlo"), (4, "four cuatro kuwatro kwatro apat"),
    (5, "five cinco singko sinko lima"), (6, "six seis sais anim"),
    (7, "seven siete siyete syete pito"), (8, "eight ocho otso walo"),
    (9, "nine nueve nuwebe nwebe siyam"), (10, "ten diez diyes dyes dies sampu"),
    (11, "eleven once onse labingisa"), (12, "twelve doce dose labindalawa"),
    (13, "thirteen trece trese labintatlo"), (14, "fourteen catorce katorse labingapat"),
    (15, "fifteen quince kinse labinlima"), (16, "sixteen dieciséis disisais labinganim"),
    (17, "seventeen diecisiete disisiyete disisyete labimpito"),
    (18, "eighteen dieciocho disiotso labingwalo"),
    (19, "nineteen diecinueve disinuwebe labinsiyam labingsiyam"),
    (20, "twenty veinte bente beynte beinte dalawampu"),
    (30, "thirty treinta trenta tatlumpu"),
    (40, "forty cuarenta kuwarenta kwarenta apatnapu"),
    (50, "fifty cincuenta singkuwenta singkwenta limampu"),
    (60, "sixty sesenta seisenta sisenta animnapu"),
    (70, "seventy setenta sitenta pitumpu"),
    (80, "eighty ochenta otsenta walumpu"),
    (90, "ninety noventa nobenta siyamnapu"),
])
def test_cardinal_forms_match_the_same_number(number: int, forms: str) -> None:
    for kind in ("Sitio", "Purok", "Barangay", "Zone", "Phase", "Block"):
        for form in forms.split():
            assert normalize_name(f"{kind} {form}") == normalize_name(f"{kind} {number}")


@pytest.mark.parametrize("name,number", [
    ("labing-isa", 11), ("labing dalawa", 12), ("labing-tatlo", 13),
    ("labing-apat", 14), ("labing lima", 15), ("labing anim", 16),
    ("labing pito", 17), ("labing walo", 18), ("labing siyam", 19),
    ("Twenty-one", 21), ("dalawampu’t isa", 21), ("dalawampu't lima", 25),
    ("bente singko", 25), ("beyntesingko", 25), ("veinticinco", 25),
    ("treinta y dos", 32), ("tatlumpu at tatlo", 33), ("kwarentay singko", 45),
    ("singkwenta y sais", 56), ("animnapu’t pito", 67), ("setenta y otso", 78),
    ("walumpu't siyam", 89), ("ninety-nine", 99), ("siyamnapu’t siyam", 99),
    ("one hundred", 100), ("sandaan", 100), ("isang daan", 100), ("siyento", 100),
    ("one hundred and five", 105), ("isang daan at lima", 105),
    ("dalawang daan", 200), ("dos siyentos", 200), ("doscientos", 200),
    ("tatlong daan pitumpu't isa", 371), ("cuatrocientos", 400),
    ("apat na raan", 400), ("limang daan", 500), ("quinientos", 500),
    ("anim na raan", 600), ("pitong daan", 700), ("walong daan", 800),
    ("siyam na raan at siyamnapu’t siyam", 999),
    ("isang libo", 1000), ("sanlibo", 1000), ("mil", 1000),
    ("sanlibo at isa", 1001), ("un millón", 1000000),
    ("one thousand and twenty five", 1025), ("isang libo at dalawampu't lima", 1025),
    ("sampung libo", 10000), ("dalawampung libo", 20000),
    ("dalawampu't limang libo", 25000), ("apatnapu't apat na libo", 44000),
    ("isang milyon", 1000000),
])
def test_compound_numbers_are_not_truncated(name: str, number: int) -> None:
    assert normalize_name(f"Purok {name}") == f"purok {number}"


@pytest.mark.parametrize("kind", ["Sitio", "Purok", "Zone", "Phase", "Block"])
def test_all_two_digit_english_numbers(kind: str) -> None:
    units = ("", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
    tens = ("twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
    for decade, name in enumerate(tens, 2):
        for unit, word in enumerate(units):
            assert normalize_name(f"{kind} {name} {word}") == f"{kind.lower()} {decade * 10 + unit}"


@pytest.mark.parametrize("text", [
    "Lima Street", "Uno Avenue", "Isa Santos Road", "Cinco de Mayo Street",
    "five inches of water at six PM", "Purok Maligaya", "Sitio Saisan",
])
def test_ordinary_names_measurements_and_words_are_not_rewritten(text: str) -> None:
    assert not list(numbered_localities(text))


@pytest.mark.parametrize("other", [
    "Purok 6", "Purok Singkwenta", "Sitio Lima", "Purok 5-A", "Purok 5 A",
    "Purok Five-A", "Purok 5/6", "Purok 5-6", "Purok 5.5", "Purok 5a",
    "Purok Twenty Five", "Purok Five and Six", "Purok Five Dos",
    "Purok -Five", "Purok Five and Half", "Purok Cinco y Media",
    "Purok 5 and 6", "Purok 5 y seis", "Purok 5 at kalahati", "Purok 5 to 6",
])
def test_distinct_or_unsupported_identifiers_never_match_five(other: str) -> None:
    assert normalize_name(other) != "purok 5"
    assert not _contains_name(other, "Purok 5")


def test_markers_accents_and_original_offsets() -> None:
    text = "May baha sa PUROK No. Síngko, Malabon; Sitio #Sais."
    places = list(numbered_localities(text))
    assert [(text[p.start:p.end], p.number) for p in places] == [
        ("PUROK No. Síngko", 5), ("Sitio #Sais", 6),
    ]
    assert normalize_name("Brgy. Dos") == normalize_name("Barangay 2")
    assert normalize_name("Purok#Singko") == "purok 5"
    assert normalize_name("Purok Singko-A") == normalize_name("Purok 5-A")
    assert _contains_name("near Purok 5A", "Purok Five-A")
    assert not _contains_name("Purok 5A", "Purok 5B")


@pytest.mark.parametrize("language", ["filipino", "spanish", "borrowed"])
def test_all_composed_tens_in_each_language(language: str) -> None:
    units = {
        "filipino": ("isa", "dalawa", "tatlo", "apat", "lima", "anim", "pito", "walo", "siyam"),
        "spanish": ("uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"),
        "borrowed": ("uno", "dos", "tres", "kuwatro", "singko", "sais", "siyete", "otso", "nuwebe"),
    }
    tens = {
        "filipino": ("dalawampu", "tatlumpu", "apatnapu", "limampu", "animnapu", "pitumpu", "walumpu", "siyamnapu"),
        "spanish": ("veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"),
        "borrowed": ("beynte", "trenta", "kuwarenta", "singkuwenta", "sisenta", "sitenta", "otsenta", "nobenta"),
    }
    for decade, name in enumerate(tens[language], 2):
        for unit, word in enumerate(units[language], 1):
            separator = "'t " if language == "filipino" else " y "
            assert normalize_name(f"Sitio {name}{separator}{word}") == f"sitio {decade * 10 + unit}"


@pytest.mark.parametrize("name", ["Sais", "anim", "Six", "labing-isa", "dalawampu’t lima", "treinta y dos"])
def test_extractor_preserves_numbered_locality_evidence(name: str) -> None:
    raw = f"Purok {name}"
    text = f"As of 4 PM, knee-deep flooding on Gov. Pascual Avenue in {raw}, Malabon City."
    mentions = find_place_mentions(text, 100)
    place = next(m for m in mentions if m["raw_place_name"] == raw)
    assert text[place["char_start"] - 100:place["char_end"] - 100] == raw
    source = NewsArticleExtractorInput(article_id=999, canonical_url="https://example.org/numbered-place",
        publisher="Fixture", title="Flood update", published_at=datetime(2026, 10, 5, tzinfo=timezone.utc),
        article_text=text)
    road = next(c for c in extract_taglish_flood_facts(source).claims
                if c.canonical_road == "Gov. Pascual Avenue")
    assert road.local_area_raw == raw
    assert road.canonical_city == "City of Malabon"
    assert road.depth_canonical == "knee"
    assert text[road.place_char_start:road.place_char_end] == road.raw_place_name


def test_number_aliases_ground_only_inside_the_checked_city() -> None:
    claim = ExtractedClaim(raw_place_name="Main Road", canonical_road="Main Road",
        canonical_city="Malabon", local_area_raw="Purok Singko",
        place_char_start=0, place_char_end=9, evidence_sentence="Flooding on Main Road",
        evidence_sentence_offset=(0, 21))
    city = Polygon([(120.9, 14.5), (121.1, 14.5), (121.1, 14.7), (120.9, 14.7)])
    base = OSMRoadSection(section_id="five", road_name="Main Road", osm_way_ids=(1,),
        centerline_geojson={"type": "LineString", "coordinates": [[121.0, 14.6], [121.001, 14.6]]},
        end_cross_streets=(("Purok 5",), ("Last Street",)), source_id="fixture")
    sections = [base, replace(base, section_id="six", end_cross_streets=(("Purok 6",), ("Last Street",))),
                replace(base, section_id="outside", centerline_geojson={"type": "LineString",
                    "coordinates": [[121.2, 14.6], [121.201, 14.6]]})]
    result = match_article_road_context(claim, sections, city)
    assert result.candidate_section_ids == ("five",)
    assert result.article_place_levels == {"five": 2}
    assert claim.local_area_raw == "Purok Singko"
