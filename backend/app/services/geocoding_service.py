import httpx
import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ParsedLocation(BaseModel):
    street: Optional[str] = None
    barangay: Optional[str] = None
    city: Optional[str] = None
    display_name: Optional[str] = None


def _clean_barangay_name(raw: Optional[str]) -> Optional[str]:
    """Strips leading 'Barangay', 'Brgy.', etc. for consistent clean storage."""
    if not raw:
        return None
    cleaned = raw.strip()
    for prefix in ["Barangay ", "Brgy. ", "Brgy "]:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    return cleaned if cleaned else None


async def reverse_geocode_structured(lat: float, lng: float) -> Optional[ParsedLocation]:
    """
    Reverse geocodes coordinates into structured street, barangay, and city fields.
    Tries OpenStreetMap Nominatim first, with fallback to Photon (Komoot).
    """
    # 1. Try Nominatim (OSM)
    nominatim_url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "zoom": 17,  # Street-level precision
        "addressdetails": 1,
    }
    headers = {
        "User-Agent": "LANESApp/1.0 (contact@lanes-navigation.org)"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(nominatim_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})

                # Extract street
                street = (
                    address.get("road")
                    or address.get("street")
                    or address.get("pedestrian")
                    or address.get("highway")
                    or address.get("path")
                )

                # Extract barangay (suburb, quarter, neighbourhood, village in PH OSM data)
                barangay_raw = (
                    address.get("quarter")
                    or address.get("suburb")
                    or address.get("neighbourhood")
                    or address.get("village")
                    or address.get("city_district")
                )
                barangay = _clean_barangay_name(barangay_raw)

                # Extract city/municipality
                city = (
                    address.get("city")
                    or address.get("town")
                    or address.get("municipality")
                )

                display_name = data.get("display_name")

                if street or barangay or city or display_name:
                    return ParsedLocation(
                        street=street,
                        barangay=barangay,
                        city=city,
                        display_name=display_name
                    )
    except Exception as e:
        logger.warning(f"Nominatim reverse geocode failed ({e}). Attempting Photon fallback...")

    # 2. Fallback to Photon
    photon_url = f"https://photon.komoot.io/reverse?lon={lng}&lat={lat}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(photon_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    props = features[0].get("properties", {})
                    street = props.get("street") or props.get("name")
                    barangay = _clean_barangay_name(
                        props.get("district") or props.get("locality")
                    )
                    city = props.get("city")
                    
                    parts = [street, barangay, city]
                    display_name = ", ".join([p for p in parts if p]) or None

                    return ParsedLocation(
                        street=street,
                        barangay=barangay,
                        city=city,
                        display_name=display_name
                    )
    except Exception as e:
        logger.error(f"Photon reverse geocode failed: {e}")

    return None


async def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """
    Reverse geocodes coordinates into a human readable address string.
    Backwards-compatible helper returning a formatted location string.
    """
    parsed = await reverse_geocode_structured(lat, lng)
    if not parsed:
        return None
    return parsed.display_name or parsed.street
