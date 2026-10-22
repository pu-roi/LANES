"""Explicit method identities for queue isolation; no activation/configuration IO."""
from __future__ import annotations

import hashlib
import json
import re

from app.schemas.news_ner_result import ProcessingMode

NATIVE_MANIFEST_KEYS = frozenset({
    "model", "tokenizer", "runtime", "location_rules", "context_rules",
    "projection", "source_check", "geography",
})


def native_pipeline_version(manifest: dict) -> str:
    """Every behavior/asset family participates; paths and secrets do not belong here."""
    if set(manifest) != NATIVE_MANIFEST_KEYS or any(not value for value in manifest.values()):
        raise ValueError("ner_pipeline_manifest_incomplete")
    encoded = json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "ner-v1:" + hashlib.sha256(encoded).hexdigest()


def validate_processing_identity(mode: ProcessingMode, pipeline_version: str) -> None:
    if mode not in ("rules_only", "ner_rules_v1"):
        raise ValueError("extraction_mode_unsupported")
    if not isinstance(pipeline_version, str) or not 1 <= len(pipeline_version) <= 100:
        raise ValueError("pipeline_identity_invalid")
    native = re.fullmatch(r"ner-v1:[a-f0-9]{64}", pipeline_version) is not None
    if (mode == "ner_rules_v1" and not native) or (mode == "rules_only" and pipeline_version.startswith("ner-v1:")):
        raise ValueError("pipeline_method_mismatch")
