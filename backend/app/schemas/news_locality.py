"""Provenance of a source-backed locality-point road estimate."""
from typing import Literal

from pydantic import BaseModel, Field


class LocalityAnchorEvidence(BaseModel):
    osm_node_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=300)
    source_url: str = Field(pattern=r"^https://www\.openstreetmap\.org/node/[0-9]+$")
    distance_metres: float = Field(ge=0, le=500, allow_inf_nan=False)
    geometry_basis: Literal["source_locality_point_estimate"] = "source_locality_point_estimate"
