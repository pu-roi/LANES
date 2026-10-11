"""Build a no-write research dataset from complete staff exports and episode reviews."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from app.services.recession_dataset_service import EpisodeReview, qualify_recession_episodes


def build(export: Path, reviews: Path | None, output: Path) -> dict:
    if output.exists():
        raise ValueError("Use a new output directory; recorded evaluations cannot be overwritten.")
    inputs = {"export": export, **({"episode_reviews": reviews} if reviews else {})}
    snapshots = {}
    for role, path in inputs.items():
        with path.open("rb") as handle:
            snapshots[role] = handle.read(10_000_001)
        if len(snapshots[role]) > 10_000_000:
            raise ValueError("Input exceeds the bounded 10 MB research file limit.")
    # Parse and hash the same captured bytes, even if a source file changes
    # while qualification is running. Never hash a second, different read.
    envelope = json.loads(snapshots["export"].decode("utf-8-sig"))
    raw_rules = json.loads(snapshots["episode_reviews"].decode("utf-8-sig")) if reviews else []
    rules = [EpisodeReview.model_validate(row) for row in raw_rules]
    result = qualify_recession_episodes(envelope, rules)
    # Only allowlisted numerical/source identities are output. Original source
    # text, media, URLs, names and request UUIDs are deliberately not copied.
    result.update(generated_at=datetime.now(timezone.utc).isoformat(),
        input_sha256={role: hashlib.sha256(blob).hexdigest() for role, blob in snapshots.items()},
        builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        qualifier_sha256=hashlib.sha256((Path(__file__).parents[1]/"app/services/recession_dataset_service.py").read_bytes()).hexdigest())
    output.mkdir(parents=True)
    (output/"dataset.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    return {"source_observations": result["source_observations"], "source_reports": result["source_reports"],
        "source_review_states": result["source_review_states"], "numeric_depth_sources": result["numeric_depth_sources"],
        "episode_reviews": len(rules), "conditional_research_candidates": len(result["candidates"]),
        "reports_without_episode_review": len(result["reports_without_episode_review"]),
        "production_training_admitted": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.export, args.reviews, args.output)))
    except (ValueError, OSError, TypeError) as exc:
        # Do not include Pydantic input dumps containing private source text.
        raise SystemExit(f"Dataset build failed ({type(exc).__name__}); check export/review contract and output path.") from None


if __name__ == "__main__":
    main()
