"""Read-only validation of private academic-use recommendations, never admission."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from .academic_use import validate_academic_review, verify_pointer
from .annotation.schema import AnnotationRecord, PLACE_LABELS
from .collection import publisher_for
from .sources import json_bytes, read_jsonl
from .use_bundle import validate_research_cohort, verified_reference


RECOMMEND = "recommend_private_academic_use"
HOLD = "hold_for_clarification"
FACTORS = {"purpose", "nature", "amount", "market_effect"}
BINDINGS = {
    "cohort_manifest", "context_manifest", "review_packet", "prior_review",
    "researcher_facts", "adviser_access", "access_verification",
    "copy_inventory", "evidence_register",
}


def _read_reference(reference: dict[str, Any], root: Path) -> Any:
    return json.loads(verified_reference(reference, root).read_text(encoding="utf-8"))


def _frozen_records(reference: dict[str, Any], filename: str,
                    records: list[AnnotationRecord], root: Path) -> dict[str, Any]:
    path = verified_reference(reference, root)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    if filename not in files:
        raise ValueError("frozen manifest must bind the supplied annotation records")
    for name, digest in files.items():
        if not isinstance(name, str) or Path(name).name != name or "/" in name or "\\" in name:
            raise ValueError("manifest entries must be local basenames")
        verified_reference({"path": (path.parent / name).relative_to(root).as_posix(),
                            "sha256": digest}, root)
    saved = read_jsonl(path.parent / filename, AnnotationRecord)
    if [r.model_dump(mode="json") for r in saved] != [r.model_dump(mode="json") for r in records]:
        raise ValueError("supplied annotations differ from the frozen bound records")
    return manifest


def _assessor(value: Any) -> None:
    try:
        when = datetime.fromisoformat(value["reviewed_at"])
        valid = value["kind"] == "ai" and bool(value["name"].strip()) and when.utcoffset() is not None
    except (KeyError, TypeError, ValueError, AttributeError):
        valid = False
    if not valid:
        raise ValueError("dated actual AI assessor required; no human approval inferred")


def _reasoned(row: dict[str, Any], evidence: dict[str, dict[str, Any]]) -> None:
    if (row.get("admission_status", "research_only") != "research_only"
            or row.get("reuse_status", "unknown") != "unknown"
            or row.get("admission_decision", "unresolved") != "unresolved"
            or row.get("publisher_permission_claimed", False) is not False):
        raise ValueError("a recommendation cannot carry an applied admission or permission")
    if row.get("recommendation") not in {RECOMMEND, HOLD}:
        raise ValueError("unsupported recommendation value")
    factors = row.get("fair_use_factors", {})
    if (not isinstance(factors, dict) or set(factors) != FACTORS
            or any(not isinstance(v, str) or not v.strip() for v in factors.values())
            or not isinstance(row.get("rationale"), str) or not row["rationale"].strip()
            or not isinstance(row.get("limitations"), list) or not row["limitations"]
            or any(not isinstance(v, str) or not v.strip() for v in row["limitations"])):
        raise ValueError("four substantive factors, rationale and limitations required")
    ids = row.get("evidence_ids")
    if (not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids)
            or len(set(ids)) != len(ids)
            or any(i not in evidence or evidence[i].get("substantive") is not True for i in ids)):
        raise ValueError("recommendations require substantive bound evidence; failed checks cannot support them")
    actions = row.get("remaining_actions", [])
    if (not isinstance(actions, list) or any(not isinstance(a, str) or not a.strip() for a in actions)
            or (row["recommendation"] == HOLD and not actions)):
        raise ValueError("held cases need concrete remaining actions")
    if row.get("basis_type") not in {"policy_and_research_rationale", "proposed_exception_unresolved"}:
        raise ValueError("separate policy/research rationale from unresolved exception proposals")
    _assessor(row.get("assessor"))


def validate_decision_proposal(proposal: dict[str, Any], records: list[AnnotationRecord],
                               contexts: list[AnnotationRecord], root: Path) -> dict[str, Any]:
    """Verify evidence and frozen inputs. Recommendations never change source flags."""
    root = root.resolve()
    if (not isinstance(proposal, dict) or proposal.get("schema_version") != "lanes-private-academic-proposal-v1"
            or proposal.get("scope") != "private_owner_only_academic_ner_training_evaluation"
            or type(proposal.get("training_admitted")) is not int or proposal["training_admitted"] != 0
            or type(proposal.get("docbin_exported")) is not int or proposal["docbin_exported"] != 0
            or proposal.get("automatic_admission") is not False
            or proposal.get("source_admission_changed") is not False
            or proposal.get("publisher_permission_claimed") is not False
            or proposal.get("distribution_ready") is not False):
        raise ValueError("proposal cannot imply applied admission, permission or distribution")
    bindings = proposal.get("bindings", {})
    if not isinstance(bindings, dict) or set(bindings) != BINDINGS:
        raise ValueError("all cohort, context, review, researcher and evidence bindings required")
    bound = {key: _read_reference(ref, root) for key, ref in bindings.items()}
    prior = bound["prior_review"]
    if any(bindings[k] != prior["bindings"][k] for k in ("cohort_manifest", "context_manifest", "review_packet")):
        raise ValueError("proposal must preserve the reviewed corrected cohort/context/packet bindings")
    validate_academic_review(prior, bound["review_packet"], records, root)
    validate_research_cohort(records)
    _frozen_records(bindings["cohort_manifest"], "grouped_annotations.jsonl", records, root)
    context_manifest = _frozen_records(bindings["context_manifest"], "context_annotations.jsonl", contexts, root)
    locations = {r.record_id: r for r in records}
    if (context_manifest.get("location_manifest_sha256") != bindings["cohort_manifest"]["sha256"]
            or len(contexts) != 40 or len({c.record_id for c in contexts}) != 40
            or Counter(c.passage_language for c in contexts) != Counter(english=20, taglish=20)):
        raise ValueError("forty unchanged paired contexts must bind this location cohort")
    for context in contexts:
        location = locations.get(context.record_id)
        if (location is None or location.split != "train" or context.split != "train"
                or context.annotation_profile != "context-rich-v1" or context.text != location.text
                or context.source.model_dump() != location.source.model_dump()
                or [e.model_dump() for e in context.entities if e.label in PLACE_LABELS]
                != [e.model_dump() for e in location.entities]
                or context.source.admission_status != "research_only" or context.source.reuse_status != "unknown"):
            raise ValueError("context/source/location references or research-only state changed")
    guidance = bound["adviser_access"]
    account = proposal.get("authorized_account")
    if (not isinstance(account, str) or not account or guidance.get("access", {}).get("authorized_account") != account
            or guidance.get("access", {}).get("conforms_to_named_account_privacy") is not True
            or guidance.get("use_scope", {}).get("private_research_and_training") is not True
            or guidance["use_scope"].get("permission_from_publishers_established_by_this_report") is not False):
        raise ValueError("private owner scope must match the bound researcher-reported guidance")
    if any(bound["researcher_facts"].get("bindings", {}).get(k) != bindings[k]
           for k in ("cohort_manifest", "context_manifest", "review_packet")):
        raise ValueError("researcher facts must refer to this corrected dataset/context")
    access = bound["access_verification"]
    items = access.get("items", [])
    if (not access.get("checked_at") or not items or len({i.get("id") for i in items}) != len(items)
            or any(len(i.get("permissions", [])) != 1 or i["permissions"][0].get("type") != "user"
                   or i["permissions"][0].get("role") != "owner"
                   or i["permissions"][0].get("emailAddress") != account for i in items)):
        raise ValueError("current evidence must show only the specified owner")
    inventory = bound["copy_inventory"]
    if (inventory.get("distinct_selected_articles") != 139 or not inventory.get("containers")
            or not inventory.get("scope_limitations")):
        raise ValueError("bounded copy inventory must distinguish containers from distinct articles")
    for container in inventory["containers"]:
        if (container.get("kind") not in {"directory", "local_archive", "remote_archive"}
                or type(container.get("complete_body_string_occurrences")) is not int
                or container["complete_body_string_occurrences"] < 0):
            raise ValueError("copy inventory needs measured counts and explicit container kinds")
        if container.get("reference"):
            verified_reference(container["reference"], root)
    evidence = {}
    for item in bound["evidence_register"]:
        key = item.get("evidence_id")
        if not isinstance(key, str) or not key or key in evidence:
            raise ValueError("unique evidence identifiers required")
        if item.get("pointer"):
            verify_pointer(item["pointer"], root)
        if item.get("reference"):
            verified_reference(item["reference"], root)
        if item.get("substantive") is True and (item.get("outcome") != "captured"
                                                  or not (item.get("pointer") or item.get("reference"))):
            raise ValueError("failed or unbound policy checks cannot be substantive evidence")
        evidence[key] = item
    prior_articles = {r["source_id"]: r for r in prior["article_reviews"]}
    sources = {r.source.source_id: r.source for r in records}
    rows = proposal.get("article_recommendations", [])
    if (not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows) or len(rows) != 139
            or len({r.get("source_id") for r in rows}) != 139 or {r.get("source_id") for r in rows} != set(sources)):
        raise ValueError("exactly one recommendation for each of the 139 articles required")
    for row in rows:
        source = sources[row["source_id"]]
        expected_ids = sorted(r.record_id for r in records if r.source.source_id == source.source_id)
        flags = prior_articles[source.source_id].get("exception_flags", [])
        if (row.get("publisher") != publisher_for(source.url) or row.get("text_sha256") != source.text_sha256
                or row.get("capture_version") != source.capture_version or row.get("sample_ids") != expected_ids
                or row.get("exception_flags") != flags or set(row.get("exception_dispositions", {})) != set(flags)
                or any(not isinstance(v, str) or not v.strip() for v in row["exception_dispositions"].values())):
            raise ValueError("article identity, sample membership or exception dispositions differ")
        _reasoned(row, evidence)
    publishers = proposal.get("publisher_recommendations", [])
    expected_publishers = {r["publisher"] for r in rows}
    if len(publishers) != 3 or {p.get("publisher") for p in publishers} != expected_publishers:
        raise ValueError("three distinct publisher summaries required")
    for publisher in publishers:
        articles = [r for r in rows if r["publisher"] == publisher["publisher"]]
        recommended = sorted(r["source_id"] for r in articles if r["recommendation"] == RECOMMEND)
        held = sorted(r["source_id"] for r in articles if r["recommendation"] == HOLD)
        if (publisher.get("source_ids") != sorted(r["source_id"] for r in articles)
                or publisher.get("recommended_source_ids") != recommended or publisher.get("held_source_ids") != held
                or publisher.get("recommendation") != (RECOMMEND if recommended else HOLD)
                or publisher.get("covers_all_publisher_articles") != (not held)):
            raise ValueError("publisher recommendations must preserve explicit article-level holds")
        _reasoned(publisher, evidence)
    decisions = proposal.get("actual_project_decisions", [])
    if len(decisions) != 3 or {d.get("publisher") for d in decisions} != expected_publishers:
        raise ValueError("three separate unresolved project decision forms required")
    for decision in decisions:
        if (decision.get("actual_decision") != "unresolved" or decision.get("decision_maker") is not None
                or decision.get("decision_date") is not None or decision.get("is_publisher_permission") is not False):
            raise ValueError("an AI proposal cannot manufacture a human decision or publisher permission")
        for key in ("researcher_facts", "adviser_access", "prior_review"):
            if decision.get("evidence_references", {}).get(key) != bindings[key]:
                raise ValueError("forms need resolvable hash-bound facts, guidance and review references")
    unchanged = prior["unchanged_nonacademic_outcomes"]
    if (proposal.get("unchanged_nonacademic_outcomes") != unchanged
            or proposal.get("nonacademic_outcomes_sha256") != hashlib.sha256(json_bytes(unchanged)).hexdigest()):
        raise ValueError("all twelve nonacademic outcomes must be preserved")
    counts = Counter(r["recommendation"] for r in rows)
    return {"articles": 139, "samples": 400, "contextual_pairs": 40,
            "recommendations": dict(counts), "actual_project_decisions": 0,
            "training_admitted": 0, "docbin_exported": 0}
