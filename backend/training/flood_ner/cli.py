"""Explicit offline corpus commands. No SQL, worker or provider configuration."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

from .annotation.schema import AnnotationRecord
from .annotation.validation import validate_corpus
from .export import corpus_tokenizer, export_corpus
from .evaluation.coverage import coverage_report
from .evaluation.research import research_matrix
from .sources import capture_source, inventory_sources, json_bytes, read_jsonl, write_jsonl

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
REPO_ROOT = Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory = commands.add_parser("inventory", help="Inventory preserved repository captures")
    inventory.add_argument("--root", type=Path, default=REPO_ROOT)
    inventory.add_argument("--output", type=Path, default=ARTIFACTS / "inventory")
    capture = commands.add_parser("capture", help="Capture a named public source offline")
    for name in ("url", "source-id", "publisher", "event-group"):
        capture.add_argument(f"--{name}", required=True)
    capture.add_argument("--language", choices=["english", "tagalog", "taglish", "unknown"], required=True)
    capture.add_argument("--output", type=Path, default=ARTIFACTS / "captures")
    validate = commands.add_parser("validate", help="Validate JSONL annotations without exporting")
    validate.add_argument("input", type=Path)
    export = commands.add_parser("export", help="Export a frozen reviewed corpus to DocBin")
    export.add_argument("input", type=Path)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--allow-constructed", action="store_true", help="Test-only export; manifest is marked constructed")
    export.add_argument("--profile", choices=['context-rich-v1', 'location-only-v1'], default='context-rich-v1')
    places = commands.add_parser("inspect-place", help="Read-only comparison with existing number/PSGC/OSM services")
    places.add_argument("--name", required=True)
    places.add_argument("--context", default="")
    places.add_argument("--city", help="Explicit parent city for OSM locality candidates")
    collect = commands.add_parser("collect-news", help="Capture discovered publisher URLs for historical review")
    collect.add_argument("urls", type=Path, help="JSON array of explicitly discovered URLs")
    collect.add_argument("--output", type=Path, default=ARTIFACTS / "collection100")
    browser = commands.add_parser("import-browser-news", help="Import an explicitly saved rendered DOM snapshot")
    browser.add_argument("snapshot", type=Path)
    browser.add_argument("--source-id", required=True)
    browser.add_argument("--language", choices=["english", "tagalog", "taglish", "unknown"], default="unknown")
    browser.add_argument("--output", type=Path, default=ARTIFACTS / "captures")
    report = commands.add_parser("verify-news", help="Verify a reviewed news manifest; default target 100")
    report.add_argument("manifest", type=Path, help="JSON array of reviewed entries")
    report.add_argument("--expected-count", type=int, default=100)
    report.add_argument("--output", type=Path, default=ARTIFACTS / "collection100" / "verified")
    prepare = commands.add_parser("prepare-pilot", help="Propose source-exact research-only passage windows for review")
    prepare.add_argument("register", type=Path)
    prepare.add_argument("--output", type=Path, default=ARTIFACTS / "readiness" / "candidates")
    editorial = commands.add_parser("review-passages", help="Apply explicit editorial decisions; no labels or admission")
    editorial.add_argument("candidates", type=Path, help="Original candidate JSONL")
    editorial.add_argument("reviews", type=Path, help="JSON array of source-bound editorial decisions")
    editorial.add_argument("--output", type=Path, required=True)
    cohort = commands.add_parser('build-cohort', help='Select a reviewed 400-sample research cohort with grouped splits')
    cohort.add_argument('annotations', type=Path)
    cohort.add_argument('--group-reviews', type=Path, required=True)
    cohort.add_argument('--news-register', type=Path, required=True, help='Reviewed source register with capture/publication evidence')
    cohort.add_argument('--pilot-records', type=Path, required=True, help='JSON array of retained pilot record IDs')
    cohort.add_argument('--output', type=Path, required=True)
    qualify = commands.add_parser('qualify-cohort', help='Diagnose a frozen research dataset without training or admission')
    qualify.add_argument('folder', type=Path)
    qualify.add_argument('--news-register', type=Path, required=True)
    qualify.add_argument('--model-register', type=Path)
    qualify.add_argument('--reuse-register', type=Path)
    qualify.add_argument('--output', type=Path, required=True)
    wiki = commands.add_parser("capture-wikipedia", help="Capture a reference revision, outside news/training")
    wiki.add_argument("--title", required=True)
    wiki.add_argument("--language", default="en")
    wiki.add_argument("--output", type=Path, default=ARTIFACTS / "collection100" / "wikipedia")
    args = parser.parse_args(argv)
    try:
        if args.command == 'qualify-cohort':
            from .qualification import write_qualification
            result = write_qualification(args.folder, args.news_register, REPO_ROOT, args.output,
                                         model_register=args.model_register, reuse_register=args.reuse_register)
            print(json.dumps({k: result[k] for k in ('samples', 'source_articles', 'export_ready_records',
                                                     'candidate_tokenizer', 'qualification_open_items')}, ensure_ascii=False))
            return 0
        if args.command == 'build-cohort':
            from .cohort import GroupReview, build_cohort
            from .collection import validate_reviewed, verify_capture_files
            sources, issues = inventory_sources(REPO_ROOT)
            if issues:
                raise ValueError('source inventory has unresolved integrity issues')
            news_entries = json.loads(args.news_register.read_text(encoding='utf-8'))
            errors = validate_reviewed(news_entries, {s.capture_version:s for s in sources}) + verify_capture_files(news_entries, REPO_ROOT)
            if errors:
                raise ValueError('\n'.join(errors))
            approved_versions = {e['capture_version'] for e in news_entries if e.get('status') == 'accepted'}
            raw_reviews = json.loads(args.group_reviews.read_text(encoding='utf-8'))
            pilot_ids = json.loads(args.pilot_records.read_text(encoding='utf-8'))
            if not isinstance(raw_reviews, list) or not isinstance(pilot_ids, list) or any(not isinstance(i, str) for i in pilot_ids):
                raise ValueError('group reviews and pilot IDs must be JSON arrays')
            reviews = [GroupReview.model_validate_json(json.dumps(r)) for r in raw_reviews]
            records = read_jsonl(args.annotations, AnnotationRecord)
            if any(r.source.capture_version not in approved_versions for r in records):
                raise ValueError('every annotation requires reviewed capture/publication evidence in the news register')
            result = build_cohort(records, reviews, sources,
                                  REPO_ROOT, args.output, pilot_ids=set(pilot_ids))
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if args.command == "review-passages":
            from .editorial import EditorialReview, build_editorial_queue
            from .preparation import CandidatePassage
            sources, issues = inventory_sources(REPO_ROOT)
            if issues:
                raise ValueError("source inventory has unresolved integrity issues")
            decisions = json.loads(args.reviews.read_text(encoding="utf-8"))
            if not isinstance(decisions, list):
                raise ValueError("editorial reviews must be a JSON array")
            reviews = [EditorialReview.model_validate_json(json.dumps(r)) for r in decisions]
            result = build_editorial_queue(read_jsonl(args.candidates, CandidatePassage), reviews,
                                          sources, REPO_ROOT, args.output)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if args.command == "prepare-pilot":
            from .preparation import prepare_candidates
            sources, issues = inventory_sources(REPO_ROOT)
            if issues:
                raise ValueError("source inventory has unresolved integrity issues")
            result = prepare_candidates(json.loads(args.register.read_text(encoding="utf-8")),sources,REPO_ROOT,args.output)
            print(json.dumps(result,ensure_ascii=False))
            return 0
        if args.command == "collect-news":
            from .collection import collect_candidates, collection_report
            entries = collect_candidates(json.loads(args.urls.read_text(encoding="utf-8")), REPO_ROOT, args.output)
            print(json.dumps(collection_report(entries), ensure_ascii=False))
            return 0
        if args.command == "verify-news":
            from .collection import verify_capture_files, write_reviewed_collection
            sources, issues = inventory_sources(REPO_ROOT)
            if issues:
                raise ValueError("source inventory has unresolved integrity issues")
            entries = json.loads(args.manifest.read_text(encoding="utf-8"))
            errors = verify_capture_files(entries, REPO_ROOT)
            if errors:
                raise ValueError("\n".join(errors))
            report = write_reviewed_collection(entries, sources, args.output, args.expected_count)
            print(json.dumps(report, ensure_ascii=False))
            return 0
        if args.command == "import-browser-news":
            from .collection import import_browser_capture
            source = import_browser_capture(args.snapshot, args.output, args.source_id, args.language)
            print(json.dumps({"source_id": source.source_id, "capture_version": source.capture_version}))
            return 0
        if args.command == "capture-wikipedia":
            from .collection import wikipedia_reference
            with httpx.Client(timeout=25, trust_env=False, headers={"User-Agent": "LANESCorpusResearch/1.0 (https://github.com/pu-roi/LANES)"}) as client:
                reference = wikipedia_reference(args.title, args.language, client, args.output)
            print(json.dumps({k: reference[k] for k in ("title", "revision_id", "revision_timestamp", "permanent_url", "news_target_count")}))
            return 0
        if args.command == "inspect-place":
            from .locations import inspect_place
            print(json.dumps(inspect_place(args.name, args.context, args.city), ensure_ascii=False))
            return 0
        if args.command == "inventory":
            sources, issues = inventory_sources(args.root.resolve())
            args.output.mkdir(parents=True, exist_ok=True)
            write_jsonl(args.output / "sources.jsonl", sources)
            report = coverage_report(sources, issues)
            (args.output / "report.json").write_bytes(json_bytes(report))
            (args.output / "case_matrix.json").write_bytes(json_bytes(research_matrix(sources)))
            print(json.dumps({k: report[k] for k in ("source_count", "language_counts", "admission_counts", "issues")}, ensure_ascii=False))
            return 0
        if args.command == "capture":
            with httpx.Client(timeout=30, trust_env=False, headers={"User-Agent": "LANES-offline-NER-research/1.0"}) as client:
                source = capture_source(args.url, args.source_id, args.publisher, args.language, args.event_group, client, args.output)
            print(json.dumps({"source_id": source.source_id, "text_sha256": source.text_sha256,
                              "characters": len(source.text), "admission_status": source.admission_status}))
            return 0
        records = read_jsonl(args.input, AnnotationRecord)
        if args.command == "validate":
            errors = validate_corpus(records, corpus_tokenizer())
            if not records:
                errors.append("no annotations supplied")
            print(json.dumps({"records": len(records), "valid": not errors, "errors": errors}, ensure_ascii=False))
            return 1 if errors else 0
        manifest = export_corpus(records, args.output, allow_constructed=args.allow_constructed,
                                 annotation_profile=args.profile)
        print(json.dumps({"counts": manifest["counts"], "output": str(args.output)}))
        return 0
    except (OSError, ValueError, httpx.HTTPError) as exc:
        print(f"{args.command} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
