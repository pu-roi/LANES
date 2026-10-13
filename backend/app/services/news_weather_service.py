"""Bounded public weather reads and deterministic adaptive collection policy."""
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import math
import re
import time
from zoneinfo import ZoneInfo
import httpx
from app.schemas.news_weather import AdaptiveDecision, WeatherBulletin, WeatherPoint, WeatherProvider

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
PAGASA_URL = "https://www.pagasa.dost.gov.ph/regional-forecast/ncrprsd"
PHT = ZoneInfo("Asia/Manila")
CATALOG_VERSION = "ncr-upstream-v1"
# Representative locality samples, not gauges, affected geometry, or city centroids.
# Upstream samples follow the San Mateo/Rodriguez corridor and Antipolo tributaries.
POINTS = tuple(WeatherPoint(locality=name, latitude=lat, longitude=lon, role=role,
    relevance="Pasig–Marikina watershed rain context" if role == "upstream" else "Metro Manila representative sample")
    for name, lat, lon, role in (
        ("Caloocan",14.6507,120.9676,"metro"), ("Las Piñas",14.4445,120.9939,"metro"),
        ("Makati",14.5547,121.0244,"metro"), ("Malabon",14.6681,120.9658,"metro"),
        ("Mandaluyong",14.5794,121.0359,"metro"), ("Manila",14.5995,120.9842,"metro"),
        ("Marikina",14.6507,121.1029,"metro"), ("Muntinlupa",14.4081,121.0415,"metro"),
        ("Navotas",14.6668,120.9417,"metro"), ("Parañaque",14.4793,121.0198,"metro"),
        ("Pasay",14.5378,121.0014,"metro"), ("Pasig",14.5731,121.0594,"metro"),
        ("Pateros",14.5454,121.0687,"metro"), ("Quezon City",14.6760,121.0437,"metro"),
        ("San Juan",14.6019,121.0355,"metro"), ("Taguig",14.5176,121.0509,"metro"),
        ("Valenzuela",14.7011,120.9830,"metro"), ("Rodriguez",14.7320,121.1450,"upstream"),
        ("San Mateo",14.6965,121.1218,"upstream"), ("Antipolo",14.6600,121.2300,"upstream")))


def choose_interval(providers: list[WeatherProvider], *, now: datetime,
                    last_positive_at: datetime | None = None, active_flood: bool = False) -> AdaptiveDecision:
    fresh = [p for p in effective_providers(providers, now) if timedelta(0) <= now-p.checked_at < timedelta(minutes=30)]
    if active_flood or any(p.status == "risk" for p in fresh):
        return AdaptiveDecision(interval_minutes=15, reason="Current active flood evidence" if active_flood else "Relevant weather risk",
                                last_positive_at=now)
    if last_positive_at and timedelta(0) <= now-last_positive_at < timedelta(minutes=60):
        return AdaptiveDecision(interval_minutes=15, reason="Monitoring after recent rain risk", last_positive_at=last_positive_at)
    if {p.name for p in fresh if p.status == "quiet"} == {"Open-Meteo", "PAGASA"} and len(fresh) == 2:
        return AdaptiveDecision(interval_minutes=60, reason="Both weather sources support quiet conditions", last_positive_at=last_positive_at)
    return AdaptiveDecision(interval_minutes=30, reason="Weather coverage incomplete, stale or unavailable", last_positive_at=last_positive_at)


def effective_providers(providers: list[WeatherProvider], now: datetime) -> list[WeatherProvider]:
    """Expiry is evaluated at read/decision time, without rewriting saved evidence."""
    result = []
    for provider in providers:
        if not timedelta(0) <= now-provider.checked_at < timedelta(minutes=30):
            provider = provider.model_copy(update={"status": "uncertain", "error_code": "weather_snapshot_stale"})
        elif provider.name == "PAGASA" and any(now >= b.valid_until for b in provider.bulletins):
            live = [b for b in provider.bulletins if now < b.valid_until and b.relevant]
            provider = provider.model_copy(update={"status": "risk" if live else "uncertain",
                "risk_locations": sorted({loc for b in live for loc in b.locations}), "error_code": "advisory_stale"})
        result.append(provider)
    return result


def parse_open_meteo(payload: object, *, now: datetime) -> WeatherProvider:
    """Validate every coordinate and hourly clock; partial positive risk still wins."""
    rows = payload if isinstance(payload, list) else [payload]
    risk, incomplete = [], len(rows) != len(POINTS)
    start = now.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    expected = [start + timedelta(hours=i) for i in range(3)]
    for index, point in enumerate(POINTS):
        try:
            row = rows[index]
            if abs(float(row["latitude"])-point.latitude) > .2 or abs(float(row["longitude"])-point.longitude) > .2:
                raise ValueError("coordinate_mismatch")
            hourly = row["hourly"]
            if row.get("utc_offset_seconds", 0) != 0 or hourly.get("precipitation") is None:
                raise ValueError("clock_or_precipitation_missing")
            if row.get("hourly_units", {}).get("precipitation") != "mm":
                raise ValueError("invalid_units")
            parsed_times = [datetime.fromisoformat(t) for t in hourly["time"]]
            times = [t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc) for t in parsed_times]
            amounts = hourly["precipitation"]
            if len(times) != len(amounts) or len(set(times)) != len(times):
                raise ValueError("invalid_slots")
            for slot in expected:
                if slot not in times:
                    incomplete = True
                    continue
                amount = amounts[times.index(slot)]
                if isinstance(amount, bool) or not isinstance(amount, (float, int)) or not math.isfinite(amount) or amount < 0:
                    incomplete = True
                elif amount >= .2 and point.locality not in risk:
                    risk.append(point.locality)
        except (TypeError, ValueError, KeyError, IndexError, AttributeError):
            incomplete = True
    return WeatherProvider(name="Open-Meteo", source_url=OPEN_METEO_URL, checked_at=now,
        status="risk" if risk else "uncertain" if incomplete else "quiet", risk_locations=risk,
        error_code="weather_coverage_incomplete" if incomplete else None)


class _AdvisorySections(HTMLParser):
    """Read only named official sections; discard comments, scripts and navigation."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: dict[str, list[str]] = {"rainfalls": [], "thunderstorms": []}
        self.stack: list[tuple[str, str | None, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        section = dict(attrs).get("id")
        parent = self.stack[-1] if self.stack else ("", None, False)
        current = section if section in self.sections else parent[1]
        ignored = parent[2] or tag in ("script", "style")
        if tag in ("br", "hr", "img", "input", "meta", "link"):
            if current and not ignored:
                self.sections[current].append("\n")
            return
        self.stack.append((tag, current, ignored))

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                if self.stack[i][1] and tag in ("div", "p"):
                    self.sections[self.stack[i][1]].append("\n")
                del self.stack[i:]
                break

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1][1] and not self.stack[-1][2]:
            self.sections[self.stack[-1][1]].append(data)


_CLOCK = r"(\d{1,2}:\d{2}\s*[AP]M)"
_DATE = r"(\d{1,2}\s+[A-Za-z]+[,]?\s+\d{4})"


def _dated_clock(value: str) -> datetime:
    cleaned = re.sub(r"\s+", " ", value.replace(",", "")).strip().upper()
    for pattern in ("%I:%M %p %d %B %Y", "%I:%M%p %d %B %Y", "%I:%M %p %d %b %Y"):
        try:
            return datetime.strptime(cleaned, pattern).replace(tzinfo=PHT).astimezone(timezone.utc)
        except ValueError:
            continue
    raise ValueError("advisory_timestamp_invalid")


def _bulletin(block: str, section: str, now: datetime) -> WeatherBulletin:
    issued = re.search(r"Issued\s*(?:at|on)?\s*:?\s*"+_CLOCK+r"\s*[,]?\s*"+_DATE, block, re.I)
    if not issued:
        raise ValueError("advisory_timestamp_missing")
    issued_at = _dated_clock(f"{issued[1]} {issued[2]}")
    if issued_at > now+timedelta(minutes=5):
        raise ValueError("advisory_timestamp_future")
    valid_until = issued_at + timedelta(hours=3 if section == "rainfalls" else 2)
    explicit = re.search(r"Valid\s*(?:until|through)\s*:?\s*"+_CLOCK+r"\s*[,]?\s*"+_DATE, block, re.I)
    next_update = re.search(r"(?:next\s+(?:warning|advisory|update).*?(?:issued\s+at|at)|Valid\s+until\s*:?)\s*"+_CLOCK+r"\s*(today|tomorrow)?", block, re.I|re.S)
    if explicit:
        valid_until = _dated_clock(f"{explicit[1]} {explicit[2]}")
    elif next_update:
        local = issued_at.astimezone(PHT)
        hour = datetime.strptime(re.sub(r"\s+", "", next_update[1].upper()), "%I:%M%p")
        end = local.replace(hour=hour.hour, minute=hour.minute, second=0, microsecond=0)
        if (next_update[2] or "").lower() == "tomorrow" or end <= local:
            end += timedelta(days=1)
        valid_until = end.astimezone(timezone.utc)
    if valid_until <= issued_at or valid_until-issued_at > timedelta(hours=24) or now >= valid_until:
        raise ValueError("advisory_stale")
    title = re.search(r"(?:Heavy\s+Rainfall\s+Warning|Rainfall\s+Advisory|Thunderstorm\s+Advisory)[^\n]*", block, re.I)
    no_advisory = re.search(r"\bno\s+(?:heavy\s+rainfall\s+warning|rainfall\s+advisory|thunderstorm\s+advisory)\b", block, re.I)
    if not title:
        raise ValueError("advisory_unrecognized")
    # Province-level Rizal is conservative upstream coverage. Credits, forecasts
    # and other tabs cannot supply a location because only this block is read.
    locations = [name for name, pattern in (("Metro Manila",r"\b(?:Metro\s+Manila|NCR)\b"), ("Rizal upstream",r"\bRizal\b"))
                 if re.search(pattern, block[issued.end():], re.I)]
    # Advisories may enumerate affected cities instead of naming the region.
    # Normalize diacritics while retaining the canonical sampled locality label.
    import unicodedata
    body = unicodedata.normalize("NFKD", block[issued.end():])
    body = "".join(c for c in body if not unicodedata.combining(c))
    for point in POINTS:
        locality = unicodedata.normalize("NFKD", point.locality)
        locality = "".join(c for c in locality if not unicodedata.combining(c))
        pattern = r"\b"+re.escape(locality).replace(r"\ ",r"\s+")+r"\b"
        if re.search(pattern, body, re.I):
            locations.append(point.locality)
    return WeatherBulletin(identity=title[0][:160], issued_at=issued_at, valid_until=valid_until,
        relevant=bool(locations) and not no_advisory, locations=locations)


def parse_pagasa(html: str, *, now: datetime) -> WeatherProvider:
    parser = _AdvisorySections()
    parser.feed(html)
    bulletins, errors = [], []
    for section, fragments in parser.sections.items():
        body = "".join(fragments).strip()
        # Separate consecutive bulletins, keeping dated no-advisory notices intact.
        blocks = re.split(r"(?=^[ \t]*(?:Heavy Rainfall Warning|Rainfall Advisory|Thunderstorm Advisory))", body, flags=re.M)
        blocks = [b.strip() for b in blocks if b.strip()]
        if not blocks:
            errors.append("advisory_section_missing")
        section_bulletins, section_errors = [], []
        for block in blocks:
            try:
                section_bulletins.append(_bulletin(block, section, now))
            except ValueError as exc:
                section_errors.append(str(exc))
        bulletins.extend(section_bulletins)
        # Archived bulletins coexist with current ones on the official page.
        # Their expiry is not a coverage error when this section has live data.
        errors.extend(error for error in section_errors if error != "advisory_stale" or not section_bulletins)
    locations = sorted({loc for bulletin in bulletins if bulletin.relevant for loc in bulletin.locations})
    return WeatherProvider(name="PAGASA", source_url=PAGASA_URL, checked_at=now,
        status="risk" if locations else "uncertain" if errors else "quiet", risk_locations=locations,
        bulletins=bulletins, error_code=sorted(set(errors))[0] if errors else None)


def fetch_weather(client: httpx.Client, *, now: datetime) -> list[WeatherProvider]:
    providers = []
    for name, url in (("Open-Meteo", OPEN_METEO_URL), ("PAGASA", PAGASA_URL)):
        try:
            started = time.monotonic()
            params = {"latitude": ",".join(str(p.latitude) for p in POINTS),
                      "longitude": ",".join(str(p.longitude) for p in POINTS), "hourly": "precipitation",
                      "forecast_hours": 3, "timezone": "UTC"} if name == "Open-Meteo" else None
            with client.stream("GET", url, params=params, headers={"User-Agent": "LANES weather scheduling/1.0", "Cache-Control": "no-cache"}) as response:
                response.raise_for_status()
                raw = bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 2_000_000 or time.monotonic()-started > 10:
                        raise ValueError("weather_response_too_large")
            if name == "Open-Meteo":
                import json
                provider = parse_open_meteo(json.loads(raw), now=now)
            else:
                provider = parse_pagasa(raw.decode("utf-8", errors="replace"), now=now)
        except (httpx.HTTPError, ValueError):
            provider = WeatherProvider(name=name, source_url=url, checked_at=now, status="unavailable", error_code="weather_fetch_failed")
        providers.append(provider)
    return providers
