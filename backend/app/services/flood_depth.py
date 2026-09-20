"""Canonical MMDA-style flood depth gauge values shared by server workflows."""

from typing import Optional

from app.models.report import ReportSeverity


FLOOD_DEPTH_SEVERITIES: dict[str, ReportSeverity] = {
    "gutter": ReportSeverity.LOW,
    "half-knee": ReportSeverity.LOW,
    "half-tire": ReportSeverity.MEDIUM,
    "knee": ReportSeverity.MEDIUM,
    "tires": ReportSeverity.HIGH,
    "waist": ReportSeverity.HIGH,
    "chest": ReportSeverity.HIGH,
    "neck": ReportSeverity.EXTREME,
}

_DEPTH_ALIASES = {
    "neck & above": "neck",
    "neck and above": "neck",
}


def normalize_flood_depth(value: Optional[str]) -> Optional[str]:
    """Return a canonical gauge ID, accepting legacy display labels at the API edge."""
    if value is None:
        return None
    normalized = " ".join(value.strip().lower().split())
    normalized = _DEPTH_ALIASES.get(normalized, normalized)
    if normalized not in FLOOD_DEPTH_SEVERITIES:
        raise ValueError("Depth must be a supported flood gauge level.")
    return normalized


def severity_for_flood_depth(depth: str) -> ReportSeverity:
    return FLOOD_DEPTH_SEVERITIES[depth]
