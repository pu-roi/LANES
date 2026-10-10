from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.flood_subsidence import DurationQuantile


class ZoneExpiryPolicy(BaseModel):
    automatic_expiry_enabled: bool
    pasig_ml_expiry_enabled: bool
    method: Literal["fixed", "fixed_fallback", "ml_pooled", "ml_cross_location", "pending_sync"]
    deadline: datetime | None
    reason: str | None
    reference_basis: Literal["observed_reference", "submission_proxy", "registration_proxy"] | None
    experimental: bool
    zone_is_active: bool = True
    prediction_as_of_at: datetime | None = None
    quantiles: list[DurationQuantile] = Field(default_factory=list)
    model_sha256: str | None = None
    accuracy_verified: Literal[False] = False
    expires_as: Literal["Unconfirmed"] = "Unconfirmed"
