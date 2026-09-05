import re
import httpx
from typing import List, Dict
from pydantic import BaseModel
from cachetools import TTLCache, cached

# Cache results for 1 hour
_national_cache = TTLCache(maxsize=1, ttl=3600)
_pasig_cache = TTLCache(maxsize=1, ttl=3600)


class HotlineNumber(BaseModel):
    raw: str
    display: str


class HotlineGroup(BaseModel):
    name: str
    numbers: List[HotlineNumber]


class FullHotlineResponse(BaseModel):
    national: List[HotlineGroup]
    pasig_city: List[HotlineGroup]
    pasig_barangay: List[HotlineGroup]


def _clean_number(raw: str) -> str:
    """Strip non-digit chars for tel: links."""
    return re.sub(r"[^\d+]", "", raw.strip())


# ---------------------------------------------------------------------------
# National hotlines — ehotlines.e.gov.ph
# ---------------------------------------------------------------------------

@cached(_national_cache)
def fetch_and_parse_hotlines() -> List[HotlineGroup]:
    try:
        response = httpx.get("https://ehotlines.e.gov.ph/", timeout=10.0, verify=False)
        response.raise_for_status()
        html = response.text

        chunks = html.split('bg-white rounded-2xl shadow-sm overflow-hidden')
        data = []
        for chunk in chunks[1:]:
            name_match = re.search(
                r'flex-1 font-semibold text-sm text-gray-900 leading-snug">\s*([^<]+)\s*</span>', chunk
            )
            name = name_match.group(1).strip() if name_match else "Unknown"

            number_matches = re.findall(
                r'<a href="tel:([^"]+)"[^>]*>.*?<span class="text-sm">([^<]+)</span>', chunk
            )
            numbers = [{"raw": raw.strip(), "display": disp.strip()} for raw, disp in number_matches]

            if numbers:
                data.append(HotlineGroup(name=name, numbers=numbers))

        return data
    except Exception as e:
        print(f"Failed to scrape national hotlines: {e}")
        return []


# ---------------------------------------------------------------------------
# Pasig City hotlines — pasigcity.gov.ph
# The og:description is a single concatenated string, so we parse it with
# known patterns rather than line-by-line splitting.
# ---------------------------------------------------------------------------

# City-level agencies: (display_name, regex_to_match_name_and_number_in_bl)
_CITY_AGENCIES = [
    ("Pasig City DRRMO",            r"PASIG CITY DRRMO EMERGENCY HOTLINE\s*([\d\s\-\u2013]+?)(?=[A-Z]{3,})"),
    ("PNP \u2013 Pasig",            r"PHILIPPINE NATIONAL POLICE\s*([\d\s\-\u2013]+?)(?=[A-Z]{3,})"),
    ("Bureau of Fire Protection",   r"BUREAU OF FIRE PROTECTION - PASIG\s*([\d\s\-\u2013]+?)(?=[A-Z]{3,})"),
    ("Pasig City Children's Hosp.", r"PASIG CITY CHILDREN.S HOSPITAL\s*([\d\s\-\u2013|]+?)(?=[A-Z]{3,})"),
    ("Pasig City General Hospital", r"PASIG CITY GENERAL HOSPITAL\s*([\d\s\-\u2013|]+?)(?=BARANGAY|$)"),
]

# Barangays that use a space-separated format (no colon) — handle manually
_KAPASIGAN_PATTERN = re.compile(r'KAPASIGAN\s+([\d\s\-]+?)(?=[A-Z]|$)')



def _parse_pasig_text(text: str) -> Dict[str, List[HotlineGroup]]:
    """
    Parse the single-line og:description blob from Pasig city website.
    Format: "AGENCY NAME NUMBER | NUMBER NEXT_AGENCY..."
    Barangays after "BARANGAYS*:" as "BRGY_NAME: NUM | NUMBRGY2_NAME: NUM..."
    """
    city_groups: List[HotlineGroup] = []
    barangay_groups: List[HotlineGroup] = []

    # ---- City-level ---------------------------------------------------------
    for display_name, pattern in _CITY_AGENCIES:
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            continue
        raw_nums = m.group(1).strip()
        parts = [p.strip() for p in re.split(r'\|', raw_nums) if p.strip() and _clean_number(p)]
        numbers = [HotlineNumber(raw=_clean_number(p), display=p.strip()) for p in parts]
        if numbers:
            city_groups.append(HotlineGroup(name=display_name, numbers=numbers))

    # ---- Barangay-level -----------------------------------------------------
    brgy_section_m = re.search(r"BARANGAYS\*?:(.+?)(?:\*Will|\Z)", text, re.DOTALL | re.IGNORECASE)
    if not brgy_section_m:
        return {"pasig_city": city_groups, "pasig_barangay": barangay_groups}

    brgy_text = brgy_section_m.group(1)

    # Split on barangay-name tokens: sequences of 2+ uppercase letters (possibly with spaces)
    # followed by a colon. Use re.split with a capturing group to keep the names.
    tokens = re.split(r'([A-Z][A-Z\s]{2,}):', brgy_text)
    skip_labels = {
        'globe', 'smart', 'brgy', 'fire', 'ambulance', 'security',
        'patient', 'landline', 'rescue', 'brigade', 'hall', 'transport',
        'santolan', 'manggahan',
    }

    i = 1  # skip leading empty string
    while i < len(tokens) - 1:
        name_raw = tokens[i].strip()
        nums_raw = tokens[i + 1].strip() if i + 1 < len(tokens) else ''

        i += 2

        # Skip sub-labels
        if any(skip in name_raw.lower() for skip in skip_labels):
            continue

        # Strip trailing uppercase letters + any space-separated word-like noise
        nums_clean = re.sub(r'[A-Z][A-Z0-9\s]{3,}$', '', nums_raw).strip()
        # Also strip anything that looks like a next barangay name glued to the last digit
        nums_clean = re.sub(r'\d+[A-Z]{2,}.*$', lambda m: m.group(0)[:re.search(r'[A-Z]{2,}', m.group(0)).start()], nums_clean).strip()

        if not _clean_number(nums_clean):
            continue

        # Split individual numbers on |
        parts = [p.strip() for p in re.split(r'\|', nums_clean) if p.strip() and _clean_number(p)]
        numbers = [HotlineNumber(raw=_clean_number(p), display=p) for p in parts]

        if numbers:
            name_display = name_raw.title()
            barangay_groups.append(HotlineGroup(name=name_display, numbers=numbers))

    # Handle KAPASIGAN which uses space-separated format without colon
    kap_m = _KAPASIGAN_PATTERN.search(brgy_text)
    if kap_m:
        kap_num = kap_m.group(1).strip()
        if _clean_number(kap_num):
            barangay_groups.append(HotlineGroup(
                name="Kapasigan",
                numbers=[HotlineNumber(raw=_clean_number(kap_num), display=kap_num)]
            ))

    return {"pasig_city": city_groups, "pasig_barangay": sorted(barangay_groups, key=lambda g: g.name)}


@cached(_pasig_cache)
def fetch_and_parse_pasig_hotlines() -> Dict[str, List[HotlineGroup]]:
    try:
        response = httpx.get(
            "https://pasigcity.gov.ph/news-and-releases/emergency-contact-numbers-ng-lungsod-ng-pasig-393",
            timeout=15.0,
            verify=False,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LANES-Bot/1.0)"},
        )
        response.raise_for_status()
        html = response.text

        # There are two og:description tags; we want the one containing the hotlines
        og_matches = re.findall(r'<meta[^>]+property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', html)
        og_matches += re.findall(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']og:description["\']', html)

        # Pick the one that actually contains hotline data
        og_text = next((m for m in og_matches if "DRRMO" in m or "HOTLINE" in m or "8643" in m), None)
        if not og_text:
            print("Pasig: Could not find hotlines og:description")
            return {"pasig_city": [], "pasig_barangay": []}
        # Decode HTML entities
        og_text = (og_text
                   .replace("&#39;", "'")
                   .replace("&amp;", "&")
                   .replace("&quot;", '"')
                   .replace("&#x27;", "'"))

        return _parse_pasig_text(og_text)
    except Exception as e:
        print(f"Failed to scrape Pasig hotlines: {e}")
        return {"pasig_city": [], "pasig_barangay": []}


def fetch_full_hotlines() -> FullHotlineResponse:
    national = fetch_and_parse_hotlines()
    pasig = fetch_and_parse_pasig_hotlines()
    return FullHotlineResponse(
        national=national,
        pasig_city=pasig.get("pasig_city", []),
        pasig_barangay=pasig.get("pasig_barangay", []),
    )
