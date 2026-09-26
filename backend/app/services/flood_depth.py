"""Canonical MMDA-style flood depth gauge values shared by server workflows."""

from dataclasses import dataclass
from typing import Optional

from app.models.report import ReportSeverity


@dataclass(frozen=True)
class FloodDepthMeasurement:
    """Official MMDA-correlated measurement specifications for a flood depth level."""
    key: str
    display_label: str
    inches: float
    meters: float
    centimeters: float
    formatted: str
    accessibility_class: str  # "PATV", "NPLV", "NPATV"
    severity: ReportSeverity


FLOOD_DEPTH_MEASUREMENTS: dict[str, FloodDepthMeasurement] = {
    "gutter": FloodDepthMeasurement(
        key="gutter",
        display_label="Gutter",
        inches=8.0,
        meters=0.20,
        centimeters=20.32,
        formatted='8" (0.20m)',
        accessibility_class="PATV",
        severity=ReportSeverity.LOW,
    ),
    "half-knee": FloodDepthMeasurement(
        key="half-knee",
        display_label="Half-Knee",
        inches=10.0,
        meters=0.25,
        centimeters=25.40,
        formatted='10" (0.25m)',
        accessibility_class="PATV",
        severity=ReportSeverity.LOW,
    ),
    "half-tire": FloodDepthMeasurement(
        key="half-tire",
        display_label="Half-Tire",
        inches=13.0,
        meters=0.33,
        centimeters=33.02,
        formatted='13" (0.33m)',
        accessibility_class="NPLV",
        severity=ReportSeverity.MEDIUM,
    ),
    "knee": FloodDepthMeasurement(
        key="knee",
        display_label="Knee",
        inches=19.0,
        meters=0.48,
        centimeters=48.26,
        formatted='19" (0.48m)',
        accessibility_class="NPLV",
        severity=ReportSeverity.MEDIUM,
    ),
    "tires": FloodDepthMeasurement(
        key="tires",
        display_label="Tires",
        inches=26.0,
        meters=0.66,
        centimeters=66.04,
        formatted='26" (0.66m)',
        accessibility_class="NPATV",
        severity=ReportSeverity.HIGH,
    ),
    "waist": FloodDepthMeasurement(
        key="waist",
        display_label="Waist",
        inches=37.0,
        meters=0.94,
        centimeters=93.98,
        formatted='37" (0.94m)',
        accessibility_class="NPATV",
        severity=ReportSeverity.HIGH,
    ),
    "chest": FloodDepthMeasurement(
        key="chest",
        display_label="Chest",
        inches=45.0,
        meters=1.14,
        centimeters=114.30,
        formatted='45" (1.14m)',
        accessibility_class="NPATV",
        severity=ReportSeverity.HIGH,
    ),
    "neck": FloodDepthMeasurement(
        key="neck",
        display_label="Neck & Above",
        inches=55.0,
        meters=1.40,
        centimeters=140.0,
        formatted='55"+ (1.40m+)',
        accessibility_class="NPATV",
        severity=ReportSeverity.EXTREME,
    ),
}

FLOOD_DEPTH_SEVERITIES: dict[str, ReportSeverity] = {
    k: v.severity for k, v in FLOOD_DEPTH_MEASUREMENTS.items()
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
    if normalized not in FLOOD_DEPTH_MEASUREMENTS:
        raise ValueError("Depth must be a supported flood gauge level.")
    return normalized


def severity_for_flood_depth(depth: str) -> ReportSeverity:
    canonical = normalize_flood_depth(depth)
    if not canonical:
        raise ValueError("Depth must be a supported flood gauge level.")
    return FLOOD_DEPTH_MEASUREMENTS[canonical].severity


def get_flood_depth_measurement(depth: Optional[str]) -> Optional[FloodDepthMeasurement]:
    """Return the official MMDA-correlated measurement details for a depth value."""
    if not depth:
        return None
    try:
        canonical = normalize_flood_depth(depth)
        return FLOOD_DEPTH_MEASUREMENTS.get(canonical) if canonical else None
    except ValueError:
        return None


def format_flood_depth(depth: Optional[str]) -> Optional[str]:
    """Format a depth string into readable MMDA measurements, e.g. 'Knee • 19\" (0.48m)'."""
    measurement = get_flood_depth_measurement(depth)
    if not measurement:
        return depth
    return f"{measurement.display_label} • {measurement.formatted}"
