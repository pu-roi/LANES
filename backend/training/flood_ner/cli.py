"""Explicit offline corpus commands. No SQL, worker or provider configuration."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

from .annotation.schema import AnnotationRecord
from .annotation.validation import validate_corpus
from .export import TOKENIZER_NAME, CANDIDATE_TOKENIZER_NAME, corpus_tokenizer, export_corpus
from .window import LEGACY_WINDOW, PublicationWindow
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
    preflight = commands.add_parser('preflight-model', help='Run a pinned model on constructed cases in an isolated research interpreter')
    preflight.add_argument('--python', type=Path, required=True)
    preflight.add_argument('--model-manifest', type=Path, required=True)
    preflight.add_argument('--cases', type=Path, required=True)
    preflight.add_argument('--output', type=Path, required=True)
    tokenizer_check = commands.add_parser('qualify-model-tokenizer', help='Compare native and candidate tokenizers on 48 constructed cases only')
    tokenizer_check.add_argument('--python', type=Path, required=True)
    tokenizer_check.add_argument('--model-manifest', type=Path, required=True)
    tokenizer_check.add_argument('--cases', type=Path, required=True)
    tokenizer_check.add_argument('--output', type=Path, required=True)
    use_bundle = commands.add_parser('prepare-use-bundle', help='Prepare private study, appendix and held download candidates offline')
    use_bundle.add_argument('--cohort', type=Path, required=True)
    use_bundle.add_argument('--context', type=Path, required=True)
    use_bundle.add_argument('--review-packet', type=Path, required=True)
    use_bundle.add_argument('--output', type=Path, required=True)
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
    collect.add_argument('--repair-embedded-markup', action='store_true', help='Opt-in HTML script-tag repair; new capture version')
    reextract = commands.add_parser('reextract-source', help='Recover visible body from malformed scripts in frozen HTML')
    reextract.add_argument('capture', type=Path)
    reextract.add_argument('--output', type=Path, default=ARTIFACTS/'captures')
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
    cohort.add_argument('--coverage-policy', type=Path, help='Versioned JSON hard-quota policy')
    cohort.add_argument('--report-infeasible', action='store_true', help='Save reviewed pool and failures, without freezing partitions')
    cohort.add_argument('--selection-time-limit', type=int, default=60,
                        help='Bounded cohort solver seconds, 1–3600; default 60')
    context = commands.add_parser('review-context-pilot', help='Validate and freeze 40 contextual records paired to training passages')
    context.add_argument('folder', type=Path)
    context.add_argument('--annotations', type=Path, required=True)
    context.add_argument('--reviews', type=Path, required=True)
    context.add_argument('--output', type=Path, required=True)
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
    for command in (collect, report, cohort, qualify, validate):
        command.add_argument('--publication-start', help='Inclusive ISO calendar date; legacy default 2022-01-01')
        command.add_argument('--publication-end', help='Inclusive ISO calendar date; legacy default 2026-10-14')
    validate.add_argument('--news-register', type=Path, help='Required for verifying date-only publication evidence')
    for command in (validate, cohort, export):
        command.add_argument('--tokenizer', choices=[TOKENIZER_NAME, CANDIDATE_TOKENIZER_NAME], default=TOKENIZER_NAME)
    for command in (collect, cohort):
        command.add_argument('--candidate-ledger', type=Path, help='Cumulative URLs for this revision; maximum 300')
        command.add_argument('--baseline-inventory', type=Path, help='Immutable pre-revision array of source objects with URLs')
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare-use-bundle':
            from .use_bundle import prepare_use_bundle
            result = prepare_use_bundle(args.cohort,args.context,args.review_packet,args.output,REPO_ROOT)
            print(json.dumps({k:v for k,v in result.items() if k != 'files'},ensure_ascii=False))
            return 0
        if args.command == 'qualify-model-tokenizer':
            from .tokenizer_qualification import qualify_tokenizer
            result = qualify_tokenizer(args.python, args.model_manifest, args.cases, args.output, REPO_ROOT)
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result['state'] == 'passed' else 2
        if args.command == 'preflight-model':
            from .preflight import run_preflight
            result = run_preflight(args.python, args.model_manifest, args.cases, args.output, REPO_ROOT)
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result['state'] == 'passed' else 2
        explicit_window = bool(getattr(args, 'publication_start', None) or getattr(args, 'publication_end', None))
        window = PublicationWindow.parse([getattr(args, 'publication_start', None) or LEGACY_WINDOW.start.isoformat(),
                                          getattr(args, 'publication_end', None) or LEGACY_WINDOW.end.isoformat()])
        ledger_path = getattr(args,'candidate_ledger',None)
        baseline_path = getattr(args,'baseline_inventory',None)
        if bool(ledger_path) != bool(baseline_path):
            raise ValueError('candidate ledger and baseline inventory must be supplied together')
        budget = None
        if ledger_path:
            from .budget import collection_budget
            candidate_urls=json.loads(ledger_path.read_text(encoding='utf-8'))
            baseline=json.loads(baseline_path.read_text(encoding='utf-8'))
            if not isinstance(baseline,list) or any(not isinstance(s,dict) or not isinstance(s.get('url'),str) for s in baseline):
                raise ValueError('baseline inventory must be source objects with URLs')
            admitted_urls=[]
            if args.command=='build-cohort':
                rows=json.loads(args.news_register.read_text(encoding='utf-8'))
                if not isinstance(rows,list) or any(not isinstance(e,dict) for e in rows):
                    raise ValueError('news register must be an array of source objects')
                admitted_urls=[e.get('url') for e in rows if e.get('status')=='accepted']
            else:
                requested=json.loads(args.urls.read_text(encoding='utf-8'))
                if not isinstance(requested,list):raise ValueError('candidate URLs must be a JSON array')
                candidate_urls=candidate_urls+requested if isinstance(candidate_urls,list) else candidate_urls
            budget=collection_budget(candidate_urls,[s['url'] for s in baseline],admitted_urls)
        if args.command == 'review-context-pilot':
            from .contextual_pilot import ContextReview, write_contextual_pilot
            reviews = json.loads(args.reviews.read_text(encoding='utf-8'))
            if not isinstance(reviews, list):
                raise ValueError('context reviews must be a JSON array')
            result = write_contextual_pilot(args.folder, read_jsonl(args.annotations, AnnotationRecord),
                                           [ContextReview.model_validate_json(json.dumps(r)) for r in reviews],
                                           REPO_ROOT, args.output)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if args.command == 'reextract-source':
            from .sources import reextract_capture
            result = reextract_capture(args.capture, args.output)
            print(json.dumps({'source_id':result.source_id,'capture_version':result.capture_version,'characters':len(result.text)}))
            return 0
        if args.command == 'qualify-cohort':
            from .qualification import write_qualification
            result = write_qualification(args.folder, args.news_register, REPO_ROOT, args.output,
                                         model_register=args.model_register, reuse_register=args.reuse_register,
                                         window=window if explicit_window else None)
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
            errors = validate_reviewed(news_entries, {s.capture_version:s for s in sources}, window=window) + verify_capture_files(news_entries, REPO_ROOT)
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
            from .policy import CoveragePolicy
            policy = CoveragePolicy.model_validate_json(args.coverage_policy.read_bytes()) if args.coverage_policy else None
            result = build_cohort(records, reviews, sources, REPO_ROOT, args.output, pilot_ids=set(pilot_ids),
                                  window=window, tokenizer=args.tokenizer, policy=policy,
                                  news_entries=news_entries, report_infeasible=args.report_infeasible,
                                  collection_budget_metadata=budget, selection_time_limit=args.selection_time_limit)
            print(json.dumps(result, ensure_ascii=False))
            return 2 if result.get('revision_complete') is False else 0
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
            entries = collect_candidates(json.loads(args.urls.read_text(encoding="utf-8")), REPO_ROOT, args.output,
                                          window=window, repair_embedded_markup=args.repair_embedded_markup)
            if budget:
                (args.output/'collection_budget.json').write_bytes(json_bytes(budget))
                from .collection import article_key
                unique={article_key(url):url for url in candidate_urls}
                ledger_path.write_bytes(json_bytes([unique[key] for key in sorted(unique)]))
            print(json.dumps(collection_report(entries, window=window), ensure_ascii=False))
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
            report = write_reviewed_collection(entries, sources, args.output, args.expected_count, window=window)
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
            errors = validate_corpus(records, corpus_tokenizer(args.tokenizer))
            if explicit_window:
                from .collection import publication_date, validate_reviewed, verify_capture_files
                dates = {}
                if args.news_register:
                    sources, issues = inventory_sources(REPO_ROOT)
                    entries = json.loads(args.news_register.read_text(encoding='utf-8'))
                    errors += issues + validate_reviewed(entries, {s.capture_version:s for s in sources}, window=window) + verify_capture_files(entries, REPO_ROOT)
                    dates = {e['capture_version']: publication_date(e['publication_date']) for e in entries if e.get('status') == 'accepted'}
                for record in records:
                    day = (publication_date(record.source.published_at.isoformat()) if record.source.published_at else dates.get(record.source.capture_version))
                    if not window.contains(day):
                        errors.append(f'{record.record_id}: unknown or out-of-window publication date')
            if not records:
                errors.append("no annotations supplied")
            print(json.dumps({"records": len(records), "valid": not errors, "errors": errors}, ensure_ascii=False))
            return 1 if errors else 0
        manifest = export_corpus(records, args.output, allow_constructed=args.allow_constructed,
                                 annotation_profile=args.profile, tokenizer=args.tokenizer)
        print(json.dumps({"counts": manifest["counts"], "output": str(args.output)}))
        return 0
    except (OSError, ValueError, httpx.HTTPError) as exc:
        print(f"{args.command} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
