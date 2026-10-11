"""Commuter headlines are information, not evidence for flood activation."""
import re

from app.services.news_discovery_service import METRO_MANILA_TERMS, body_has_metro_manila_flood_claim
from app.services.news_feed_service import NewsEntry

METRO_RAIL = re.compile(r"\b(?:MRT[-\s]?3|LRT[-\s]?[12])\b", re.I)
WEATHER_TOPICS = re.compile(r"\b(?:weather\s+forecast|PAGASA|rain(?:s|fall|showers)?|rain\s+showers|thunderstorms?|habagat|typhoons?|heat\s+index)\b", re.I)
COMMUTER_TOPICS = re.compile(
    r"\b(?:weather\s+(?:advisory|warning|forecast)|rainfall\s+(?:warning|advisory)|"
    r"rain(?:s|fall|showers)?|rain\s+showers|thunderstorms?|habagat|heat\s+(?:index|advisory|warning)|"
    r"typhoons?|tropical\s+(?:storm|depression)|"
    r"traffic\s+(?:advisory|scheme|rerouting|congestion|disruption|restriction)|"
    r"road\s+(?:closure|closures|closed|works)|lane\s+(?:closure|closures)|"
    r"(?:roads?|bridges?)\s+(?:will\s+be\s+|temporarily\s+)?closed|"
    r"rerouting|re[-\s]?routing|road\s+repair|"
    r"transport\s+(?:strike|disruption|advisory)|"
    r"(?:bus|jeepney|train|rail|MRT[-\s]?3|LRT[-\s]?[12])\s+(?:service|operations?|strike|fare|schedule)|"
    r"service\s+(?:interruption|suspension|disruption)|"
    r"safety\s+advisory|evacuation\s+(?:order|advisory|notice)|"
    r"landslide\s+warning|class(?:es)?\s+suspension|walang\s+pasok)\b", re.I,
)


def has_local_commuter_context(text: str) -> bool:
    # A publisher dateline or the location of its weather office is not impact.
    text = re.sub(r"^\s*Manila(?:,\s*Philippines)?\s*[-—–:\ufffd]\s*", "", text, flags=re.I)
    text = re.sub(r"\bManila\s+(?:weather\s+)?office\b", "office", text, flags=re.I)
    return bool(COMMUTER_TOPICS.search(text) and (METRO_MANILA_TERMS.search(text) or METRO_RAIL.search(text)))


def metadata_has_commuter_news(entry: NewsEntry) -> bool:
    text = f"{entry.title}. {entry.excerpt}"
    # National weather headlines may name another region while the forecast
    # body also covers Metro Manila. Fetch within the separate bounded budget;
    # body_has_commuter_news still requires actual local forecast context.
    return has_local_commuter_context(text) or bool(WEATHER_TOPICS.search(text))


def body_has_commuter_news(entry: NewsEntry, body: str) -> bool:
    # Both metadata and a current body sentence must support local relevance.
    return metadata_has_commuter_news(entry) and any(
        has_local_commuter_context(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", body)
    )


def body_has_local_news(entry: NewsEntry, body: str) -> bool:
    return body_has_commuter_news(entry, body) or body_has_metro_manila_flood_claim(entry, body)
