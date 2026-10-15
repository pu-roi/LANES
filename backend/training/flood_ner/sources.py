"""Explicit offline public capture and local-file inventory; no application imports."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

from .annotation.schema import SourceCapture, text_hash

MAX_CAPTURE_BYTES = 4 * 1024 * 1024
VOID_TAGS = {"br", "hr", "img", "input", "link", "meta", "source", "wbr", "area", "base", "embed", "param", "track", "col"}


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def write_jsonl(path: Path, records: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r.model_dump(mode="json") if hasattr(r, "model_dump") else r,
                        ensure_ascii=False, sort_keys=True, separators=(",", ":")) for r in records]
    # Escape alternate Unicode line separators in the JSON representation;
    # decoding still restores the exact source text and character offsets.
    lines = [line.replace('\u0085', '\\u0085').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
             for line in lines]
    path.write_bytes(("\n".join(lines) + ("\n" if lines else "")).encode("utf-8"))


def read_jsonl(path: Path, model: Any) -> list[Any]:
    records = []
    for index, line in enumerate(path.read_text(encoding="utf-8").split('\n'), 1):
        if not line.strip():
            continue
        try:
            records.append(model.model_validate_json(line))
        except ValueError as exc:
            raise ValueError(f"{path.name}: line {index}: {exc}") from exc
    return records


def known_datetime(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


class CaptureParser(HTMLParser):
    """Freeze visible article/main content; do not guess entities or flood facts."""
    def __init__(self, target_id: str | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, bool]] = []
        self.parts: list[str] = []
        self.jsonld: list[str] = []
        self.script_parts: list[str] | None = None
        self.meta: dict[str, str] = {}
        self.canonical_url: str | None = None
        self.title_parts: list[str] = []
        self.target_id = target_id

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if tag == "meta" and attr.get("content"):
            self.meta[(attr.get("property") or attr.get("name") or attr.get("itemprop") or "").casefold()] = attr["content"]
        if tag == "link" and "canonical" in (attr.get("rel") or "").casefold().split():
            self.canonical_url = attr.get("href")
        parent_selected = self.stack[-1][1] if self.stack else False
        parent_skipped = self.stack[-1][2] if self.stack else False
        selected = parent_selected or (attr.get("id") == self.target_id if self.target_id else
            tag in {"article", "main"} or bool(classes & {"entry-content", "story-text", "article-body", "post-single__content"}))
        skipped = parent_skipped or tag in {"script", "style", "nav", "footer", "aside"} or bool(
            classes & {"related-article", "lower_article", "ivs-placeholder-more-videos"}
        ) or attr.get("id") in {"mrect_related_content_holder", "related_block", "load_more"}
        if tag == "script" and attr.get("type") == "application/ld+json":
            self.script_parts = []
        if selected and not skipped and tag in {"p", "div", "li", "td", "br", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")
        if tag not in VOID_TAGS:
            self.stack.append((tag, selected, skipped))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.script_parts is not None:
            self.jsonld.append("".join(self.script_parts))
            self.script_parts = None
        if self.stack and self.stack[-1][1] and not self.stack[-1][2] and tag in {"p", "div", "li", "td", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1][0] == "title":
            self.title_parts.append(data)
        if self.script_parts is not None:
            self.script_parts.append(data)
        if self.stack and self.stack[-1][1] and not self.stack[-1][2]:
            self.parts.append(data)

    def article_metadata(self) -> dict[str, Any]:
        def walk(value: Any) -> list[dict[str, Any]]:
            if isinstance(value, list):
                return [item for v in value for item in walk(v)]
            if not isinstance(value, dict):
                return []
            types = value.get("@type", [])
            if isinstance(types, str):
                types = [types]
            if not isinstance(types, list):
                types = []
            types = [t for t in types if isinstance(t, str)]
            return ([value] if set(types) & {"NewsArticle", "Article", "ReportageNewsArticle"} else []) + walk(value.get("@graph", []))
        for snippet in self.jsonld:
            try:
                articles = walk(json.loads(snippet))
            except (ValueError, TypeError):
                continue
            if articles:
                return articles[0]
        return {}

    def text(self) -> str:
        lines = [line.strip() for line in "".join(self.parts).splitlines()]
        return "\n".join(line for line in lines if line)

    def publication_value(self) -> tuple[str | None, str]:
        metadata = self.article_metadata()
        value = metadata.get("datePublished")
        if isinstance(value, str):
            return value, "JSON-LD datePublished"
        for key in ("article:published_time", "datepublished", "pubdate", "publication_date"):
            if self.meta.get(key):
                return self.meta[key], f"HTML meta {key}"
        return None, "publication metadata unavailable"

    def headline(self) -> str:
        return str(self.article_metadata().get("headline") or self.meta.get("og:title") or "".join(self.title_parts).strip())


def public_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("capture URL must be public HTTP(S) without credentials")
    # This CLI is offline tooling, never an API accepting untrusted caller URLs.
    if parts.hostname.casefold() in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("local application URLs are not public source captures")
    return url


def capture_source(url: str, source_id: str, publisher: str, language: str, event_group: str,
                   client: httpx.Client, output: Path, *, repair_embedded_markup: bool = False) -> SourceCapture:
    requested = public_url(url)
    current = requested
    raw = b""
    for attempt in range(5):
        with client.stream("GET", current, follow_redirects=False) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location or attempt == 4:
                    raise ValueError("invalid or excessive source redirects")
                current = public_url(urljoin(current, location))
                continue
            response.raise_for_status()
            if "html" not in response.headers.get("content-type", "").lower():
                raise ValueError("capture requires HTML; use preserved text manifests for other formats")
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > MAX_CAPTURE_BYTES:
                    raise ValueError("source exceeds 4 MiB capture limit")
                chunks.append(chunk)
            raw = b"".join(chunks)
            encoding = response.encoding or "utf-8"
        break
    parser = CaptureParser()
    parser.feed(raw.decode(encoding, errors="strict"))
    parser.close()
    metadata = parser.article_metadata()
    text = parser.text()
    method = "html-visible-article-main-v1"
    if (urlsplit(current).hostname or "").endswith("abs-cbn.com"):
        body_parser = CaptureParser(target_id="bodyTopPart")
        body_parser.feed(raw.decode(encoding, errors="strict"))
        body_parser.close()
        text = body_parser.text()
        method = "abs-cbn-bodyTopPart-v1"
    if isinstance(metadata.get("articleBody"), str) and metadata["articleBody"].strip():
        body = metadata["articleBody"]
        if "<" in body and ">" in body:
            if repair_embedded_markup:
                body = repair_script_markup(body)
            article = CaptureParser()
            article.feed("<article>" + body + "</article>")
            article.close()
            text = article.text()
            method = "jsonld-articleBody-html-v3" if repair_embedded_markup else "jsonld-articleBody-html-v2"
        else:
            text = body
            method = "jsonld-articleBody-text-v2"
    if not text.strip():
        raise ValueError("no article/main content found; refused whole-page fallback")
    digest = hashlib.sha256(raw).hexdigest()
    version = text_hash(json.dumps([requested, current, source_id, digest, text_hash(text), method], separators=(",", ":")))
    publication, publication_basis = parser.publication_value()
    source = SourceCapture(
        source_id=source_id, url=current, publisher=publisher, title=parser.headline(),
        language=language, text=text, text_sha256=text_hash(text), capture_version=version,
        raw_sha256=digest, published_at=known_datetime(publication),
        captured_at=datetime.now(timezone.utc), publication_basis=publication_basis,
        article_group=requested, event_group=event_group, reuse_terms="not verified",
        extraction_method=method,
    )
    output.mkdir(parents=True, exist_ok=True)
    # A capture is immutable. Repeat retrieval never overwrites an old capture.
    base = output / version
    if base.with_suffix(".json").exists():
        saved = SourceCapture.model_validate_json(base.with_suffix(".json").read_bytes())
        if hashlib.sha256(base.with_suffix(".html").read_bytes()).hexdigest() != saved.raw_sha256:
            raise ValueError("existing raw capture hash mismatch")
        if hashlib.sha256(base.with_suffix(".txt").read_bytes()).hexdigest() != saved.text_sha256:
            raise ValueError("existing frozen-text capture hash mismatch")
        return saved
    for suffix, content in ((".html", raw), (".txt", text.encode("utf-8")), (".json", json_bytes(source.model_dump(mode="json")))):
        path = base.with_suffix(suffix)
        if not path.exists():
            path.write_bytes(content)
    return source


def repair_script_markup(markup: str) -> str:
    """Repair a publisher's malformed closing tag, never visible text or saved HTML."""
    return re.sub(r'<\\script\s*>', '</script>', markup, flags=re.I)


def reextract_capture(path: Path, output: Path) -> SourceCapture:
    """Create a new extraction version from immutable raw HTML; no network or rewrite."""
    original = SourceCapture.model_validate_json(path.read_bytes())
    if text_hash(path.with_suffix('.txt').read_bytes().decode('utf-8')) != original.text_sha256:
        raise ValueError('re-extraction needs hash-bound original text')
    raw = path.with_suffix('.html').read_bytes()
    if hashlib.sha256(raw).hexdigest() != original.raw_sha256:
        raise ValueError('re-extraction needs hash-bound original HTML')
    parser = CaptureParser(); parser.feed(raw.decode('utf-8')); parser.close()
    body = parser.article_metadata().get('articleBody')
    if not isinstance(body, str) or '<' not in body:
        raise ValueError('re-extraction requires structured HTML articleBody')
    repaired = repair_script_markup(body)
    if repaired == body:
        raise ValueError('no supported malformed-script repair needed')
    article = CaptureParser(); article.feed('<article>' + repaired + '</article>'); article.close()
    text = article.text()
    if not text or text == original.text:
        raise ValueError('repair did not recover additional visible article text')
    method = 'jsonld-articleBody-html-v3-from-frozen-raw'
    version = text_hash(json.dumps([original.capture_version, original.raw_sha256, text_hash(text), method], separators=(',', ':')))
    source = SourceCapture.model_validate(original.model_dump() | {'capture_version': version, 'text': text,
                            'text_sha256': text_hash(text), 'extraction_method': method,
                            'admission_status': 'research_only'})
    output.mkdir(parents=True, exist_ok=True)
    base = output / version
    contents = {'.html': raw, '.txt': text.encode('utf-8'), '.json': json_bytes(source.model_dump(mode='json'))}
    for suffix, content in contents.items():
        target = base.with_suffix(suffix)
        if target.exists() and target.read_bytes() != content:
            raise ValueError('immutable repaired capture conflict')
    for suffix, content in contents.items():
        target = base.with_suffix(suffix)
        if not target.exists(): target.write_bytes(content)
    return source


def inventory_sources(root: Path) -> tuple[list[SourceCapture], list[dict[str, str]]]:
    records: dict[tuple[str, str], SourceCapture] = {}
    issues: list[dict[str, str]] = []
    for manifest in sorted((root / "docs" / "evaluations").rglob("source_manifest.json")):
        try:
            rows = json.loads(manifest.read_text(encoding="utf-8"))
            if not isinstance(rows, list):
                issues.append({"manifest": manifest.relative_to(root).as_posix(), "error": "unsupported_manifest_shape"})
                continue
            for row in rows:
                if not isinstance(row, dict):
                    issues.append({"manifest": manifest.relative_to(root).as_posix(), "error": "invalid_manifest_row"})
                    continue
                if not row.get("text_path"):
                    continue
                try:
                    path = (manifest.parent / row["text_path"]).resolve()
                    if not path.is_relative_to(manifest.parent.resolve()):
                        raise ValueError("capture path escapes manifest directory")
                    # Decode without universal-newline conversion: offsets and hashes use original text.
                    text = path.read_bytes().decode("utf-8")
                    digest = text_hash(text)
                    if row.get("text_sha256") and row["text_sha256"] != digest:
                        raise ValueError("manifest text_sha256 mismatch")
                    source = SourceCapture(
                        source_id=row["source_id"], url=row.get("final_url") or row["url"],
                        publisher=row.get("publisher") or "Unknown publisher", title=row.get("title") or "",
                        text=text, text_sha256=digest, capture_version=row.get("capture_version") or digest,
                        published_at=known_datetime(row.get("publication_metadata")),
                        captured_at=known_datetime(row.get("fetched_at")),
                        publication_basis=row.get("publication_metadata_basis"),
                        article_group=row["url"], event_group=row.get("episode_group"),
                        reuse_terms=row.get("reuse_terms") or "not verified", extraction_method="preserved-manifest-text",
                        raw_sha256=row.get("html_sha256"),
                    )
                    records[(source.url, source.capture_version)] = source
                except (OSError, ValueError, KeyError) as exc:
                    issues.append({"manifest": manifest.relative_to(root).as_posix(), "source_id": str(row.get("source_id", "")), "error": str(exc)})
        except (OSError, ValueError) as exc:
            issues.append({"manifest": manifest.relative_to(root).as_posix(), "error": str(exc)})
    fixture = root / "backend" / "tests" / "fixtures" / "mcp_saved_news.json"
    if fixture.exists():
        for row in json.loads(fixture.read_text(encoding="utf-8")):
            article = row.get("article", {})
            text = article.get("article_text")
            if row.get("origin") != "captured-original-extraction" or not text:
                continue
            digest = text_hash(text)
            source = SourceCapture(
                source_id=f"saved-article-{article['article_id']}", url=article["canonical_url"],
                publisher=article["publisher"], title=article["title"], text=text, text_sha256=digest,
                capture_version=digest, published_at=known_datetime(article.get("published_at")),
                captured_at=known_datetime(article.get("fetched_at")), article_group=article["canonical_url"],
                reuse_terms="not verified", extraction_method="preserved-captured-original-fixture",
            )
            records.setdefault((source.url, source.capture_version), source)
    capture_dir = root / "backend" / "training" / "flood_ner" / "artifacts" / "captures"
    for path in sorted(capture_dir.glob("*.json")):
        try:
            source = SourceCapture.model_validate_json(path.read_bytes())
            # Identical visible text can have distinct immutable raw evidence,
            # retrieval timestamps and publication metadata. Article-level
            # deduplication belongs to collection/assembly, not this inventory.
            records[(source.url, source.capture_version)] = source
        except (OSError, ValueError) as exc:
            issues.append({"manifest": path.relative_to(root).as_posix(), "error": str(exc)})
    return sorted(records.values(), key=lambda r: (r.url, r.text_sha256, r.capture_version)), issues
