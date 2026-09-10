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


FALLBACK_NATIONAL_HOTLINES = [
    HotlineGroup(
        name="National Emergency Hotline",
        numbers=[HotlineNumber(raw="911", display="911")]
    ),
    HotlineGroup(
        name="National Disaster Risk Reduction and Management Council (NDRRMC)",
        numbers=[
            HotlineNumber(raw="0289115061", display="(02) 8911-5061 to 65"),
            HotlineNumber(raw="0289111406", display="(02) 8911-1406"),
            HotlineNumber(raw="0289122665", display="(02) 8912-2665"),
            HotlineNumber(raw="0289125668", display="(02) 8912-5668"),
            HotlineNumber(raw="0289111873", display="(02) 8911-1873"),
        ]
    ),
    HotlineGroup(
        name="Red Cross",
        numbers=[
            HotlineNumber(raw="143", display="143 (Hotline)"),
            HotlineNumber(raw="0285278385", display="(02) 8527-8385 to 95"),
            HotlineNumber(raw="0285270000", display="(02) 8527-0000"),
        ]
    ),
    HotlineGroup(
        name="Philippine National Police (PNP)",
        numbers=[
            HotlineNumber(raw="117", display="117 (Emergency)"),
            HotlineNumber(raw="0287220650", display="(02) 8722-0650"),
            HotlineNumber(raw="09178475757", display="0917-847-5757 (Text Hotline)"),
        ]
    ),
    HotlineGroup(
        name="Bureau of Fire Protection (BFP)",
        numbers=[
            HotlineNumber(raw="0284260219", display="(02) 8426-0219"),
            HotlineNumber(raw="0284260246", display="(02) 8426-0246"),
        ]
    ),
    HotlineGroup(
        name="Philippine Coast Guard",
        numbers=[
            HotlineNumber(raw="0285278481", display="(02) 8527-8481 to 89"),
            HotlineNumber(raw="09177243682", display="0917-724-3682 (Text Hotline)"),
        ]
    ),
    HotlineGroup(
        name="Metro Manila Development Authority (MMDA)",
        numbers=[
            HotlineNumber(raw="136", display="136 (Hotline)"),
            HotlineNumber(raw="0288824151", display="(02) 8882-4151 to 77"),
        ]
    ),
    HotlineGroup(
        name="Department of Social Welfare and Development",
        numbers=[
            HotlineNumber(raw="09189122813", display="0918-912-2813 (Text Hotline)"),
            HotlineNumber(raw="0289318101", display="(02) 8931-8101 to 07"),
            HotlineNumber(raw="0288563665", display="(02) 8856-3665 (Disaster Response)"),
        ]
    ),
]


# ---------------------------------------------------------------------------
# National hotlines — ehotlines.e.gov.ph
# ---------------------------------------------------------------------------

def fetch_and_parse_hotlines() -> List[HotlineGroup]:
    if "national" in _national_cache:
        return _national_cache["national"]

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

        if data:
            _national_cache["national"] = data
            return data
        print("Warning: Scraped national hotlines empty, using fallback.")
        return FALLBACK_NATIONAL_HOTLINES
    except Exception as e:
        print(f"Failed to scrape national hotlines: {e}. Using fallback.")
        return FALLBACK_NATIONAL_HOTLINES


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


FALLBACK_PASIG_CITY_HOTLINES = [
    HotlineGroup(
        name="Pasig City DRRMO",
        numbers=[HotlineNumber(raw="86430000", display="8643-0000")]
    ),
    HotlineGroup(
        name="PNP – Pasig",
        numbers=[HotlineNumber(raw="0286410433", display="(02) 8641-0433")]
    ),
    HotlineGroup(
        name="Bureau of Fire Protection",
        numbers=[HotlineNumber(raw="0286412815", display="(02) 8641-2815")]
    ),
    HotlineGroup(
        name="Pasig City Children's Hosp.",
        numbers=[HotlineNumber(raw="0286432222", display="(02) 8643-2222")]
    ),
    HotlineGroup(
        name="Pasig City General Hospital",
        numbers=[HotlineNumber(raw="0286433333", display="(02) 8643-3333")]
    ),
]


def fetch_and_parse_pasig_hotlines() -> Dict[str, List[HotlineGroup]]:
    if "pasig" in _pasig_cache:
        return _pasig_cache["pasig"]

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
            print("Pasig: Could not find hotlines og:description, using fallback")
            return {"pasig_city": FALLBACK_PASIG_CITY_HOTLINES, "pasig_barangay": []}
        # Decode HTML entities
        og_text = (og_text
                   .replace("&#39;", "'")
                   .replace("&amp;", "&")
                   .replace("&quot;", '"')
                   .replace("&#x27;", "'"))

        parsed = _parse_pasig_text(og_text)
        if parsed.get("pasig_city") or parsed.get("pasig_barangay"):
            _pasig_cache["pasig"] = parsed
            return parsed
        return {"pasig_city": FALLBACK_PASIG_CITY_HOTLINES, "pasig_barangay": []}
    except Exception as e:
        print(f"Failed to scrape Pasig hotlines: {e}. Using fallback.")
        return {"pasig_city": FALLBACK_PASIG_CITY_HOTLINES, "pasig_barangay": []}


def fetch_full_hotlines() -> FullHotlineResponse:
    national = fetch_and_parse_hotlines()
    pasig = fetch_and_parse_pasig_hotlines()
    return FullHotlineResponse(
        national=national,
        pasig_city=pasig.get("pasig_city", []),
        pasig_barangay=pasig.get("pasig_barangay", []),
    )
