"""Reviewed historical-news collection manifest, independent of runtime ingestion."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import httpx

from .annotation.schema import SourceCapture, text_hash
from .sources import CaptureParser, capture_source, inventory_sources, json_bytes, known_datetime, public_url

START_DATE = date(2022, 1, 1)
END_DATE = date(2026, 10, 14)
PUBLISHERS = {"gmanetwork.com": "GMA News", "abs-cbn.com": "ABS-CBN News", "philstar.com": "Philstar",
              "inquirer.net": "Inquirer", "tribune.net.ph": "Daily Tribune", "rmn.ph": "RMN Networks",
              "onenews.ph": "OneNews", "pna.gov.ph": "Philippine News Agency", "rappler.com": "Rappler"}


def publisher_for(url: str) -> str | None:
    host = (urlsplit(url).hostname or "").casefold()
    return next((name for domain, name in PUBLISHERS.items() if host == domain or host.endswith("." + domain)), None)


def canonical_news_url(url: str) -> str:
    parts = urlsplit(public_url(url))
    host = (parts.hostname or "").casefold().removeprefix("www.")
    path = re.sub(r"/+", "/", parts.path).rstrip("/")
    # Percent-escape hex case is equivalent; ordinary path case is not.
    path = re.sub(r"%[0-9a-fA-F]{2}", lambda match: match.group().lower(), path)
    path = re.sub(r"/amp$", "", path, flags=re.I)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.casefold().startswith("utm_") and k.casefold() not in
             {"fbclid", "gclid", "amp", "order", "top_picks", "output"}]
    return urlunsplit(("https", host, path, urlencode(sorted(query)), ""))


def article_key(url: str) -> str:
    canonical = canonical_news_url(url)
    match = re.search(r"gmanetwork\.com/news/[^?#]*?/(\d{5,})/", canonical)
    return f"gma:{match.group(1)}" if match else canonical


def publication_date(value: str | None) -> date | None:
    """Date-only evidence does not manufacture a timezone-qualified instant."""
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}(?:T|\s|$)", value):
        return None
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if instant.utcoffset() is not None:
            return instant.astimezone(ZoneInfo("Asia/Manila")).date()
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def body_fingerprint(text: str) -> str:
    words = re.findall(r"\w+", text.casefold())
    return text_hash(" ".join(words))


def shingles(text: str) -> set[tuple[str, ...]]:
    words = re.findall(r"\w+", text.casefold())
    return {tuple(words[i:i + 8]) for i in range(max(0, len(words) - 7))}


def same_story(first: str, second: str) -> bool:
    if body_fingerprint(first) == body_fingerprint(second):
        return True
    a, b = shingles(first), shingles(second)
    return bool(a and b and len(a & b) / len(a | b) >= 0.85)


def source_entry(source: SourceCapture, *, publication_value: str | None = None,
                 canonical_url: str | None = None, capture_path: str | None = None) -> dict[str, Any]:
    value = publication_value or (source.published_at.isoformat() if source.published_at else None)
    day = publication_date(value)
    publisher = publisher_for(source.url)
    reason = None
    if not publisher:
        reason = "not_publisher_news"
    elif not day:
        reason = "publication_date_unconfirmed"
    elif not START_DATE <= day <= END_DATE:
        reason = "publication_date_out_of_range"
    elif len(re.findall(r"\w+", source.text)) < 40:
        reason = "article_body_incomplete"
    return {
        "source_category": "news_article" if publisher else "supporting_reference",
        "source_id": source.source_id, "publisher": publisher or source.publisher,
        "url": source.url, "canonical_url": canonical_news_url(canonical_url or source.url),
        "article_key": article_key(canonical_url or source.url), "title": source.title,
        "publication_date": day.isoformat() if day else None, "publication_value": value,
        "publication_basis": source.publication_basis, "published_at": source.published_at.isoformat() if source.published_at else None,
        "captured_at": source.captured_at.isoformat() if source.captured_at else None,
        "capture_version": source.capture_version, "capture_path": capture_path,
        "text_sha256": source.text_sha256, "raw_sha256": source.raw_sha256,
        "body_fingerprint": body_fingerprint(source.text), "characters": len(source.text),
        "language": source.language, "event_group": source.event_group, "syndication_group": source.syndication_group,
        "reuse_status": source.reuse_status, "admission_status": source.admission_status,
        "status": "excluded" if reason else "review_pending", "exclusion_reason": reason,
        "reviewer": None, "review_notes": [], "evidence": [], "case_types": [],
    }


def import_browser_capture(snapshot_path: Path, output: Path, source_id: str, language: str = "unknown") -> SourceCapture:
    """Preserve a rendered public body with explicit DOM-snapshot provenance."""
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    url = public_url(snapshot["url"])
    publisher = publisher_for(url)
    if not publisher:
        raise ValueError("browser capture needs a recognized publisher")
    text = snapshot.get("body_text") or ""
    if len(re.findall(r"\w+", text)) < 40:
        raise ValueError("rendered article body incomplete")
    header = next((s for s in snapshot.get("headers", []) if s.startswith("Published ")), None)
    instant = None
    if header and header.endswith(" PHT"):
        for pattern in ("Published %B %d, %Y %I:%M %p PHT", "Published %b %d, %Y %I:%M %p PHT"):
            try:
                instant = datetime.strptime(header, pattern).replace(tzinfo=timezone(timedelta(hours=8)))
                break
            except ValueError:
                continue
    if instant is None:
        raise ValueError("rendered publication header not verified")
    raw = snapshot_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    source = SourceCapture(source_id=source_id, url=url, publisher=publisher, title=snapshot["title"], language=language,
                           text=text, text_sha256=text_hash(text), raw_sha256=digest, capture_version=digest,
                           published_at=instant, captured_at=datetime.fromisoformat(snapshot["captured_at"].replace("Z", "+00:00")),
                           publication_basis=header, article_group=canonical_news_url(url),
                           event_group="review-needed:" + article_key(url), reuse_terms="not verified",
                           extraction_method="browser-rendered-article-dom-v1")
    output.mkdir(parents=True, exist_ok=True)
    existing = output / f"{digest}.json"
    if existing.exists():
        saved = SourceCapture.model_validate_json(existing.read_bytes())
        if saved.source_id != source_id or saved.language != language or saved.url != url:
            raise ValueError("immutable browser capture identity conflict")
        if ((output / f"{digest}.dom-snapshot").read_bytes() != raw
                or text_hash((output / f"{digest}.txt").read_bytes().decode("utf-8")) != saved.text_sha256):
            raise ValueError("immutable browser capture file mismatch")
        if saved != source:
            raise ValueError("immutable browser capture metadata mismatch")
        return saved
    (output / f"{digest}.dom-snapshot").write_bytes(raw)
    (output / f"{digest}.txt").write_bytes(text.encode("utf-8"))
    (output / f"{digest}.json").write_bytes(json_bytes(source.model_dump(mode="json")))
    return source


def wikipedia_reference(title: str, language: str, client: httpx.Client, output: Path) -> dict[str, Any]:
    """Freeze revision/content/attribution separately from news and training."""
    if not re.fullmatch(r"[a-z]{2,3}", language):
        raise ValueError("invalid Wikipedia language code")
    host = f"https://{language}.wikipedia.org"
    response = client.get(host + "/w/api.php", params={"action": "query", "format": "json", "formatversion": "2",
        "prop": "revisions", "titles": title, "rvprop": "ids|timestamp|user|content", "rvslots": "main",
        "rvlimit": "1", "rvstart": END_DATE.isoformat() + "T15:59:59Z", "redirects": "1"})
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise ValueError("Wikipedia API error: " + str(payload["error"].get("code")))
    pages = payload.get("query", {}).get("pages", [])
    if not isinstance(pages, list) or not pages or not isinstance(pages[0], dict):
        raise ValueError("Wikipedia API returned no usable page")
    page = pages[0]
    if not page.get("revisions"):
        raise ValueError("Wikipedia page has no revision available in the research window")
    revision = page["revisions"][0]
    content = revision["slots"]["main"]["content"]
    revision_id = revision["revid"]
    revision_time = known_datetime(revision.get("timestamp"))
    cutoff = datetime.combine(END_DATE, datetime.max.time(), tzinfo=timezone(timedelta(hours=8)))
    if not revision_time or revision_time > cutoff or not isinstance(content, str) or type(revision_id) is not int:
        raise ValueError("Wikipedia revision content/identity/timestamp invalid or after cutoff")
    encoded_title = quote(page['title'].replace(' ', '_'), safe='')
    permanent = f"{host}/w/index.php?title={encoded_title}&oldid={revision_id}"
    license_response = client.get(host + "/w/api.php", params={"action": "query", "meta": "siteinfo", "siprop": "rightsinfo", "format": "json"})
    license_response.raise_for_status()
    rights = license_response.json()["query"]["rightsinfo"]
    output.mkdir(parents=True, exist_ok=True)
    version = text_hash(content)
    # Revision IDs are unique within a wiki, not across languages. Preserve old
    # revision-only filenames when present; new files have a language namespace.
    base = f"{language}-{revision_id}"
    for candidate in (base, str(revision_id)):
        metadata_path = output / f"{candidate}.json"
        if not metadata_path.exists():
            continue
        saved = json.loads(metadata_path.read_text(encoding="utf-8"))
        if saved.get("language") != language:
            if candidate == base:
                raise ValueError("immutable Wikipedia language identity conflict")
            continue
        saved_text = output / f"{candidate}.wiki.txt"
        if (saved.get("revision_id") != revision_id or saved.get("title") != page["title"]
                or saved.get("text_sha256") != version or hashlib.sha256(saved_text.read_bytes()).hexdigest() != version):
            raise ValueError("immutable Wikipedia revision/content mismatch")
        return saved
    text_path = output / f"{base}.wiki.txt"
    if text_path.exists() and text_path.read_bytes() != content.encode("utf-8"):
        raise ValueError("immutable Wikipedia content file mismatch")
    text_path.write_bytes(content.encode("utf-8"))
    result = {"source_category": "wikipedia_reference", "title": page["title"], "language": language,
              "revision_id": revision_id, "revision_timestamp": revision["timestamp"], "permanent_url": permanent,
              "history_url": host + "/w/index.php?title=" + encoded_title + "&action=history",
              "attribution": f"Wikipedia contributors, {page['title']}, revision {revision_id}; contributor history linked.",
              "license": rights, "text_sha256": version, "captured_at": datetime.now(timezone.utc).isoformat(),
              "extraction_method": "MediaWiki revisions main-slot wikitext", "training_admission": "excluded_support_only",
              "news_target_count": 0, "geographic_verification": "unverified_reference_not_imported_into_PSGC_OSM"}
    (output / f"{base}.json").write_bytes(json_bytes(result))
    return result


def collect_candidates(urls: list[str], root: Path, output: Path) -> list[dict[str, Any]]:
    """Capture eligible publisher links; every fetch failure remains visible."""
    if not isinstance(urls, list) or any(not isinstance(url, str) for url in urls):
        raise ValueError("discovered URLs must be a JSON array of strings")
    output.mkdir(parents=True, exist_ok=True)
    existing, issues = inventory_sources(root)
    entries = [source_entry(s) for s in existing]
    captures = root / "backend/training/flood_ner/artifacts/captures"
    source_files: dict[tuple[str, str], Path] = {}
    for path in captures.glob("*.json"):
        source = SourceCapture.model_validate_json(path.read_bytes())
        source_files[(source.url, source.text_sha256)] = path
    for entry in entries:
        found = source_files.get((entry["url"], entry["text_sha256"]))
        if found:
            entry["capture_path"] = found.relative_to(root).as_posix()
    known_keys = {e["article_key"] for e in entries}
    unique: dict[str, str] = {}
    for url in urls:
        if publisher_for(url) and not re.search(r"\.(?:png|pdf|jpg)(?:\?|$)", url, re.I):
            key = article_key(url)
            if key not in known_keys:
                unique.setdefault(key, url)

    def fetch(item: tuple[str, str]) -> dict[str, Any]:
        key, url = item
        publisher = publisher_for(url)
        language = "tagalog" if "/balitambayan/" in url or "/ulatfilipino/" in url else "unknown"
        source_id = "news-" + hashlib.sha256(key.encode()).hexdigest()[:16]
        try:
            with httpx.Client(timeout=25, trust_env=False, headers={"User-Agent": "LANES-offline-NER-research/1.0"}) as client:
                source = capture_source(url, source_id, publisher, language, "review-needed:" + key, client, captures)
            raw_path = captures / f"{source.capture_version}.html"
            parser = CaptureParser()
            parser.feed(raw_path.read_bytes().decode("utf-8", errors="replace"))
            publication, _ = parser.publication_value()
            canonical = parser.canonical_url
            if canonical:
                canonical = canonical if publisher_for(canonical) == publisher else None
            return source_entry(source, publication_value=publication, canonical_url=canonical,
                                capture_path=(captures / f"{source.capture_version}.json").relative_to(root).as_posix())
        except (OSError, ValueError, httpx.HTTPError) as exc:
            return {"url": url, "article_key": key, "publisher": publisher, "source_category": "news_article",
                    "source_id": source_id, "status": "capture_failed", "exclusion_reason": str(exc),
                    "reviewer": None, "review_notes": [], "evidence": [], "case_types": []}

    with ThreadPoolExecutor(max_workers=4) as pool:
        entries.extend(pool.map(fetch, sorted(unique.items())))
    (output / "candidates.json").write_bytes(json_bytes({"inventory_issues": issues, "entries": entries}))
    return entries


def validate_reviewed(entries: list[dict[str, Any]], sources: dict[str, SourceCapture]) -> list[str]:
    errors = []
    if not isinstance(entries, list):
        return ["collection manifest must be a JSON array of records"]
    seen: dict[str, dict[str, Any]] = {}
    accepted: list[tuple[dict[str, Any], SourceCapture]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("collection record must be an object")
            continue
        if entry.get("status") != "accepted":
            continue
        sid = entry.get("source_id", "<missing source id>")
        version = entry.get("capture_version")
        source = sources.get(version) if isinstance(version, str) else None
        try:
            matching_url = source is not None and isinstance(entry.get("url"), str) and canonical_news_url(source.url) == canonical_news_url(entry["url"])
        except ValueError:
            matching_url = False
        if (not matching_url or source is None or source.source_id != sid or source.text_sha256 != entry.get("text_sha256")):
            errors.append(f"{sid}: missing/mismatched captured source")
            continue
        day = publication_date(entry.get("publication_date"))
        if (not day or not START_DATE <= day <= END_DATE or entry.get("source_category") != "news_article"
                or not publisher_for(entry.get("url", ""))):
            errors.append(f"{sid}: accepted record is not dated publisher news in range")
        if (day != publication_date(entry.get("publication_value")) or not entry.get("publication_basis")
                or (source.published_at and day != publication_date(source.published_at.isoformat()))):
            errors.append(f"{sid}: publication date does not match captured evidence")
        instant = known_datetime(entry.get("publication_value"))
        if instant and source.published_at and instant != source.published_at:
            errors.append(f"{sid}: publication instant does not match captured evidence")
        if entry.get("raw_sha256") != source.raw_sha256:
            errors.append(f"{sid}: raw hash does not match captured source")
        if entry.get("publisher") != publisher_for(source.url):
            errors.append(f"{sid}: publisher identity mismatch")
        for field in ("captured_at", "published_at"):
            original = getattr(source, field)
            value = entry.get(field)
            if (original is None and value is not None) or (original is not None and known_datetime(value) != original):
                errors.append(f"{sid}: {field} does not match captured provenance")
        if entry.get("reuse_status") != source.reuse_status:
            errors.append(f"{sid}: reuse status does not match captured source")
        try:
            matching_key = (isinstance(entry.get("canonical_url"), str)
                            and entry.get("article_key") == article_key(entry["canonical_url"]) == article_key(source.url))
        except ValueError:
            matching_key = False
        if not matching_key:
            errors.append(f"{sid}: canonical article identity mismatch")
            continue
        if source.admission_status != "research_only" or entry.get("admission_status") != "research_only":
            errors.append(f"{sid}: historical collection must remain research only")
        notes = entry.get("review_notes")
        spans = entry.get("evidence")
        if (not isinstance(entry.get("reviewer"), str) or not entry["reviewer"].strip()
                or not isinstance(notes, list) or not notes or any(not isinstance(n, str) or not n.strip() for n in notes)
                or not isinstance(spans, list) or not spans):
            errors.append(f"{sid}: body/date/publisher review and evidence required")
        for span in spans if isinstance(spans, list) else []:
            if not isinstance(span, dict) or type(span.get("start")) is not int or type(span.get("end")) is not int or not 0 <= span["start"] < span["end"] <= len(source.text):
                errors.append(f"{sid}: invalid body evidence pointer")
            elif span.get("sha256") != text_hash(source.text[span["start"]:span["end"]]):
                errors.append(f"{sid}: body evidence hash mismatch")
        key = entry.get("article_key")
        if key in seen:
            errors.append(f"{sid}: duplicate article/version of {seen[key]['source_id']}")
        seen[key] = entry
        for other, other_source in accepted:
            if same_story(source.text, other_source.text):
                errors.append(f"{sid}: copied/near-identical story of {other['source_id']}")
                break
        accepted.append((entry, source))
    return errors


def verify_capture_files(entries: list[dict[str, Any]], root: Path) -> list[str]:
    """Check frozen text/raw files and publication evidence; never fetch missing data."""
    errors = []
    if not isinstance(entries, list):
        return ["collection manifest must be a JSON array of records"]
    root = root.resolve()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("collection record must be an object")
            continue
        if entry.get("status") != "accepted":
            continue
        sid = entry.get("source_id", "<missing source id>")
        try:
            def local_file(value: str) -> Path:
                path = (root / value).resolve()
                if not path.is_relative_to(root):
                    raise ValueError("evidence path outside repository")
                return path
            text = local_file(entry["text_path"]).read_bytes().decode("utf-8")
            if text_hash(text) != entry["text_sha256"]:
                raise ValueError("frozen text hash mismatch")
            if entry.get("raw_sha256"):
                raw = local_file(entry["raw_path"]).read_bytes()
                if hashlib.sha256(raw).hexdigest() != entry["raw_sha256"]:
                    raise ValueError("raw capture hash mismatch")
            evidence = entry["publication_evidence"]
            if not isinstance(evidence, dict):
                raise ValueError("publication evidence must be an object")
            if evidence["kind"] == "html_metadata":
                if local_file(evidence["path"]) != local_file(entry["raw_path"]):
                    raise ValueError("publication evidence is not bound to this raw capture")
                parser = CaptureParser()
                parser.feed(local_file(evidence["path"]).read_bytes().decode("utf-8"))
                value, _ = parser.publication_value()
                if value != entry["publication_value"]:
                    raise ValueError("publication metadata mismatch")
            elif evidence["kind"] == "rendered_header":
                if local_file(evidence["path"]) != local_file(entry["raw_path"]):
                    raise ValueError("publication evidence is not bound to this raw capture")
                snapshot = json.loads(local_file(evidence["path"]).read_text(encoding="utf-8"))
                if entry["publication_basis"] not in snapshot["headers"]:
                    raise ValueError("publication header mismatch")
                if snapshot.get("body_text") != text or canonical_news_url(snapshot["url"]) != canonical_news_url(entry["url"]):
                    raise ValueError("rendered body/URL does not match frozen capture")
            elif evidence["kind"] == "preserved_body_header":
                # Explicitly preserve missing raw HTML/retrieval time on old captured fixtures.
                start, end = evidence["start"], evidence["end"]
                if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                        or text_hash(text[start:end]) != evidence["sha256"]):
                    raise ValueError("preserved publication header mismatch")
                if local_file(evidence["path"]) != local_file(entry["text_path"]) or entry.get("raw_sha256") is not None:
                    raise ValueError("preserved header must reference its legacy frozen text")
                header = re.search(r"(?:^Published\s+|^)([A-Za-z]+ \d{1,2}, \d{4})", text[start:end])
                try:
                    header_day = datetime.strptime(header.group(1), "%B %d, %Y").date() if header else None
                except ValueError:
                    header_day = None
                if header_day != publication_date(entry["publication_value"]):
                    raise ValueError("preserved header does not corroborate publication day")
            else:
                raise ValueError("unsupported publication evidence kind")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{sid}: {exc}")
    return errors


def collection_report(entries: list[dict[str, Any]], expected_count: int = 100) -> dict[str, Any]:
    if type(expected_count) is not int or expected_count < 1:
        raise ValueError('expected count must be a positive integer')
    accepted = [e for e in entries if e.get("status") == "accepted"]
    return {"schema_version": "lanes-flood-news-collection-v1", "target": expected_count, "accepted_news_articles": len(accepted),
            "publication_window": [START_DATE.isoformat(), END_DATE.isoformat()], "window_timezone": "Asia/Manila",
            "status_counts": dict(Counter(e["status"] for e in entries)),
            "years": dict(sorted(Counter(e["publication_date"][:4] for e in accepted).items())),
            "publishers": dict(Counter(e["publisher"] for e in accepted)),
            "languages": dict(Counter(e["language"] for e in accepted)),
            "languages_by_year": {year: dict(Counter(e["language"] for e in accepted if e["publication_date"].startswith(year)))
                                  for year in sorted({e["publication_date"][:4] for e in accepted})},
            "publishers_by_year": {year: dict(Counter(e["publisher"] for e in accepted if e["publication_date"].startswith(year)))
                                   for year in sorted({e["publication_date"][:4] for e in accepted})},
            "case_types": dict(Counter(t for e in accepted for t in e["case_types"])),
            "note": "Reviewed research articles only; no training admission, entity labels or operational publication."}


def write_reviewed_collection(entries: list[dict[str, Any]], sources: list[SourceCapture], output: Path,
                              expected_count: int = 100) -> dict[str, Any]:
    if type(expected_count) is not int or expected_count < 1:
        raise ValueError('expected count must be a positive integer')
    errors = validate_reviewed(entries, {s.capture_version: s for s in sources})
    accepted = [e for e in entries if isinstance(e, dict) and e.get("status") == "accepted"] if isinstance(entries, list) else []
    if len(accepted) != expected_count:
        errors.append(f"expected exactly {expected_count} reviewed news articles; found {len(accepted)}")
    if errors:
        raise ValueError("\n".join(errors))
    if output.exists() and any(output.iterdir()):
        raise ValueError('collection destination must be empty; preserve earlier registers')
    output.mkdir(parents=True, exist_ok=True)
    report = collection_report(entries, expected_count)
    (output / "news_register.json").write_bytes(json_bytes(sorted(accepted, key=lambda e: (e["publication_date"], e["article_key"]))))
    (output / "collection_outcomes.json").write_bytes(json_bytes(entries))
    (output / "coverage.json").write_bytes(json_bytes(report))
    return report
