"""Offline NCR research capture and evidence-linked reviewed observation export.

Reads explicit source/rule JSON; never accesses application settings or databases.
Publisher bodies are captured separately from interpretation and training admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib import error, request, robotparser
from urllib.parse import urlparse

from collect_flood_duration_pilot import BLOCK, VOID, base_observation, depth_bounds, dump_csv, dump_json, norm

AGENT = "LANES-Research-Pilot/1.0"
HOSTS = {"www.gmanetwork.com", "www.pna.gov.ph", "rmn.ph", "www.onenews.ph"}
CITIES = ("Caloocan", "Las Piñas", "Makati", "Malabon", "Mandaluyong", "Manila", "Marikina", "Muntinlupa", "Navotas", "Parañaque", "Pasay", "Pasig", "Quezon City", "San Juan", "Taguig", "Valenzuela", "Pateros")


class PublisherBody(HTMLParser):
    def __init__(self, host: str) -> None:
        super().__init__(convert_charrefs=True)
        self.host = host
        self.stack: list[tuple[str, bool, bool]] = []
        self.parts: list[str] = []
        self.metadata: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag == "meta":
            key = attributes.get("property") or attributes.get("name")
            if key and attributes.get("content"):
                self.metadata[key] = attributes["content"] or ""
        parent_active = self.stack[-1][1] if self.stack else False
        parent_skip = self.stack[-1][2] if self.stack else False
        root = (self.host == "www.gmanetwork.com" and "story_main" in classes) or (self.host == "www.pna.gov.ph" and ("article-body" in classes or "article_body" in classes)) or (self.host == "rmn.ph" and "td-post-content" in classes) or (self.host == "www.onenews.ph" and "articlebody" in attributes)
        active = parent_active or root
        skip = parent_skip or tag in {"script", "style", "nav", "aside"} or bool(set(classes) & {"advertisement", "related-stories", "story-tags", "ads"})
        if active and not skip and tag in BLOCK:
            self.parts.append("\n")
        if tag not in VOID:
            self.stack.append((tag, active, skip))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                if self.stack[index][1] and not self.stack[index][2] and tag in BLOCK:
                    self.parts.append("\n")
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1][1] and not self.stack[-1][2]:
            self.parts.append(data)

    def lines(self) -> list[str]:
        return [norm(line) for line in "".join(self.parts).splitlines() if norm(line)]


def fetch(url: str) -> tuple[bytes, str]:
    with request.urlopen(request.Request(url, headers={"User-Agent": AGENT}), timeout=25) as response:
        payload = response.read(3_000_001)
        final_url = response.url
    if len(payload) > 3_000_000:
        raise ValueError("Capture exceeds 3 MB limit")
    if urlparse(final_url).netloc != urlparse(url).netloc:
        raise ValueError("Capture redirected outside approved publisher")
    return payload, final_url


def capture(seeds: list[dict[str, Any]], output: Path) -> None:
    manifest_path = output / "source_manifest.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    manifest = {row["source_id"]: row for row in previous}
    policy_path = output / "access_policy.json"
    access: dict[str, Any] = json.loads(policy_path.read_text(encoding="utf-8")) if policy_path.exists() else {}
    policies: dict[str, robotparser.RobotFileParser | None] = {}
    for seed in seeds:
        sid, url = seed["source_id"], seed["url"]
        host = urlparse(url).netloc
        if host not in HOSTS or urlparse(url).scheme != "https" or not re.fullmatch(r"[A-Z0-9-]+", sid):
            raise ValueError("Unapproved publisher or unsafe source identity")
        cached = manifest.get(sid)
        if cached and cached.get("status") == "captured":
            if all((output / cached[f"{kind}_path"]).is_file() and hashlib.sha256((output / cached[f"{kind}_path"]).read_bytes()).hexdigest() == cached[f"{kind}_sha256"] for kind in ("html", "text")):
                print(f"cached {sid}", flush=True)
                continue
        row = {**seed, "status": "failed", "fetched_at": datetime.now(timezone.utc).isoformat()}
        try:
            if host not in policies:
                policy_url = f"https://{host}/robots.txt"
                try:
                    payload, _ = fetch(policy_url)
                    policy_text = payload.decode("utf-8")
                    policy = robotparser.RobotFileParser()
                    policy.parse(policy_text.splitlines())
                    policies[host] = policy
                    access[host] = {"url": policy_url, "text": policy_text, "fetched_at": datetime.now(timezone.utc).isoformat(), "reuse_terms": "not verified; robots permission is not a reuse license"}
                except (error.URLError, TimeoutError, OSError, ValueError) as exc:
                    policies[host] = None
                    access[host] = {"url": policy_url, "error": str(exc)}
                dump_json(output / "access_policy.json", access)
            policy = policies[host]
            if policy is None or not policy.can_fetch(AGENT, url):
                raise ValueError("Publisher robots rules unavailable or disallow this page")
            for attempt in range(2):
                try:
                    payload, final_url = fetch(url)
                    break
                except (error.URLError, TimeoutError, OSError, ValueError) as exc:
                    if attempt == 1:
                        raise
                    time.sleep(1)
            parser = PublisherBody(host)
            parser.feed(payload.decode("utf-8"))
            body = parser.lines()
            if len(body) < 2:
                raise ValueError("Supported publisher story body missing; no global text fallback")
            title = norm(parser.metadata.get("og:title", seed.get("title", sid)))
            published = parser.metadata.get("article:published_time", "")
            lines = [title, "Publication metadata: " + (published or "unavailable; see source HTML"), *body]
            digest = hashlib.sha256(payload).hexdigest()
            html_path = f"sources/{sid}.{digest[:12]}.html"
            text_path = f"sources/{sid}.{digest[:12]}.txt"
            text_bytes = ("\n".join(lines) + "\n").encode("utf-8")
            (output / "sources").mkdir(parents=True, exist_ok=True)
            (output / html_path).write_bytes(payload)
            (output / text_path).write_bytes(text_bytes)
            row.update(status="captured", title=title, publication_metadata=published, final_url=final_url, html_path=html_path, text_path=text_path, html_sha256=digest, text_sha256=hashlib.sha256(text_bytes).hexdigest(), capture_version=digest[:12], reuse_terms="not verified", admission_status="research_candidates_not_training_admitted")
            print(f"captured {sid}: {len(body)} body lines", flush=True)
        except (error.URLError, TimeoutError, OSError, UnicodeError, ValueError) as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            print(f"capture failed {sid}: {row['error']}", flush=True)
        manifest[sid] = row
        dump_json(manifest_path, list(manifest.values()))
        time.sleep(0.6)


def reviewed_rows(output: Path, rules: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest = json.loads((output / "source_manifest.json").read_text(encoding="utf-8"))
    sources = {row["source_id"]: row for row in manifest}
    rows: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    for rule in rules:
        sid = rule["source_id"]
        source = sources.get(sid)
        if not source or source.get("status") != "captured":
            exceptions.append({"source_id": sid, "reason": "rule_source_not_captured", "evidence": rule["rule_id"]})
            continue
        payload = (output / source["text_path"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != source["text_sha256"]:
            raise ValueError(f"Text checksum mismatch: {sid}")
        if rule["capture_version"] != source["capture_version"]:
            raise ValueError(f"Reviewed rule belongs to another capture: {rule['rule_id']}")
        lines = payload.decode("utf-8").splitlines()
        refs = []
        evidence = []
        for expected in rule.get("evidence_lines", []):
            number, expected_text = expected["line"], expected["text"]
            if number < 1 or number > len(lines) or lines[number - 1] != expected_text:
                raise ValueError(f"Reviewed line changed: {rule['rule_id']}")
            refs.append(number)
            evidence.append(expected_text)
        for fragment in rule.get("evidence_contains", []):
            hits = [(number, line) for number, line in enumerate(lines, 1) if fragment in line]
            if len(hits) != 1:
                raise ValueError(f"Evidence is not unique: {rule['rule_id']} {fragment!r}")
            refs.append(hits[0][0])
            evidence.append(hits[0][1])
        html_payload = (output / source["html_path"]).read_bytes()
        if hashlib.sha256(html_payload).hexdigest() != source["html_sha256"]:
            raise ValueError(f"HTML checksum mismatch: {sid}")
        html_text = html_payload.decode("utf-8")
        for fragment in rule.get("html_evidence_contains", []):
            if html_text.count(fragment) != 1:
                raise ValueError(f"HTML time/date context not unique: {rule['rule_id']}")
        if not refs:
            raise ValueError("Observation requires story evidence")
        if rule["city"] not in CITIES:
            raise ValueError("Unsupported NCR locality")
        observed = rule.get("observation_at", "")
        if observed:
            parsed = datetime.fromisoformat(observed)
            if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 28800:
                raise ValueError("Reviewed observation clock requires explicit Asia/Manila offset")
        row = base_observation(source, min(refs), " | ".join(evidence), observed or None, rule["clock_basis"])
        for key in ("city", "barangay", "location_raw", "status", "depth_raw", "passability_raw"):
            row[key] = rule.get(key, "")
        row["barangay_raw"] = rule.get("barangay", "")
        row["depth_cm_low"], row["depth_cm_high"] = depth_bounds(row["depth_raw"])
        if "up to" in row["depth_raw"].lower():
            row["depth_cm_low"] = ""
        if row["status"] != "flood_observed":
            # Updated MMDA lists retain old depth/passability beside SUBSIDED.
            row["depth_cm_low"], row["depth_cm_high"] = "", ""
        row["geography_basis"] = rule.get("geography_basis", "explicit publisher city section")
        row["html_date_evidence"] = " | ".join(rule.get("html_evidence_contains", []))
        row.update(observation_date=rule["observation_date"], source_line_refs=";".join(map(str, sorted(set(refs)))), review_rule_id=rule["rule_id"], review_status="source_reviewed_candidate_not_training_admitted", flags=rule.get("flags", ""), clearance_scope=rule.get("clearance_scope", ""))
        outside, separator, inside = row["depth_raw"].partition("(")
        imperial = r"\b(?:inch(?:es)?|ft|feet)\b"
        alternate = separator and ((re.search(r"\bcm\b", outside, re.I) and re.search(imperial, inside, re.I)) or (re.search(r"\bcm\b", inside, re.I) and re.search(imperial, outside, re.I)))
        if alternate and row["status"] == "flood_observed":
            first, second = depth_bounds(outside), depth_bounds(inside)
            if all(isinstance(v, (int, float)) for v in (*first, *second)) and any(abs(a-b) > .25 for a,b in zip(first, second)):
                row["depth_cm_low"], row["depth_cm_high"] = "", ""
                row["flags"] = ";".join(filter(None, [row["flags"], "source_alternate_units_disagree"]))
                exceptions.append({"source_id": sid, "reason": "source_alternate_units_disagree", "evidence": rule["rule_id"] + " | " + row["depth_raw"]})
        if row["status"] == "flood_observed" and row["depth_cm_high"] == "" and "source_alternate_units_disagree" not in row["flags"]:
            row["flags"] = ";".join(filter(None, [row["flags"], "qualitative_or_missing_depth_no_numeric_conversion"]))
        if not observed:
            row["flags"] = ";".join(filter(None, [row["flags"], "observation_date_only_clock_unknown"]))
        row["observation_id"] = "OBS-" + hashlib.sha256((sid + "|" + source["capture_version"] + "|" + rule["rule_id"]).encode()).hexdigest()[:16]
        rows.append(row)
    return rows, exceptions


def location_key(value: str) -> str:
    value = re.sub(r"\s+", " ", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()).strip()
    return re.sub(r"^(?:barangay|brgy\.?)\s+", "", value)


def document_rows(output: Path) -> list[dict[str, Any]]:
    rules_path = output / "document_review_rules.json"
    if not rules_path.exists():
        return []
    manifest = {s["source_id"]: s for s in json.loads((output / "document_manifest.json").read_text(encoding="utf-8"))}
    rows = []
    for rule in json.loads(rules_path.read_text(encoding="utf-8")):
        source = manifest[rule["source_id"]]
        for kind in ("pdf", "text"):
            if hashlib.sha256((output / source[f"{kind}_path"]).read_bytes()).hexdigest() != source[f"{kind}_sha256"]:
                raise ValueError("Document capture checksum mismatch")
        if source["capture_version"] != rule["capture_version"]:
            raise ValueError("Document reviewed version mismatch")
        text = (output / source["text_path"]).read_text(encoding="utf-8")
        # Stored layout text has explicit PAGE delimiters. Rules retain exact
        # page/row evidence, rather than transferring occurrence into clearance.
        page_match = re.search(r"(?:^|\n\n)PAGE " + str(rule["source_page"]) + r"\n(.*?)(?=\n\nPAGE |\Z)", text, re.S)
        if not page_match or page_match[1].count(rule["evidence"]) != 1 or source["source_id"] != rule["source_id"]:
            raise ValueError("Reviewed document row not uniquely supported")
        row = {**rule, "observation_id": "DOC-" + hashlib.sha256((source["source_id"]+source["capture_version"]+rule["rule_id"]).encode()).hexdigest()[:16], "source_url": source["url"], "publisher": source["publisher"], "source_version": source["capture_version"], "source_bundle": str(output.as_posix()), "observation_at": "", "status": "historical_flood_incident_reported", "depth_raw": "", "depth_cm_low": "", "depth_cm_high": "", "passability_raw": "", "flags": "occurrence_not_clearance_clock;barangay_or_area_scope_not_road_section", "latest_status_as_of": source["report_as_of"], "review_status": "document_reviewed_candidate_not_training_admitted", "clock_basis": "Table occurrence time retained separately; status update clock unknown", "episode_group": "NCR-2021-FABIAN-HABAGAT"}
        rows.append(row)
    return rows


def paired_bounds(rows: list[dict[str, Any]], pair_rules: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_rule = {row.get("review_rule_id"): row for row in rows if row.get("review_rule_id")}
    bounds = []
    exceptions = []
    for rule in pair_rules:
        wet, clear = by_rule[rule["wet_rule_id"]], by_rule[rule["clear_rule_id"]]
        if wet["status"] != "flood_observed" or clear["status"] != "clearance_candidate" or wet["city"] != clear["city"] or wet["storm_group"] != clear["storm_group"] or location_key(wet["location_raw"]) != location_key(clear["location_raw"]):
            raise ValueError(f"Unsupported explicit pairing: {rule['pair_id']}")
        minutes = (datetime.fromisoformat(clear["observation_at"]) - datetime.fromisoformat(wet["observation_at"])).total_seconds() / 60
        if minutes <= 0:
            raise ValueError(f"Nonpositive explicit pairing: {rule['pair_id']}")
        bounds.append({"pair_id": rule["pair_id"], "city": wet["city"], "location_raw": wet["location_raw"], "storm_group": wet["storm_group"], "last_wet_at": wet["observation_at"], "reported_subsided_at": clear["observation_at"], "onset_at": "", "remaining_minutes_low": 0, "remaining_minutes_high": minutes, "interval": f"(0, {minutes:g}] minutes", "wet_observation_id": wet["observation_id"], "clear_observation_id": clear["observation_id"], "wet_source_id": wet["source_id"], "clear_source_id": clear["source_id"], "match_basis": rule["match_basis"], "review_status": "candidate_report_based_interval_not_training_admitted", "limitation": "Unknown onset; source clocks and continuity need qualification; not total flood duration or model accuracy"})
    # Retain contradictory chronological lists for review rather than deriving
    # a negative duration or silently dropping either observation.
    for clear in rows:
        if clear["status"] != "clearance_candidate" or not clear["observation_at"]:
            continue
        for wet in rows:
            if wet["status"] == "flood_observed" and wet["observation_at"] and wet["city"] == clear["city"] and wet["storm_group"] == clear["storm_group"] and location_key(wet["location_raw"]) == location_key(clear["location_raw"]) and wet["observation_at"] >= clear["observation_at"]:
                exceptions.append({"source_id": clear["source_id"], "reason": "clearance_at_or_before_matched_wet_report", "evidence": f"{wet['observation_id']} {wet['observation_at']} | {clear['observation_id']} {clear['observation_at']}"})
                for affected in (wet, clear):
                    affected["flags"] = ";".join(filter(None, [affected["flags"], "temporal_source_conflict_requires_review"]))
    return bounds, exceptions


def build(output: Path, rules: list[dict[str, Any]], base: Path | None, pair_rules: list[dict[str, Any]]) -> None:
    extra, exceptions = reviewed_rows(output, rules)
    rows = []
    if base:
        rows = json.loads((base / "observations.json").read_text(encoding="utf-8"))
        for row in rows:
            row["observation_date"] = row["observation_at"][:10]
            row["source_bundle"] = str(base.as_posix())
    for row in extra:
        row["source_bundle"] = str(output.as_posix())
    rows.extend(extra)
    historical = document_rows(output)
    rows.extend(historical)
    dump_json(output / "historical_incidents.json", historical)
    dump_csv(output / "historical_incidents.csv", historical, list(dict.fromkeys(key for row in historical for key in row)) or ["observation_id"])
    for row in rows:
        # Conservative date-based grouping avoids treating one multi-city report
        # as independent storms. Longer events require further grouped review.
        row["storm_group"] = "NCR-" + row["observation_date"]
    bounds, pair_exceptions = paired_bounds(rows, pair_rules)
    exceptions.extend(pair_exceptions)
    dump_json(output / "candidate_clearance_bounds.json", bounds)
    dump_csv(output / "candidate_clearance_bounds.csv", bounds, list(bounds[0]) if bounds else ["pair_id"])
    fields = list(dict.fromkeys(key for row in rows for key in row)) or ["observation_id"]
    dump_json(output / "observations.json", rows)
    dump_csv(output / "observations.csv", rows, fields)
    pasig = [r for r in rows if r["city"] == "Pasig"]
    dump_json(output / "pasig_observations.json", pasig)
    dump_csv(output / "pasig_observations.csv", pasig, fields)
    dump_csv(output / "exceptions.csv", exceptions, ["source_id", "reason", "evidence"])
    manifest = json.loads((output / "source_manifest.json").read_text(encoding="utf-8"))
    counts = {city: dict(sorted(Counter(r["observation_date"][:4] for r in rows if r["city"] == city).items())) for city in CITIES}
    coverage = {"revision": "ncr-reviewed-capture-v1", "built_at": datetime.now(timezone.utc).isoformat(), "target_years": list(range(2021, 2027)), "cutoff_date": "2026-10-04", "supplement_captured_sources": sum(s["status"] == "captured" for s in manifest), "supplement_failed_sources": sum(s["status"] != "captured" for s in manifest), "supplement_observations": len(extra), "total_observations": len(rows), "pasig_observations": len(pasig), "date_only_observations": sum(not r["observation_at"] for r in rows), "city_year_observation_counts": counts, "base_bundle": str(base.as_posix()) if base else None, "training_admitted_incidents": 0, "model_trained": False, "archive_exhaustive": False, "limitations": ["Reviewed source selection is not an exhaustive year/city archive", "Multiple observations can share one storm", "Date-only records cannot supply hourly clearance targets", "No new exact onset or total flood durations inferred", "Base pilot interval candidates remain separately traceable"]}
    coverage.update(covered_lgus=sum(bool(value) for value in counts.values()), total_lgus=len(CITIES), new_candidate_clearance_pairs=len(bounds), new_pair_date_groups=len({b["storm_group"] for b in bounds}), temporal_conflict_exceptions=len(pair_exceptions), supplement_exception_count=len(exceptions), storm_group_basis="Conservative NCR observation-date grouping; longer storms still require event reconciliation")
    coverage.update(total_evidence_rows=len(rows), direct_report_observations=len(rows)-len(historical), historical_incident_records=len(historical), pasig_direct_observations=len(pasig)-sum(r["city"] == "Pasig" for r in historical), pasig_historical_incidents=sum(r["city"] == "Pasig" for r in historical), historical_city_year_counts={city:dict(Counter(r["observation_date"][:4] for r in historical if r["city"] == city)) for city in CITIES}, city_year_evidence_counts=counts)
    coverage["city_year_observation_counts"] = {city:dict(Counter(r["observation_date"][:4] for r in rows if r["city"] == city and r["status"] != "historical_flood_incident_reported")) for city in CITIES}
    coverage["pasig_evidence_rows"] = len(pasig)
    coverage["pasig_observations"] = coverage["pasig_direct_observations"]
    coverage["total_observations"] = len(rows)-len(historical)
    coverage["date_only_observations"] = sum(not r["observation_at"] for r in rows if r["status"] != "historical_flood_incident_reported")
    coverage["limitations"].append("Historical document occurrence clocks are not wet observation or clearance clocks; kept as a separate record type")
    if base:
        coverage["base_observations_sha256"] = hashlib.sha256((base / "observations.json").read_bytes()).hexdigest()
    dump_json(output / "coverage.json", coverage)
    citations = ["# Metro Manila flood-report capture sources", "", "Source-linked research observations, not training-admitted duration labels.", "", f"Base Pasig captures: [original citations](../{base.name}/sources.md)." if base else "", ""]
    for source in manifest:
        citations += [f"## {source['source_id']}", "", f"- Publisher: {source['publisher']}; [{source.get('title', source['source_id'])}]({source['url']}).", f"- Status: {source['status']}; retrieved {source['fetched_at']}."]
        if source["status"] == "captured":
            ids = [r["observation_id"] for r in extra if r["source_id"] == source["source_id"]]
            citations += [f"- [HTML]({source['html_path']}); [normalized story text]({source['text_path']}).", f"- HTML SHA-256 `{source['html_sha256']}`; text SHA-256 `{source['text_sha256']}`; version `{source['capture_version']}`.", f"- Publication metadata: {source['publication_metadata'] or 'unavailable'}; observation clocks are separate.", f"- Observation IDs: {', '.join(ids) or 'none admitted to observation register; capture retained'}. Reuse terms unverified."]
        else:
            citations.append(f"- Failure: {source['error']}.")
        citations.append("")
    document_manifest = output / "document_manifest.json"
    if document_manifest.exists():
        for source in json.loads(document_manifest.read_text(encoding="utf-8")):
            ids = [r["observation_id"] for r in historical if r["source_id"] == source["source_id"]]
            citations += [f"## {source['source_id']}", "", f"- Publisher: {source['publisher']}; [{source['title']}]({source['url']}).", f"- Status: {source['status']}; retrieved {source['fetched_at']}; report as of {source['report_as_of']}.", f"- [Original PDF]({source['pdf_path']}); [layout text]({source['text_path']}); [inspected page 47](sources/NDRRMC-20210801-page47.png).", f"- PDF SHA-256 `{source['pdf_sha256']}`; text SHA-256 `{source['text_sha256']}`; version `{source['capture_version']}`.", f"- Retained records: {', '.join(ids)}.", "- Page 47: 12 Pasig and two Pateros historical incident rows. Occurrence times and Subsided status remain separate; no clearance clock or exact duration inferred. Reuse terms unverified.", ""]
    (output / "sources.md").write_text("\n".join(citations) + "\n", encoding="utf-8")
    print(json.dumps(coverage, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rules", type=Path)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--pairs", type=Path)
    parser.add_argument("--collect", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    seeds = json.loads(args.seeds.read_text(encoding="utf-8"))
    if args.collect:
        capture(seeds, args.output)
    if args.rules:
        build(args.output, json.loads(args.rules.read_text(encoding="utf-8")), args.base, json.loads(args.pairs.read_text(encoding="utf-8")) if args.pairs else [])


if __name__ == "__main__":
    main()
