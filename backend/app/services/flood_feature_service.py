"""Versioned, source-labeled model inputs; never impute outcomes or hydraulic data."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from threading import Lock
import time

import httpx
from geoalchemy2.shape import to_shape

from app.services.flood_depth import get_flood_depth_measurement
from app.services.flood_location_service import get_flood_location_provider

_cache: dict[tuple, tuple[datetime, dict]] = {}
_lock = Lock()


def _json_request(path: str, params: dict) -> dict:
    # Fixed provider/paths: no client-controlled URL, redirects or credentials.
    started=time.monotonic()
    with httpx.Client(timeout=httpx.Timeout(2.5), follow_redirects=False) as client:
        with client.stream("GET", f"https://api.open-meteo.com/v1/{path}", params=params) as response:
            response.raise_for_status()
            raw = bytearray()
            for chunk in response.iter_bytes():
                raw.extend(chunk)
                if len(raw) > 128_000:
                    raise ValueError("Environmental response exceeds budget")
                if time.monotonic()-started>3:
                    raise ValueError("Environmental response exceeds time budget")
    result = json.loads(raw)
    if not isinstance(result, dict) or result.get("error"):
        raise ValueError("Provider returned invalid environmental data")
    return result


def environment_context(lon: float, lat: float, now: datetime) -> dict:
    key = (round(lon,3), round(lat,3), now.strftime("%Y-%m-%dT%H"))
    with _lock:
        stored = _cache.get(key)
        if stored and now-stored[0] < timedelta(hours=1):
            return json.loads(json.dumps(stored[1]))
    result = {"captured_at": now.isoformat(), "requested_coordinates": [lon,lat],
        "elevation_m": None, "elevation_source": "Copernicus DEM GLO-90 via Open-Meteo (90 m modelled surface)",
        "rainfall_previous_3h_mm": None, "rainfall_source": "Open-Meteo ECMWF IFS 0.25-degree model background",
        "rainfall_grid_coordinates": None, "rainfall_interval_end": None,
        "is_street_measurement": False, "hydraulic_drainage_capacity": None,
        "source_url": "https://open-meteo.com/en/docs", "errors": []}
    try:
        data = _json_request("elevation", {"latitude":lat,"longitude":lon})
        values = data["elevation"]
        if not isinstance(values,list) or len(values)!=1 or type(values[0]) not in (int,float) or not math.isfinite(values[0]):
            raise ValueError("Invalid elevation")
        result["elevation_m"] = values[0]
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        result["errors"].append("Modelled elevation unavailable; no value was substituted.")
    try:
        data = _json_request("forecast", {"latitude":lat,"longitude":lon,"hourly":"precipitation",
            "past_days":1,"forecast_days":1,"timezone":"UTC","models":"ecmwf_ifs025"})
        if data["hourly_units"]["precipitation"] != "mm" or data.get("utc_offset_seconds") != 0:
            raise ValueError("Unknown rainfall units or timezone")
        clocks, values = data["hourly"]["time"], data["hourly"]["precipitation"]
        if len(clocks) != len(values) or len(clocks)>96:
            raise ValueError("Invalid rainfall series")
        end = now.replace(minute=0,second=0,microsecond=0)
        slots = {datetime.fromisoformat(t).replace(tzinfo=timezone.utc):v for t,v in zip(clocks,values)}
        selected = [slots.get(end-timedelta(hours=h)) for h in range(3)]
        if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=500 for v in selected):
            raise ValueError("Missing or invalid pre-issuance rainfall slots")
        result["rainfall_previous_3h_mm"] = round(sum(selected),2)
        result["rainfall_interval_end"] = end.isoformat()
        result["rainfall_grid_coordinates"] = [data["longitude"], data["latitude"]]
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in result["rainfall_grid_coordinates"]):
            raise ValueError("Invalid model grid coordinates")
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        result.update(rainfall_previous_3h_mm=None,rainfall_interval_end=None,rainfall_grid_coordinates=None)
        result["errors"].append("Modelled rainfall unavailable; no value was substituted.")
    result["captured_at"]=datetime.now(timezone.utc).isoformat()
    with _lock:
        if len(_cache)>=128:
            _cache.pop(next(iter(_cache)))
        _cache[key]=(now,json.loads(json.dumps(result)))
    return result


def capture_features(geometry, depth: str | None, *, observed_at: datetime | None = None,
                     now: datetime | None = None, include_environment: bool = False,
                     measured_depth_cm: float | None = None) -> dict:
    """Observation/registration hooks freeze only data actually available then.

    Environment can be fetched by an authorized read; normal submissions take
    a cached snapshot and never wait on an optional external provider.
    """
    clock=now or datetime.now(timezone.utc)
    result={"schema_version":"flood_features_v1","recorded_at":clock.isoformat(),
        "observed_at":observed_at.isoformat() if observed_at else None,
        "coordinates":None,"geometry_sha256":None,"barangays":[],"boundary_revision":None,
        "depth_cm":None,"depth_basis":"unknown","environment":None,"errors":[],
        "is_training_label":False,"changes_status_expiry_or_routing":False}
    measurement=get_flood_depth_measurement(depth)
    if measurement is not None:
        result.update(depth_cm=measurement.centimeters,depth_basis="reported_canonical_gauge_proxy",
            depth_gauge=measurement.key)
    if measured_depth_cm is not None:
        if type(measured_depth_cm) not in (int,float) or not math.isfinite(measured_depth_cm) or not 0<=measured_depth_cm<=1000:
            raise ValueError("Invalid reported numeric depth feature")
        result.update(depth_cm=measured_depth_cm,depth_basis="reported_numeric_centimeters")
    if geometry is None or getattr(geometry,"srid",None)!=4326:
        result["errors"].append("Missing valid WGS84 geometry for features.")
        return result
    shape=to_shape(geometry)
    if not shape.is_valid or shape.is_empty:
        result["errors"].append("Invalid geometry for features.")
        return result
    provider=get_flood_location_provider()
    if provider.error or provider.city_boundary is None or not provider.city_boundary.covers(shape):
        result["errors"].append("Prediction location source unavailable or geometry outside Pasig.")
        return result
    point=shape.representative_point()
    result.update(coordinates=[point.x,point.y],geometry_sha256=hashlib.sha256(shape.wkb).hexdigest(),
        barangays=sorted(r.barangay for r,p in provider.records.values() if p.intersects(shape)),
        boundary_revision=provider.revision)
    if include_environment:
        result["environment"]=environment_context(point.x,point.y,clock)
        result["recorded_at"]=datetime.now(timezone.utc).isoformat()
    else:
        key=(round(point.x,3),round(point.y,3),clock.strftime("%Y-%m-%dT%H"))
        with _lock:
            cached=_cache.get(key)
        available=datetime.fromisoformat(cached[1]["captured_at"]) if cached else None
        result["environment"]=json.loads(json.dumps(cached[1])) if cached and timedelta(0)<=clock-cached[0]<timedelta(hours=1) and available<=clock else {
            "status":"not_captured","reason":"No current environmental cache at submission; historical availability is not invented."}
    return result
