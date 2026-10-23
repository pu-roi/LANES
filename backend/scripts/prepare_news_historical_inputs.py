"""Prepare/verify private E0 inputs using read-only SQL and zero model inference."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-database", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--worker-code-sha256", required=True)
    parser.add_argument("--retained-workload", type=Path)
    parser.add_argument("--retained-workload-sha256")
    parser.add_argument("--selection", type=Path, help="Pinned JSON {dataset_id, version_ids}; general inactive history batch")
    parser.add_argument("--selection-sha256")
    args = parser.parse_args()
    engine = None
    preparation_error_type = ()
    try:
        from sqlalchemy import create_engine
        from app.services.news_historical_preparation import build_preparation, save_private_package, text_sha, PreparationError
        preparation_error_type = PreparationError
        from app.core.config import settings
        from app.crud.news_historical_preparation import read_preparation_inventory
        from app.services.news_ner_durable.assets import load_trusted_assets, with_placement_assets
        from app.services.news_ner_durable.contracts import sha
        backend = Path(__file__).resolve().parents[1]
        root = backend.parent
        output = args.output.resolve()
        if not output.is_relative_to(root / "data") or output == root / "data":
            raise PreparationError("private_data_output_required")
        ignored = subprocess.run(["git", "check-ignore", "--quiet", "--", str(output)], cwd=root,
                                 capture_output=True, check=False)
        if ignored.returncode != 0:
            raise PreparationError("ignored_output_required")
        trusted = with_placement_assets(load_trusted_assets(args.bundle.resolve(), args.bundle_sha256,
            expected_worker_code_sha256=args.worker_code_sha256))
        retained = None
        if bool(args.retained_workload) != bool(args.retained_workload_sha256):
            raise PreparationError("retained_workload_binding_required")
        if args.retained_workload:
            import hashlib
            raw = args.retained_workload.read_bytes()
            if hashlib.sha256(raw).hexdigest() != args.retained_workload_sha256:
                raise PreparationError("retained_workload_changed")
            retained = {text_sha(row["text"]) for row in json.loads(raw)["rows"]}
        files = [backend / "app/services/news_historical_preparation.py",
                 backend / "app/crud/news_historical_preparation.py", Path(__file__)]
        import hashlib
        code = {path.relative_to(backend).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
        engine = create_engine(settings.DATABASE_URL, connect_args={"connect_timeout": 8})
        selected = None
        if bool(args.selection) != bool(args.selection_sha256):
            raise PreparationError('historical_selection_binding_required')
        if args.selection:
            from app.services.news_historical_processing import read_document
            selected = read_document(args.selection)
            if sha(selected) != args.selection_sha256 or set(selected) != {'dataset_id', 'version_ids'}:
                raise PreparationError('historical_selection_changed')
        inventory = read_preparation_inventory(engine, args.confirm_database,
            version_ids=tuple(selected['version_ids']) if selected else None)
        options = {}
        if selected:
            from app.services.news_historical_preparation import SourceSpec
            rows = inventory['sources']
            if len(rows) != len(selected['version_ids']):
                raise PreparationError('historical_selected_version_missing')
            options = dict(dataset_id=selected['dataset_id'], candidates=(), specs=tuple(
                SourceSpec(row['article_id'], row['version_id'], row['input_fingerprint'],
                    text_sha(row['input_snapshot'].get('article_text') or ''),
                    row['input_snapshot']['canonical_url'], row['input_snapshot']['publisher'],
                    row['input_snapshot']['published_at']) for row in rows))
        documents = build_preparation(inventory, {"manifest": trusted.manifest,
            "manifest_sha256": sha(trusted.manifest), "pipeline_version": trusted.pipeline_version,
            "preparation_code_sha256": sha(code)}, retained_text_hashes=retained, **options)
        if args.retained_workload:
            # Bind the optional cache oracle separately without altering a capture or its publication provenance.
            documents["manifest.json"]["retained_workload_sha256"] = args.retained_workload_sha256
            receipt = documents["receipt.json"]
            receipt["manifest_sha256"] = sha(documents["manifest.json"])
            receipt["document_sha256"]["manifest.json"] = receipt["manifest_sha256"]
        created = save_private_package(output, documents)
        print(json.dumps({"status": "prepared" if created else "existing_package_verified",
            **documents["receipt.json"]}))
        return 0
    except KeyboardInterrupt:
        print(json.dumps({"status": "interrupted", "error_code": "preparation_cancelled"}))
        return 130
    except Exception as exc:
        code = str(exc) if isinstance(exc, preparation_error_type) else "preparation_failed"
        print(json.dumps({"status": "failed", "error_code": code}))
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
