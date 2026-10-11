from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.flood_subsidence import DurationQuantile, DurationCalculation
from app.schemas.cross_location_prediction import CrossLocationCalculation


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
    calculation: DurationCalculation | CrossLocationCalculation | None = None
    city: str | None = None
    barangays: list[str] = Field(default_factory=list)
    depth_cm: float | None = None
    depth_basis: str | None = None
    target_location: str | None = None
    fallback_basis: Literal["activation_retention"] | None = None
    accuracy_verified: Literal[False] = False
    expires_as: Literal["Unconfirmed"] = "Unconfirmed"
