import httpx
import logging
from typing import Optional, Any
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


# Centroids for all 30 official Pasig City barangays (SRID 4326: lat, lng)
PASIG_BARANGAY_CENTROIDS: dict[str, tuple[float, float]] = {
    "bagong ilog": (14.565254, 121.069000),
    "bagong katipunan": (14.558597, 121.075193),
    "bambang": (14.554780, 121.078653),
    "buting": (14.554785, 121.067741),
    "caniogan": (14.571951, 121.080520),
    "dela paz": (14.613554, 121.095793),
    "kalawaan": (14.551481, 121.086725),
    "kapasigan": (14.564499, 121.074174),
    "kapitolyo": (14.571258, 121.059267),
    "malinao": (14.557603, 121.078579),
    "manggahan": (14.603896, 121.099242),
    "maybunga": (14.573879, 121.098035),
    "oranbo": (14.573583, 121.064245),
    "palatiw": (14.563063, 121.084919),
    "pinagbuhatan": (14.557297, 121.090992),
    "pineda": (14.566581, 121.059579),
    "rosario": (14.590928, 121.087306),
    "sagad": (14.566274, 121.079462),
    "san antonio": (14.583057, 121.061801),
    "san joaquin": (14.552226, 121.075712),
    "san jose": (14.561303, 121.073645),
    "san miguel": (14.565805, 121.085476),
    "san nicolas": (14.560669, 121.080379),
    "santa cruz": (14.563571, 121.078921),
    "santa lucia": (14.584264, 121.101303),
    "santa rosa": (14.557324, 121.070366),
    "santo tomas": (14.562841, 121.081683),
    "santolan": (14.621693, 121.086314),
    "sumilang": (14.556648, 121.073891),
    "ugong": (14.584131, 121.073246),
}

# Major Metro Manila and Rizal city centroids for fallback matching
METRO_MANILA_CITY_CENTROIDS: dict[str, tuple[float, float]] = {
    "pasig": (14.5764, 121.0851),
    "quezon city": (14.6760, 121.0437),
    "manila": (14.5995, 120.9842),
    "makati": (14.5547, 121.0244),
    "marikina": (14.6507, 121.1029),
    "taguig": (14.5176, 121.0509),
    "mandaluyong": (14.5794, 121.0359),
    "san juan": (14.6019, 121.0355),
    "pasay": (14.5378, 120.9993),
    "paranaque": (14.5080, 120.9897),
    "las pinas": (14.4445, 120.9939),
    "muntinlupa": (14.4081, 121.0415),
    "cainta": (14.5786, 121.1219),
    "taytay": (14.5632, 121.1350),
    "antipolo": (14.5842, 121.1763),
}


def _clean_address_term(val: Any) -> str:
    """Normalizes address string by lowercasing and trimming common prefixes/suffixes."""
    if not val or not isinstance(val, str):
        return ""
    cleaned = val.strip().lower()
    for prefix in ["barangay ", "brgy. ", "brgy "]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    for suffix in [" city"]:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()
    return cleaned


def resolve_address_coordinates(
    barangay: Optional[str] = None,
    city: Optional[str] = None,
    province: Optional[str] = None
) -> Optional[tuple[float, float]]:
    """
    Resolves geographical coordinates (lat, lng) from a registered profile address.

    1. Checks offline 0ms Pasig barangay centroids first (fast path for primary deployment area).
    2. Falls back to Komoot Photon API for geocoding non-Pasig barangays.
    3. Falls back to city centroid if specific barangay geocode is unavailable.
    """
    bgy_clean = _clean_address_term(barangay)
    city_clean = _clean_address_term(city)

    # 1. Pasig barangay direct match
    if bgy_clean and (not city_clean or "pasig" in city_clean or "ncr" in city_clean or "metro manila" in city_clean):
        if bgy_clean in PASIG_BARANGAY_CENTROIDS:
            return PASIG_BARANGAY_CENTROIDS[bgy_clean]

    if bgy_clean in PASIG_BARANGAY_CENTROIDS:
        return PASIG_BARANGAY_CENTROIDS[bgy_clean]

    # 2. External geocoding via Photon
    query_parts = []
    if isinstance(barangay, str) and barangay.strip():
        query_parts.append(barangay.strip())
    if isinstance(city, str) and city.strip():
        query_parts.append(city.strip())
    if isinstance(province, str) and province.strip() and province.strip() != city:
        query_parts.append(province.strip())
    query_parts.append("Philippines")


    query = ", ".join(query_parts)
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(
                "https://photon.komoot.io/api/",
                params={"q": query, "limit": 1},
                headers={"User-Agent": "LANES/1.0"}
            )
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    coords = features[0]["geometry"]["coordinates"]
                    return (round(coords[1], 6), round(coords[0], 6))
    except Exception as exc:
        logger.warning(f"Photon forward geocode failed for query '{query}': {exc}")

    # 3. Fallback to city centroid
    if city_clean in METRO_MANILA_CITY_CENTROIDS:
        return METRO_MANILA_CITY_CENTROIDS[city_clean]

    return None
