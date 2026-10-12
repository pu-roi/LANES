"""Gemini wire projections; canonical validation and evidence limits stay local."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

GeminiSchemaProfile = Literal["normalized", "compact", "inline"]
GEMINI_SCHEMA_PROFILES = ("normalized", "compact", "inline")
GEMINI_SCHEMA_REVISION = "gemini-json-schema-v1"


def gemini_response_schema(schema: dict[str, Any], profile: str = "normalized") -> dict[str, Any]:
    """Project only schema keywords, never property names or the original model.

    Inline accepts local acyclic definitions only. No remote schema retrieval,
    schema auto-selection, output coercion or canonical model mutation occurs.
    """
    if profile not in GEMINI_SCHEMA_PROFILES:
        raise ValueError("auditor_gemini_schema_profile_invalid")
    original = deepcopy(schema)
    definitions = original.get("$defs", {})

    def project(node: Any, active: frozenset[str] = frozenset()) -> Any:
        if not isinstance(node, dict):
            return deepcopy(node)
        if profile == "inline" and "$ref" in node:
            ref = node["$ref"]
            if (not isinstance(ref, str) or not ref.startswith("#/$defs/")
                    or ref in active or ref[8:] not in definitions
                    or set(node) != {"$ref"}):
                raise ValueError("auditor_gemini_schema_reference_invalid")
            return project(definitions[ref[8:]], active | {ref})
        result = {}
        for key, value in node.items():
            if key == "pattern":
                continue
            if key == "exclusiveMaximum":
                if node.get("type") != "integer" or type(value) is not int:
                    raise ValueError("auditor_gemini_schema_bound_invalid")
                result["maximum"] = min(node.get("maximum", value - 1), value - 1)
                continue
            if profile != "normalized" and key in {"minItems", "maxItems"}:
                continue
            if profile == "inline" and key in {"$defs", "title", "description"}:
                continue
            if key in {"$defs", "properties"}:
                result[key] = {name: project(child, active) for name, child in value.items()}
            elif key in {"items", "additionalProperties"} and isinstance(value, dict):
                result[key] = project(value, active)
            elif key in {"anyOf", "oneOf", "allOf", "prefixItems"}:
                result[key] = [project(child, active) for child in value]
            else:
                result[key] = deepcopy(value)
        return result

    return project(original)
