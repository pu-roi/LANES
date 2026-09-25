"""Evaluation script for Taglish NLP extraction service.

Benchmarks extraction performance on the 50-item labeled evaluation set in
data/taglish_flood_eval_set.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.taglish_extraction_service import extract_taglish_flood_facts


def run_evaluation() -> dict:
    repo_root = Path(__file__).resolve().parent.parent.parent
    eval_file = repo_root / "data" / "taglish_flood_eval_set.json"
    if not eval_file.exists():
        eval_file = repo_root / "backend" / "tests" / "fixtures" / "taglish_flood_eval_set.json"
    if not eval_file.exists():
        eval_file = Path("data/taglish_flood_eval_set.json")
    if not eval_file.exists():
        eval_file = Path("backend/tests/fixtures/taglish_flood_eval_set.json")

    with open(eval_file, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    total_items = len(eval_data)
    total_claims_expected = sum(len(item["expected_claims"]) for item in eval_data)

    correct_flood_mentioned = 0
    correct_negated = 0
    correct_forecast = 0
    correct_historical = 0

    barangay_matches = 0
    barangay_expected_total = 0

    depth_matches = 0
    depth_expected_total = 0

    condition_matches = 0
    condition_expected_total = 0

    start_time = time.perf_counter()

    verbose = "--verbose" in sys.argv
    for item in eval_data:
        article_input = NewsArticleExtractorInput(
            article_id=item["id"],
            canonical_url=f"https://example.com/eval/{item['id']}",
            publisher="Evaluation Suite",
            title=item["text"][:60],
            excerpt=item["text"],
            article_text=item["text"] if item.get("category") != "metadata_only" else None,
        )

        res = extract_taglish_flood_facts(article_input)

        # Check high-level flags from claims
        has_active_flood_claim = any(c.flood_mentioned for c in res.claims)
        has_negated_claim = any(c.is_negated for c in res.claims)
        has_forecast_claim = any(c.is_forecast for c in res.claims)
        has_historical_claim = any(c.is_historical for c in res.claims)

        if has_active_flood_claim == item["expected_flood_mentioned"]:
            correct_flood_mentioned += 1
        elif verbose:
            print(f"[MISMATCH Item {item['id']}] flood_mentioned: got {has_active_flood_claim}, exp {item['expected_flood_mentioned']}. Text: {item['text']}")

        if has_negated_claim == item["expected_is_negated"]:
            correct_negated += 1
        elif verbose:
            print(f"[MISMATCH Item {item['id']}] negated: got {has_negated_claim}, exp {item['expected_is_negated']}")

        if has_forecast_claim == item["expected_is_forecast"]:
            correct_forecast += 1
        if has_historical_claim == item["expected_is_historical"]:
            correct_historical += 1

        # Compare expected claims against extracted claims
        for exp in item["expected_claims"]:
            if exp["canonical_barangay"] is not None:
                barangay_expected_total += 1
                if any(c.canonical_barangay == exp["canonical_barangay"] for c in res.claims):
                    barangay_matches += 1
                elif verbose:
                    print(f"[MISMATCH Item {item['id']}] barangay: missing {exp['canonical_barangay']} in {[c.canonical_barangay for c in res.claims]}")

            if exp["expected_depth_canonical"] is not None:
                depth_expected_total += 1
                if any(c.depth_canonical == exp["expected_depth_canonical"] for c in res.claims):
                    depth_matches += 1
                elif verbose:
                    print(f"[MISMATCH Item {item['id']}] depth: missing {exp['expected_depth_canonical']} in {[c.depth_canonical for c in res.claims]}")

            if exp["expected_condition"] != "unknown":
                condition_expected_total += 1
                if any(c.condition == exp["expected_condition"] for c in res.claims):
                    condition_matches += 1
                elif verbose:
                    print(f"[MISMATCH Item {item['id']}] condition: missing {exp['expected_condition']} in {[c.condition for c in res.claims]}")

    total_time = time.perf_counter() - start_time
    latency_per_item_ms = (total_time / total_items) * 1000

    metrics = {
        "total_items": total_items,
        "total_expected_claims": total_claims_expected,
        "flood_mentioned_accuracy": correct_flood_mentioned / total_items,
        "negation_accuracy": correct_negated / total_items,
        "forecast_accuracy": correct_forecast / total_items,
        "historical_accuracy": correct_historical / total_items,
        "canonical_barangay_recall": barangay_matches / barangay_expected_total if barangay_expected_total else 1.0,
        "depth_canonical_recall": depth_matches / depth_expected_total if depth_expected_total else 1.0,
        "condition_recall": condition_matches / condition_expected_total if condition_expected_total else 1.0,
        "total_duration_sec": total_time,
        "latency_per_item_ms": latency_per_item_ms,
    }

    print("=" * 60)
    print("TAGLISH NLP EXTRACTION EVALUATION REPORT")
    print("=" * 60)
    print(f"Total Evaluation Items: {metrics['total_items']}")
    print(f"Total Processing Time: {metrics['total_duration_sec']:.4f}s ({metrics['latency_per_item_ms']:.2f} ms/item)")
    print(f"Flood Mention Detection Accuracy: {metrics['flood_mentioned_accuracy']*100:.1f}%")
    print(f"Negation Detection Accuracy:      {metrics['negation_accuracy']*100:.1f}%")
    print(f"Forecast Detection Accuracy:      {metrics['forecast_accuracy']*100:.1f}%")
    print(f"Historical Detection Accuracy:    {metrics['historical_accuracy']*100:.1f}%")
    print(f"Canonical Barangay Recall:        {metrics['canonical_barangay_recall']*100:.1f}% ({barangay_matches}/{barangay_expected_total})")
    print(f"Canonical Depth Match Recall:     {metrics['depth_canonical_recall']*100:.1f}% ({depth_matches}/{depth_expected_total})")
    print(f"Condition Match Recall:           {metrics['condition_recall']*100:.1f}% ({condition_matches}/{condition_expected_total})")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    run_evaluation()
