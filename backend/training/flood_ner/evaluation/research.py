"""Research evidence pointers, deliberately separate from pilot annotations."""
from __future__ import annotations

from typing import Any

from ..annotation.schema import SourceCapture

# Anchors locate captured passages; reports contain offsets/hashes, not copied article bodies.
CASES = (
    ("named-sitio-parent", "GMA-997943", "In Sitio Veterans", "Named sitio with explicit barangay context; recognition and parent resolution are separate."),
    ("clearance-clock", "GMA-997943", "Before 7 a.m.", "Local recession/clearance wording has its own observation role; publication is not onset."),
    ("discourse-boundary", "GMA-997943", "Meanwhile in Marikina", "A city/source transition separates the preceding observation scope."),
    ("river-gauge", "GMA-997943", "16 meters early", "River gauge readings must not become road-water depths."),
    ("borrowed-number-name", "GMA-997943", "Barangay Talon Tres", "A numeral embedded in a proper name remains part of that name."),
    ("shared-measurement", "TRIBUNE-20260830", "The Genesis and Victory Liner", "Two terminals share a supported depth and chronology, without independent invented measurements."),
    ("recession-rising", "TRIBUNE-20260830", "Levels receded Sunday morning", "Recession followed by renewed rising is not lasting clearance."),
    ("collective-range", "TRIBUNE-20260830", "Several towns including", "A collective depth range does not provide an exact reading for every road."),
    ("taglish-quote", "TRIBUNE-20260830", '"Nakakapagod', "Mixed-language quotation requires attribution; a surrounding English article does not erase its language."),
    ("tagalog-depth", "GMA-997853", "Sa Bauan, Batangas", "Verbal road depth without a supported clock retains unknown observation time."),
    ("habitual-current", "GMA-997853", "Sa Barangay Roxas District", "Habitual flood context must be distinguished from nearby current observations."),
    ("warning-time", "GMA-997853", "Itinaas", "A warning issuance clock does not establish road-flood onset."),
    ("compound-address", "QC-ADDRESS-DIRECTORY", "Lot 1 Block 18, Kapisanan", "Preserve lot, block, road, area, sitio, barangay and city roles separately."),
    ("named-purok", "QC-ADDRESS-DIRECTORY", "Purok 7, Sitio Rolling", "Purok/sitio hierarchy can combine numbers with names and boundary context."),
    ("larger-purok", "QC-ADDRESS-DIRECTORY", "Purok 20", "Numbers beyond the illustrative 4/6 need corpus support."),
    ("roman-unit", "QC-ADDRESS-DIRECTORY", "Unit IV, Plaza", "Roman-number unit syntax needs explicit handling and source context."),
    ("block-abbreviation", "QC-ADDRESS-DIRECTORY", "Blk. 10 Phase 1", "Abbreviated block and phase components must not be collapsed."),
    ("letter-suffix", "QC-ADDRESS-DIRECTORY", "Lot 158-B", "Alphanumeric lot identities retain their full suffix."),
    ("compact-address", "QC-ADDRESS-DIRECTORY", "B1 L21", "Compact block/lot notation is a research gap, not an automatic alias."),
    ("numbered-street", "QC-ADDRESS-DIRECTORY", "7th St.", "Ordinal street names differ from units or purok designators."),
)


def research_matrix(sources: list[SourceCapture]) -> dict[str, Any]:
    by_id = {source.source_id: source for source in sources}
    cases = []
    for case_id, source_id, anchor, interpretation in CASES:
        source = by_id.get(source_id)
        start = source.text.find(anchor) if source else -1
        if start >= 0:
            line_start = source.text.rfind("\n", 0, start) + 1
            line_end = source.text.find("\n", start)
            if line_end < 0:
                line_end = len(source.text)
        else:
            line_start = line_end = None
        cases.append({"case_id": case_id, "source_id": source_id, "status": "captured_evidence" if start >= 0 else "missing_evidence",
                      "url": source.url if source else None, "text_sha256": source.text_sha256 if source else None,
                      "passage_start": line_start, "passage_end": line_end, "interpretation": interpretation,
                      "annotation_status": "research_case_not_pilot_label"})
    return {"schema_version": "lanes-flood-ner-research-v1", "cases": cases,
            "missing_cases": [c["case_id"] for c in cases if c["status"] == "missing_evidence"],
            "limitations": ["Interpretations are research proposals; source-exact pointers do not establish independent gold labels.",
                            "Official address-directory examples establish syntax, not current flooding."]}
