from typing import List, Any, Literal, Optional
from pydantic import BaseModel, Field


class LineStringGeometry(BaseModel):
    """GeoJSON LineString geometry."""
    type: str = "LineString"
    coordinates: List[List[float]]  # List of [longitude, latitude] points


class RouteRequest(BaseModel):
    """Request start and end coordinates for routing.
    Coordinates format: [longitude, latitude]
    """
    start: List[float] = Field(..., min_length=2, max_length=2, description="Start coordinates [lng, lat]")
    end: List[float] = Field(..., min_length=2, max_length=2, description="End coordinates [lng, lat]")
    ignore_floods: bool = Field(False, description="Legacy compatibility field; public routing always applies flood policy")
    vehicle_profile: Literal["light", "heavy", "motorcycle", "walk"] = Field("light", description="Vehicle profile")
    engine: Literal["valhalla", "ors"] = Field("valhalla", description="Routing engine to use")
    heading: int = Field(None, description="Optional heading in degrees (0-360) to force snapping to a specific lane direction")


class FloodExposure(BaseModel):
    """Deterministic flood exposure, not a probability of harm."""
    highest_severity: Literal["none", "low", "medium", "high", "extreme"] = "none"
    zone_count: int = 0
    intersected_distance_m: float = 0.0
    exposure_score: int = 0
    message: str = "No active flood-zone exposure."


class RouteOption(BaseModel):
    """A single route candidate returned as part of a multi-route response.

    Attributes:
        index: Position in the OSRM candidate list (0 = primary).
        label: Human-readable label e.g. 'Recommended', 'Alternative 1'.
        geometry: GeoJSON LineString of the route path.
        distance: Total route distance in meters.
        duration: Estimated travel duration in seconds.
        avoided_floods: True if this route successfully diverted around an active flood zone.
        blocked: True if this specific route passes through an active flood zone.
        is_truncated: True if the route appears spatially incomplete due to one-way road constraints.
                      See docs/planning.md section Routing Known Constraints for context.
        safety_score: A calculated safety percentage (e.g. 100 for clear, 50 for traversing orange).
        flood_risk: A string indicator of the highest flood severity encountered (e.g. 'none', 'low', 'medium', 'high').
    """
    index: int
    label: str
    geometry: LineStringGeometry
    distance: float
    duration: float
    avoided_floods: bool
    blocked: bool = False
    is_truncated: bool = False
    safety_score: float = 100.0
    flood_risk: str = "none"
    category: Literal["fastest", "safest", "balanced", "alternative"] = "alternative"
    flood_exposure: FloodExposure = Field(default_factory=FloodExposure)
    instructions: List[Any] = []


class BlockedRouteBaseline(BaseModel):
    """Explanation-only direct route; never a selectable navigation option."""
    distance: float
    duration: float
    flood_exposure: FloodExposure
    message: str


class MultiRouteResponse(BaseModel):
    """Response containing all available route candidates with flood safety metadata.

    Attributes:
        routes: List of route options ordered by OSRM priority (index 0 = primary).
        recommended_index: Index of the safest route (first flood-free option, or 0 as fallback).
    """
    routes: List[RouteOption]
    recommended_index: int
    engine_used: Literal["valhalla", "ors"]
    fallback_used: bool = False
    blocked_baseline: Optional[BlockedRouteBaseline] = None


# Legacy schema retained for backward compatibility
class RouteResponse(BaseModel):
    """Legacy single-route response schema."""
    geometry: LineStringGeometry
    distance: float
    duration: float
    avoided_floods: bool
    blocked: bool = False
