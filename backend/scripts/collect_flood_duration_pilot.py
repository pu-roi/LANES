"""Bounded, offline Pasig research capture. Never publishes or writes application data.

Collection and extraction use the Python standard library; figures use Matplotlib.
Sources and reviewed interpretation rules are supplied as JSON. Cached immutable
HTML/text captures permit offline rebuilds.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib import error, request, robotparser
from urllib.parse import urlparse


REVISION = "pasig-duration-pilot-v3"
AGENT = "LANES-Research-Pilot/1.0"
MONTHS = {name: n for n, name in enumerate(
    ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"), 1)}
DATE_PATTERNS = (
    re.compile(r"(" + "|".join(MONTHS) + r")\s+(\d{1,2}),?\s+(20\d{2})", re.I),
    re.compile(r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(20\d{2})", re.I),
)
CLOCK = re.compile(r"\b(\d{1,2}):(\d{2})\s*(AM|PM|NN)\b", re.I)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCK = {"p", "h1", "h2", "h3", "li", "div", "br"}
BARANGAY_REFERENCE = Path(__file__).resolve().parents[2] / "data/pasig_barangay_reference.csv"


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()


def barangay_key(value: str) -> str:
    name = re.sub(r"\s*\([^)]*\)\s*$", "", value.split("*", 1)[0]).strip(" .")
    key = re.sub(r"[^a-z0-9]", "", norm(name).lower())
    return "Sta. Lucia" if key in {"stalucia", "santalucia"} else name


def location_key(value: str) -> str:
    # Only remove an explicit trailing barangay qualifier and punctuation.
    road = re.split(r"\b(?:Brgy\.?|Barangay)\s*", value, flags=re.I)[0]
    return re.sub(r"[^a-z0-9]", "", norm(road).lower())


def date_in(value: str) -> str | None:
    for index, pattern in enumerate(DATE_PATTERNS):
        match = pattern.search(value)
        if match:
            month, day, year = match.groups() if index == 0 else (match[2], match[1], match[3])
            return datetime(int(year), MONTHS[month.title()], int(day)).date().isoformat()
    return None


def time_in(value: str, day: str | None) -> str | None:
    match = CLOCK.search(value)
    if not match or not day:
        return None
    hour, minute, period = int(match[1]), int(match[2]), match[3].upper()
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        return None
    hour = hour % 12 + (12 if period in ("PM", "NN") else 0)
    return f"{day}T{hour:02}:{minute:02}:00+08:00"


class ArticleText(HTMLParser):
    """Only main Pasig article column; excludes navigation/related news/scripts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, bool]] = []
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = (dict(attrs).get("class") or "").split()
        parent_active = self.stack[-1][1] if self.stack else False
        parent_skip = self.stack[-1][2] if self.stack else False
        inside_section = any(t == "section" and active for t, active, _ in self.stack)
        active = parent_active or (tag == "section" and "newspage-content" in classes)
        skip = parent_skip or tag in {"script", "style"} or "newspage-related" in classes
        in_column = any(t == "article-column" for t, _, _ in self.stack)
        is_column = inside_section and tag == "div" and "col-lg-9" in classes
        if not skip and (in_column or is_column) and tag in BLOCK:
            self.parts.append("\n")
        if tag not in VOID:
            self.stack.append(("article-column" if is_column else tag, active, skip))

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID:
            return
        # article-column stands for the captured root div.
        for index in range(len(self.stack) - 1, -1, -1):
            actual = "div" if self.stack[index][0] == "article-column" else self.stack[index][0]
            if actual == tag:
                if any(t == "article-column" for t, _, _ in self.stack) and tag in BLOCK:
                    self.parts.append("\n")
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if any(t == "article-column" for t, _, _ in self.stack) and not any(s for _, _, s in self.stack):
            self.parts.append(data)

    def lines(self) -> list[str]:
        return [norm(line) for line in "".join(self.parts).splitlines() if norm(line)]


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dump_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def collect(seeds: list[dict[str, Any]], output: Path, refresh: bool) -> list[dict[str, Any]]:
    manifest_path = output / "source_manifest.json"
    old = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    by_id = {row["source_id"]: row for row in old}
    output.mkdir(parents=True, exist_ok=True)
    robots_url = "https://pasigcity.gov.ph/robots.txt"
    try:
        with request.urlopen(request.Request(robots_url, headers={"User-Agent": AGENT}), timeout=25) as response:
            robots_text = response.read().decode("utf-8")
        rules = robotparser.RobotFileParser()
        rules.parse(robots_text.splitlines())
        dump_json(output / "access_policy.json", {"url": robots_url, "fetched_at": datetime.now(timezone.utc).isoformat(), "text": robots_text, "reuse_terms": "not verified; robots permission is not a reuse license"})
    except (error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Cannot verify robots rules; collection stopped: {exc}") from exc
    for seed in seeds:
        sid, url = seed["source_id"], seed["url"]
        if not re.fullmatch(r"[A-Z0-9-]+", sid):
            raise ValueError(f"Unsafe source ID: {sid}")
        if urlparse(url).netloc != "pasigcity.gov.ph" or not url.startswith("https://pasigcity.gov.ph/news-and-releases/"):
            raise ValueError(f"Out-of-scope source URL: {url}")
        cached = by_id.get(sid)
        if cached and cached.get("status") == "captured" and not refresh:
            raw = output / cached["html_path"]
            text_path = output / cached["text_path"]
            if raw.is_file() and text_path.is_file() and hashlib.sha256(raw.read_bytes()).hexdigest() == cached["html_sha256"] and hashlib.sha256(text_path.read_bytes()).hexdigest() == cached["text_sha256"]:
                print(f"cached {sid}", flush=True)
                continue
        if not rules.can_fetch(AGENT, url):
            by_id[sid] = {**seed, "status": "robots_disallowed"}
            dump_json(manifest_path, list(by_id.values()))
            continue
        row: dict[str, Any] = {**seed, "fetched_at": datetime.now(timezone.utc).isoformat(), "status": "failed"}
        for attempt in range(2):
            try:
                with request.urlopen(request.Request(url, headers={"User-Agent": AGENT}), timeout=25) as response:
                    payload = response.read(3_000_001)
                    row.update(http_status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type"))
                if len(payload) > 3_000_000:
                    raise ValueError("Source exceeds 3 MB bounded capture limit")
                if "text/html" not in (row["content_type"] or "").lower():
                    raise ValueError("Expected HTML response")
                if urlparse(row["final_url"]).netloc != "pasigcity.gov.ph":
                    raise ValueError("Redirect leaves approved publisher")
                digest = hashlib.sha256(payload).hexdigest()
                parser = ArticleText()
                parser.feed(payload.decode("utf-8"))
                lines = parser.lines()
                if len(lines) < 3:
                    raise ValueError("Missing article main-column text")
                html_path = f"sources/{sid}.{digest[:12]}.html"
                text_path = f"sources/{sid}.{digest[:12]}.txt"
                (output / "sources").mkdir(exist_ok=True)
                (output / html_path).write_bytes(payload)
                text_bytes = ("\n".join(lines) + "\n").encode("utf-8")
                (output / text_path).write_bytes(text_bytes)
                row.update(status="captured", title=lines[0], displayed_publication_date=date_in(lines[1]), html_path=html_path, text_path=text_path, html_sha256=digest, text_sha256=hashlib.sha256(text_bytes).hexdigest(), capture_version=digest[:12], admission_status="pilot_candidates_not_training_admitted", reuse_terms="not verified")
                print(f"captured {sid}: {len(lines)} lines", flush=True)
                break
            except (error.URLError, TimeoutError, OSError, UnicodeError, ValueError) as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
                print(f"fetch failure {sid}: {row['error']}", flush=True)
                if attempt == 0:
                    time.sleep(2)
        by_id[sid] = row
        dump_json(manifest_path, list(by_id.values()))
        time.sleep(0.6)
    return list(by_id.values())


def base_observation(source: dict[str, Any], line: int, evidence: str, clock: str | None, clock_evidence: str) -> dict[str, Any]:
    identity = f"{source['source_id']}|{source['capture_version']}|{line}|{evidence}"
    return {"observation_id": "OBS-" + hashlib.sha256(identity.encode()).hexdigest()[:16], "source_id": source["source_id"], "capture_version": source["capture_version"], "source_url": source["url"], "episode_group": source["episode_group"], "city": "Pasig", "barangay_raw": "", "barangay": "", "location_raw": "", "observation_at": clock or "", "clock_evidence": clock_evidence, "source_line_start": line, "evidence": evidence, "status": "", "depth_raw": "", "depth_cm_low": "", "depth_cm_high": "", "passability_raw": "", "review_status": "candidate", "clearance_scope": "", "flags": ""}


def depth_bounds(raw: str) -> tuple[float | str, float | str]:
    # No numeric conversion of knee/waist/gutter words. Preserve original text.
    repeated = re.search(r"(\d+(?:\.\d+)?)\s*(cm|inch(?:es)?|ft|feet|foot)\s*[-–]\s*(\d+(?:\.\d+)?)\s*\2\b", raw, re.I)
    if repeated:
        factor = 1 if repeated[2].lower() == "cm" else (30.48 if repeated[2].lower() in {"ft", "feet", "foot"} else 2.54)
        low, high = float(repeated[1]), float(repeated[3])
        return (round(low * factor, 4), round(high * factor, 4)) if high >= low else ("", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*(cm|inch(?:es)?|ft|feet|foot)\b", raw, re.I)
    if not match:
        return "", ""
    factor = 1 if match[3].lower() == "cm" else (30.48 if match[3].lower() in {"ft", "feet", "foot"} else 2.54)
    low, high = float(match[1]), float(match[2] or match[1])
    if high < low:
        return "", ""
    # Mixed feet-and-inch values cannot be truncated at the first feet value.
    if match[3].lower() in {"ft", "feet", "foot"}:
        # Parenthetical alternate units must not become additive depth.
        remainder = raw[match.end():].split("(", 1)[0]
        extra = re.search(r"(?:and\s+)?(\d+(?:\.\d+)?)\s*inch(?:es)?", remainder, re.I)
        if extra and not match[2]:
            return round(low * factor + float(extra[1]) * 2.54, 4), round(high * factor + float(extra[1]) * 2.54, 4)
    return round(low * factor, 4), round(high * factor, 4)


def alternate_depth_review(raw: str) -> tuple[float | str, float | str, str]:
    """Retain reported metric features with explicit rounding/conflict qualifiers."""
    low, high = depth_bounds(raw)
    outside, separator, inside = raw.partition("(")
    if not separator:
        return low, high, ""
    # Numeric-adjacent units (10.64cm, 4inches) are legitimate spellings.
    metric = r"(?<![A-Za-z])cm\b"
    imperial = r"(?<![A-Za-z])(?:inch(?:es)?|ft|feet|foot)\b"
    if re.search(metric, outside, re.I) and re.search(imperial, inside, re.I):
        metric_text, imperial_text = outside, inside
    elif re.search(metric, inside, re.I) and re.search(imperial, outside, re.I):
        metric_text, imperial_text = inside, outside
    else:
        return low, high, ""
    metric_bounds, imperial_bounds = depth_bounds(metric_text), depth_bounds(imperial_text)
    if not all(isinstance(v, (int, float)) for v in (*metric_bounds, *imperial_bounds)):
        return "", "", "alternate_units_unparsed_requires_review"
    differences = [abs(a - b) for a, b in zip(metric_bounds, imperial_bounds)]
    if max(differences) <= 0.25:
        return low, high, ""
    # Only a source-reported whole-centimeter scalar matching nearest rounding
    # receives this qualifier. Decimal metric disagreements remain unresolved.
    metric_scalar = re.fullmatch(r"\s*(\d+)\s*cm\s*\)?\s*", metric_text, re.I)
    if metric_scalar and imperial_bounds[0] == imperial_bounds[1] and max(differences) <= 0.5:
        return metric_bounds[0], metric_bounds[1], "alternate_unit_rounding_uncertain"
    return "", "", "source_alternate_units_disagree"


def barangay_headings() -> set[str]:
    """Accept unprefixed headings only when they match the existing Pasig reference."""
    with BARANGAY_REFERENCE.open(encoding="utf-8-sig", newline="") as handle:
        names = {barangay_key(row["barangay_name"]).lower() for row in csv.DictReader(handle)}
    return names


def observations(source: dict[str, Any], output: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text_path = output / source["text_path"]
    text_payload = text_path.read_bytes()
    if hashlib.sha256(text_payload).hexdigest() != source["text_sha256"]:
        raise ValueError(f"Capture text checksum mismatch: {source['source_id']}")
    lines = text_payload.decode("utf-8").splitlines()
    title_date = date_in(lines[0])
    clock = time_in(lines[0], title_date)
    clock_evidence = lines[0] if clock else ""
    day = title_date
    barangay = ""
    flood_list_context = ""
    pending: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    known_barangays = barangay_headings()
    for number, line in enumerate(lines[2:], 3):
        new_day = date_in(line)
        if new_day:
            day = new_day
        new_clock = time_in(line, day)
        # Only full dated/as-of headings, not unrelated response subsection clocks.
        if new_clock and (new_day or re.search(r"\bas of\b", line, re.I)):
            clock, clock_evidence = new_clock, line
            pending, barangay, flood_list_context = None, "", ""
            continue
        # Explicit flood-attributed closure lists; bridge/collision closure stays separate.
        if "due to significant flooding" in line.lower():
            flood_list_context = line
            named = re.search(r"(?:advised|advise) that (.+?)\s+(?:in\s+)?Brgy\.\s*(.+?)\s+is still", line, re.I)
            if named:
                row = base_observation(source, number, line, clock, clock_evidence)
                row.update(status="flood_observed", location_raw=named[1].strip(), barangay_raw=named[2].strip(), barangay=barangay_key(named[2]), passability_raw="NOT PASSABLE to light vehicles", flags="depth_not_reported")
                rows.append(row)
                flood_list_context = ""
            continue
        if line.startswith("-") and flood_list_context:
            inline = re.search(r"\b(?:Brgy\.?|Barangay)\s*(.+)$", line, re.I)
            if inline:
                row = base_observation(source, number, flood_list_context + " | " + line, clock, clock_evidence)
                row.update(status="flood_observed", location_raw=line.lstrip("- "), barangay_raw=inline[1].strip(" ."), barangay=barangay_key(inline[1]), passability_raw="NOT PASSABLE to light vehicles", flags="depth_not_reported")
                rows.append(row)
                continue
        if flood_list_context and not line.startswith("-"):
            flood_list_context = ""
        if line.startswith("-") and re.search(r"\b(?:Brgy\.?|Barangay)\s+", line, re.I):
            exceptions.append({"source_id": source["source_id"], "line": number, "reason": "bullet_without_explicit_flood_attribution_requires_review", "evidence": line})
            continue
        if re.search(r"\bhumupa\b|\bsubsided\b|\breceded\b", line, re.I):
            row = base_observation(source, number, line, clock, clock_evidence)
            row.update(status="clearance_candidate", clearance_scope="summary_requires_review", flags="no_exact_physical_clearance_time")
            rows.append(row)
            pending = None
            continue
        heading = re.match(r"^(?:Brgy\.?|Barangay)\s+(.+)$", line, re.I)
        if heading or barangay_key(line).lower() in known_barangays:
            barangay = heading[1].strip(" .") if heading else line.strip(" .")
            pending = None
            continue
        location = re.match(r"^\d+(?:\s*[.,]+\s*|\s+)(.+)$", line)
        if location:
            pending = base_observation(source, number, line, clock, clock_evidence)
            pending["location_raw"] = location[1].strip()
            inline = re.search(r"\b(?:Brgy\.?|Barangay)\s*(.+)$", location[1], re.I)
            pending["barangay_raw"] = inline[1].strip(" .") if inline else barangay
            pending["barangay"] = barangay_key(pending["barangay_raw"])
            continue
        water = re.match(r"^(?:Water\s*Level|Flood\s*Depth)\s*:?\s*(.+)$", line, re.I)
        if water:
            if pending is None or pending.get("status"):
                exceptions.append({"source_id": source["source_id"], "line": number, "reason": "depth_without_supported_numbered_location", "evidence": line})
                continue
            pending.update(status="flood_observed", depth_raw=water[1], evidence=pending["evidence"] + " | " + line)
            low, high, unit_flag = alternate_depth_review(water[1])
            pending["depth_cm_low"], pending["depth_cm_high"] = low, high
            flags = []
            if unit_flag:
                flags.append(unit_flag)
                exceptions.append({"source_id": source["source_id"], "line": number, "reason": unit_flag, "evidence": line})
            if pending["depth_cm_low"] == "":
                if not unit_flag:
                    flags.append("qualitative_depth_no_numeric_conversion")
            if not pending["observation_at"]:
                flags.append("missing_observation_clock")
            if not pending["barangay"]:
                flags.append("missing_barangay")
            pending["flags"] = ";".join(flags)
            rows.append(pending)
            continue
        if re.search(r"\bpassable\b", line, re.I) and pending and pending.get("status"):
            pending["passability_raw"] = line
            pending["evidence"] += " | " + line
    # Empty rows aren't interpreted as dry; non-numbered prose is a review exception.
    if not rows:
        exceptions.append({"source_id": source["source_id"], "line": "", "reason": "no_supported_numbered_depth_or_clearance_rows", "evidence": "inspect captured text"})
    return rows, exceptions


def build(seeds: list[dict[str, Any]], output: Path, reviewed_rules: list[dict[str, Any]], source_bundle: Path | None = None, figures: bool = True) -> dict[str, Any]:
    capture_root = source_bundle or output
    manifest = json.loads((capture_root / "source_manifest.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    for source in manifest:
        if source.get("status") != "captured":
            exceptions.append({"source_id": source["source_id"], "line": "", "reason": source["status"], "evidence": source.get("error", "")})
            continue
        parsed, issues = observations(source, capture_root)
        rows.extend(parsed)
        exceptions.extend(issues)
    # Record exact repeated rows and same-clock measurement conflicts, never erase raw evidence.
    seen: dict[tuple[str, ...], dict[str, Any]] = {}
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["status"] != "flood_observed":
            continue
        key = (row["episode_group"], row["barangay"].lower(), location_key(row["location_raw"]), row["observation_at"])
        groups[key].append(row)
        full_key = (*key, row["depth_raw"], row["passability_raw"])
        if full_key in seen:
            row["flags"] = ";".join(filter(None, [row["flags"], "duplicate_of:" + seen[full_key]["observation_id"]]))
        else:
            seen[full_key] = row
    for group in groups.values():
        if len({r["depth_raw"] for r in group}) > 1:
            for row in group:
                row["flags"] = ";".join(filter(None, [row["flags"], "same_clock_depth_conflict"]))
    candidates: list[dict[str, Any]] = []
    for rule in reviewed_rules:
        clear = [r for r in rows if r["source_id"] == rule["clear_source_id"] and r["status"] == "clearance_candidate" and rule["clear_evidence_contains"] in r["evidence"]]
        if len(clear) != 1:
            exceptions.append({"source_id": rule["clear_source_id"], "line": "", "reason": "review_rule_clearance_evidence_not_unique", "evidence": rule["rule_id"]})
            continue
        upper = datetime.fromisoformat(rule["clearance_upper_at"])
        clear_row = clear[0]
        clear_row.update(review_status="summary_scope_reviewed", clearance_scope=rule["scope"])
        wet = [r for r in rows if r["episode_group"] == rule["episode_group"] and r["status"] == "flood_observed" and r["barangay"].lower() == barangay_key(rule["barangay"]).lower() and r["observation_at"] and datetime.fromisoformat(r["observation_at"]) < upper]
        by_location: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in wet:
            by_location[location_key(row["location_raw"])].append(row)
        for location, history in by_location.items():
            history.sort(key=lambda r: r["observation_at"])
            first, last = history[0], history[-1]
            # Only final supported wet rows selected by reviewed source/time rules qualify.
            if last["source_id"] != rule["last_wet_source_id"] or last["observation_at"] != rule["last_wet_at"]:
                continue
            elapsed = (datetime.fromisoformat(last["observation_at"]) - datetime.fromisoformat(first["observation_at"])).total_seconds() / 3600
            upper_remaining = (upper - datetime.fromisoformat(last["observation_at"])).total_seconds() / 3600
            identity = rule["rule_id"] + "|" + location
            candidates.append({"candidate_id": "INC-" + hashlib.sha256(identity.encode()).hexdigest()[:16], "episode_group": rule["episode_group"], "city": "Pasig", "barangay": last["barangay"], "location_raw": last["location_raw"], "first_observed_wet_at": first["observation_at"], "last_observed_wet_at": last["observation_at"], "reported_clearance_upper_at": rule["clearance_upper_at"], "clearance_upper_inclusive": rule["upper_inclusive"], "remaining_hours_low": 0, "remaining_low_inclusive": False, "remaining_hours_high": round(upper_remaining, 6), "observed_span_hours": round(elapsed, 6), "onset_at": "", "total_duration_hours": "", "last_wet_observation_id": last["observation_id"], "clearance_observation_id": clear_row["observation_id"], "clear_source_id": clear_row["source_id"], "support_observation_ids": ";".join(r["observation_id"] for r in history), "review_rule_id": rule["rule_id"], "review_status": "candidate_summary_link_not_training_admitted", "clearance_scope": rule["scope"], "limitations": "unknown_onset;summary_clearance;continuity_assumed_between_observations;locations_share_storm_and_clearance"})
    fields = list(base_observation({"source_id": "", "capture_version": "", "url": "", "episode_group": ""}, 0, "", None, ""))
    dump_csv(output / "observations.csv", rows, fields)
    dump_json(output / "observations.json", rows)
    dump_csv(output / "candidate_incidents.csv", candidates, list(candidates[0]) if candidates else ["candidate_id"])
    dump_json(output / "candidate_incidents.json", candidates)
    for row in rows:
        if "same_clock_depth_conflict" in row["flags"]:
            exceptions.append({"source_id": row["source_id"], "line": row["source_line_start"], "reason": "same_clock_depth_conflict", "evidence": row["evidence"]})
    dump_csv(output / "exceptions.csv", exceptions, ["source_id", "line", "reason", "evidence"])
    by_year = Counter(r["observation_at"][:4] for r in rows if r["observation_at"])
    summary = {"revision": REVISION, "built_at": datetime.now(timezone.utc).isoformat(), "seeded_sources": len(seeds), "captured_sources": sum(s.get("status") == "captured" for s in manifest), "failed_sources": sum(s.get("status") != "captured" for s in manifest), "observations": len(rows), "flood_observations": sum(r["status"] == "flood_observed" for r in rows), "clearance_summary_observations": sum(r["status"] == "clearance_candidate" for r in rows), "duplicate_flags": sum("duplicate_of:" in r["flags"] for r in rows), "conflict_flags": sum("same_clock_depth_conflict" in r["flags"] for r in rows), "missing_clock_rows": sum(not r["observation_at"] for r in rows), "candidate_incident_bounds": len(candidates), "candidate_clearance_episode_groups": len({r["episode_group"] for r in candidates}), "candidate_episode_groups": len({r["episode_group"] for r in rows}), "barangays": sorted({r["barangay"] for r in rows if r["barangay"]}), "observation_year_counts": dict(sorted(by_year.items())), "exceptions": len(exceptions), "training_admitted_incidents": 0, "model_trained": False, "readiness": "pilot_only_not_validated_training_data", "limits": ["selected reports; not exhaustive archive", "episode groups are candidate continuity groups, not proved independent storms", "summary clearance lacks individual measured timestamps", "no known flood onset for candidate incidents", "no matched weather exports yet", "2021-2023 archive coverage unverified", "no local ML accuracy estimate"]}
    dump_json(output / "coverage.json", summary)
    if figures:
        from plot_flood_duration_pilot import render_pilot_figures
        render_pilot_figures(output)
    # Human-readable citations for every captured/failed source with observation links.
    citations = ["# Captured Pasig pilot sources", "", "Generated from source_manifest.json. Reuse terms remain unverified. Capture is not training admission.", ""]
    for source in manifest:
        citations += [f"## {source['source_id']}", "", f"- Publisher: City Government of Pasig. [{source.get('title', source['source_id'])}]({source['url']}).", f"- Status: {source['status']}. Retrieved: {source.get('fetched_at', 'unavailable')}."]
        if source.get("status") == "captured":
            ids = [r["observation_id"] for r in rows if r["source_id"] == source["source_id"]]
            html_link = Path(os.path.relpath(capture_root / source["html_path"], output)).as_posix()
            text_link = Path(os.path.relpath(capture_root / source["text_path"], output)).as_posix()
            citations += [f"- Displayed publication date: {source.get('displayed_publication_date') or 'unknown'}; embedded observation clocks retained separately.", f"- [HTML capture]({html_link}); [normalized article text]({text_link}).", f"- HTML SHA-256: `{source['html_sha256']}`.", f"- Text SHA-256: `{source['text_sha256']}`.", f"- Capture version: `{source['capture_version']}`; observation IDs: {', '.join(ids) or 'none parsed'}." ]
        else:
            citations.append(f"- Failure/restriction: {source.get('error', source['status'])}.")
        citations.append("")
    (output / "sources.md").write_text("\n".join(citations), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--review-rules", type=Path)
    parser.add_argument("--source-bundle", type=Path, help="Read immutable captures from another bundle; write derived outputs separately")
    parser.add_argument("--skip-figures", action="store_true", help="Build source-linked tables with the standard library only")
    parser.add_argument("--collect", action="store_true", help="Fetch approved seed pages; otherwise rebuild offline")
    parser.add_argument("--refresh", action="store_true", help="Create a new capture version when source changed")
    args = parser.parse_args()
    seeds = json.loads(args.seeds.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    if args.collect:
        if args.source_bundle:
            parser.error("--source-bundle is offline-only; collect into its own output bundle")
        collect(seeds, args.output, args.refresh)
    rules = json.loads(args.review_rules.read_text(encoding="utf-8")) if args.review_rules else []
    build(seeds, args.output, rules, args.source_bundle, figures=not args.skip_figures)


if __name__ == "__main__":
    main()
