"""Shared observation and geographic gates for collection, extraction and reading.

Patterns use syntax supported by Python, PostgreSQL and SQLite REGEXP. SQL
applies these gates before counting/pagination; history retains excluded claims.
"""
import re

from app.schemas.news_extraction import ExtractedClaim


NON_OBSERVATION_PATTERN = (
    r"(?:flood[\s‐‑–—-]+(?:control|mitigation|prevention|management|protection)|"
    r"anti[\s‐‑–—-]+flood|"
    r"(?:prevent|mitigate|curb|address|reduce|avoid|alleviate|avert|combat)(?:s|ed|ing)?\s+"
    r"(?:(?:localized|local|urban|future|potential|severe|the|risk\s+of)\s+)*(?:flood(?:s|ing)?|inundation)|"
    r"(?:regularly|usually|often|frequently|historically|routinely)\s+"
    r"(?:(?:is|are|was|were|becomes?|gets?)\s+)?(?:flooded|submerged|inundated)|"
    r"flood[\s-]+prone)"
)
# Independent evidence preserves mixed infrastructure/actual incident reports.
# Bare "flooding", "rising" or funding/project dimensions are insufficient
# to override a prevention or habitual reference.
OBSERVED_EVENT_PATTERN = (
    r"(?:binaha|binabaha|bumaha|bumabaha|nalubog|humuhupa|humupa|"
    r"(?<!regularly )(?<!usually )(?<!often )(?<!frequently )(?<!historically )(?<!routinely )"
    r"(?:is|are|was|were|remain|remains|remained|has\s+been|have\s+been)\s+"
    r"(?:(?:still|also|now|currently|already|completely)\s+)*(?:flooded|submerged|inundated)|"
    r"(?:flooding|floodwaters?|flood\s+water|baha)\s+(?:(?:is|are|was|were)\s+)?"
    r"(?:reported|observed|recorded|seen|rising|receding|subsided)|"
    r"(?:reported|observed|recorded|experienced)\s+(?:(?:actual|ongoing|severe)\s+)?(?:flooding|floodwaters?|baha)|"
    r"(?:gutter|ankle|calf|knee|tire|waist|chest|neck)[\s-]+deep|"
    r"(?:abot|lagpas|lampas|hanggang)[\s-]+(?:sakong|binti|tuhod|gulong|baywang|bewang|dibdib|leeg))"
)
# Every accepted claim needs affirmative water-on-the-ground evidence, even
# when a sentence does not contain an infrastructure/prevention keyword.
FLOOD_OBSERVATION_PATTERN = (
    OBSERVED_EVENT_PATTERN
    + r"|(?:floods?|flooding|floodwaters?|baha)\s+"
      r"(?:(?:has|have|had|is|are|was|were|also|still|already|been)\s+)*"
      r"(?:hit|hits|affected|affects|inundated|submerged|swamped|rose|risen|receded|subsided)(?:[^a-z]|$)"
      r"|(?:^|[^a-z])flooded\s+(?:roads?|streets?|homes?|houses?|areas?|villages?|barangays?)(?:[^a-z]|$)"
      r"|(?:^|[^a-z])(?:waded|wading|stranded)[^.!?]{0,80}floodwaters?(?:[^a-z]|$)"
      r"|(?:^|[^a-z])(?:floodwaters?|baha)[^.!?]{0,50}(?:rose|rising|receding|subsided|humupa|humuhupa)(?:[^a-z]|$)"
      r"|(?:^|[^a-z])(?:flooding|floodwaters?|baha)[^.!?]{0,140}(?:cleared|subsided|receded)(?:[^a-z]|$)"
      r"|(?:^|[^a-z])(?:roads?|routes?|areas?)(?:\s+and\s+(?:roads?|routes?|areas?))?\s+"
      r"(?:(?:were|are)\s+)?affected\s+by\s+flooding(?:[^a-z]|$)"
)
HYPOTHETICAL_FLOOD_PATTERN = (
    r"(?:^|[^a-z])(?:will|may|might|could|would)\s+(?:be\s+)?"
    r"(?:flood(?:ed)?|inundate(?:d)?|submerge(?:d)?|reach|rise)(?:[^a-z]|$)"
    r"|(?:^|[^a-z])(?:simulat(?:ion|ed|es?)|drills?|predict(?:s|ed|ion)?)(?:[^a-z]|$)"
    r"|(?:^|[^a-z])(?:madalas|lagi|palagi|karaniwang|tuwing)\s+[^.!?]{0,40}(?:binabaha|bumabaha)"
    r"|(?:prevent|avoid|mitigate|reduce)\s+[^.!?]{0,35}(?:knee|waist|chest|ankle|gutter)[\s-]+deep"
)
METRO_CITY_PATTERN = (
    r"^(?:(?:city|municipality)\s+of\s+)?(?:caloocan|las\s+pi[ñn]as|makati|malabon|"
    r"mandaluyong|manila|marikina|muntinlupa|navotas|para[ñn]aque|pasay|pasig|"
    r"quezon|san\s+juan|taguig|valenzuela|pateros)(?:\s+city)?$"
)


def non_observation_only(text: str) -> bool:
    evidence = text.lower()
    return bool(re.search(NON_OBSERVATION_PATTERN, evidence)
                and not re.search(OBSERVED_EVENT_PATTERN, evidence))


def has_flood_observation(text: str) -> bool:
    return bool(re.search(FLOOD_OBSERVATION_PATTERN, text.lower())
                and not re.search(HYPOTHETICAL_FLOOD_PATTERN, text.lower())
                and not non_observation_only(text))


def metro_manila_claim(claim: ExtractedClaim) -> bool:
    if claim.psgc_code:
        return claim.psgc_code.startswith("13")
    return bool(re.fullmatch(METRO_CITY_PATTERN, (claim.canonical_city or "").strip().lower()))
