"""OSM/NOAH/Pasig evidence previews shared by saved extraction and staff reads."""
from __future__ import annotations

import hashlib
import csv
import io
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from shapely import union_all, line_merge
from shapely.geometry import shape, mapping
from shapely.errors import ShapelyError

from app.schemas.news_extraction import ExtractedClaim, RoadPlacementEvidence
from app.schemas.news_placement import NewsPlacementPreview, PlacementFragment, PlacementHistoryRow, PlacementSection
from app.services.placement_geometry_service import geometry_id, line_parts
from app.services.flood_depth import get_flood_depth_measurement
from app.services.article_road_context_service import match_article_road_context
from app.services.article_road_match_service import OSMRoadSection
from app.services.news_road_placement_service import NewsRoadPlacementProvider, city_key, get_news_road_placement_provider
from app.services.noah_road_prediction_service import RoadSectionEvidence, rank_measured_road_sections
from app.services.noah_vector_catalog_service import NoahAssetError, NoahVectorCatalog, get_noah_vector_catalog, metric_geometry
from app.services.pasig_historical_service import DEFAULT_PASIG_CLEAN_CSV


class NewsPlacementPreviewService:
    def __init__(self, roads: NewsRoadPlacementProvider, noah: NoahVectorCatalog,
                 history_path: Path = DEFAULT_PASIG_CLEAN_CSV) -> None:
        self.roads, self.noah, self.history_path = roads, noah, history_path
        self.history_digest: str | None = None
        self.history_available = False
        try:
            if history_path.stat().st_size <= 2_000_000:
                raw = history_path.read_bytes()
                required = {"source_year", "source_record_no", "barangay_canonical", "street_normalized", "landmark_normalized"}
                reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
                if not required.issubset(set(reader.fieldnames or ())):
                    raise ValueError("Invalid historical source columns")
                self.history_digest = hashlib.sha256(raw).hexdigest()
                self.history_available = True
        except (OSError, ValueError, UnicodeError):
            pass  # Exposed as history_status=source_unavailable for Pasig claims.

    @property
    def revision(self) -> str:
        return f"fragments-v1:osm-{self.roads.revision}:noah-{self.noah.revision}:history-{self.history_digest or 'none'}"

    def preview(self, claim: ExtractedClaim, placement: RoadPlacementEvidence | None = None) -> NewsPlacementPreview:
        placement = placement or self.roads.resolve(claim)
        is_pasig = city_key(claim.canonical_city or "") == "pasig"
        depth = get_flood_depth_measurement(claim.depth_canonical)
        metadata = dict(total_candidate_count=placement.total_candidate_count,
                        reported_severity=depth.severity.value if depth else None,
                        barangay_catalog_sha256=placement.barangay_catalog_sha256,
                        barangay_source_id=placement.barangay_source_id,
                        barangay_psgc_code=placement.barangay_psgc_code,
                        barangay_osm_relation_id=placement.barangay_osm_relation_id,
                        barangay_source_url=placement.barangay_source_url,
                        barangay_source_classification=placement.barangay_source_classification,
                        barangay_boundary_status=placement.barangay_boundary_status,
                        candidates_truncated=placement.candidates_truncated,
                        osm_source_id=placement.source_id,
                        osm_catalog_sha256=placement.catalog_sha256,
                        osm_snapshot_at=placement.snapshot_at,
                        city_relation_id=placement.city_relation_id,
                        noah_catalog_sha256=self.noah.digest,
                        history_status=("available" if self.history_available else "source_unavailable") if is_pasig else "not_applicable",
                        history_sha256=self.history_digest if is_pasig else None)
        if self.noah.manifest:
            metadata.update(noah_source_ids={p: s.source_id for p, s in self.noah.manifest.scenarios.items()},
                            noah_attribution=self.noah.manifest.attribution)
        if not placement.candidates:
            return NewsPlacementPreview(status="source_unavailable" if placement.status == "source_unavailable" else "unresolved",
                                        reason=placement.reason, **metadata)
        # The provider's city relation must agree with the supplied placement.
        _ = self.roads.revision
        city = self.roads.cities.get(city_key(claim.canonical_city or ""))
        boundary = self.roads.boundaries.get(city_key(claim.canonical_city or ""))
        if (city is None or boundary is None or placement.catalog_sha256 != self.roads.digest
                or placement.city_relation_id != city.relation_id):
            return NewsPlacementPreview(status="unresolved", reason="placement_source_mismatch", **metadata)
        barangay_boundary = self.roads.barangay_boundary(claim)
        if claim.canonical_barangay and (barangay_boundary is None
                or placement.barangay_catalog_sha256 != self.roads.barangays.digest
                or placement.barangay_boundary_status != "available"):
            return NewsPlacementPreview(status="unresolved", reason="missing_valid_barangay_boundary", **metadata)
        sections = [OSMRoadSection(c.candidate_id, claim.canonical_road or claim.raw_place_name,
                    c.centerline_geojson, tuple(c.osm_way_ids),
                    tuple(tuple(names) for names in c.cross_streets), placement.source_id or "",
                    c.ambiguous_carriageway) for c in placement.candidates if len(c.cross_streets) == 2]
        try:
            context = match_article_road_context(claim, sections, boundary,
                         self.history_path if is_pasig and self.history_available else None,
                         barangay_boundary=barangay_boundary,
                         reported_span_section_ids=frozenset(c.candidate_id for c in placement.candidates if c.kind == "reported_span"))
        except (OSError, ValueError, ShapelyError) as exc:
            return NewsPlacementPreview(status="source_unavailable", reason="invalid_placement_context",
                                        uncertainty_reasons=[type(exc).__name__], **metadata)
        def history_row(row: object) -> PlacementHistoryRow:
            value = asdict(row)
            value.pop("section_ids")
            return PlacementHistoryRow(**value)
        metadata["unmatched_history"] = [history_row(row) for row in context.unmatched_history_rows]
        by_id = {c.candidate_id: c for c in placement.candidates}
        evidence, output, measurements = [], [], {}
        for candidate_id in context.candidate_section_ids:
            candidate = by_id[candidate_id]
            line = shape(candidate.centerline_geojson)
            if barangay_boundary is not None and not barangay_boundary.covers(line):
                return NewsPlacementPreview(status="unresolved", reason="placement_outside_barangay", **metadata)
            metric = metric_geometry(line)
            rows = context.historical_rows_by_section.get(candidate_id, ())
            level = context.article_place_levels[candidate_id]
            evidence.append(RoadSectionEvidence(candidate_id, metric, placement.source_id or "",
                            level, len(rows), not candidate.ambiguous_carriageway))
            output.append(PlacementSection(candidate_id=candidate_id, kind=candidate.kind,
                centerline_geojson=candidate.centerline_geojson, osm_way_ids=candidate.osm_way_ids,
                cross_streets=candidate.cross_streets, ambiguous_carriageway=candidate.ambiguous_carriageway,
                article_place_level=level, approximate_length_m=metric.length,
                matching_history=[history_row(row) for row in rows]))
        if not evidence:
            return NewsPlacementPreview(status="unresolved", reason=context.reason, **metadata)
        uncertainties = []
        if claim.is_historical:
            uncertainties.append("historical_claim_preview_only")
        if is_pasig and not self.history_available:
            uncertainties.append("pasig_history_unavailable")
        try:
            for candidate in output:
                intersections = self.noah.intersections(shape(candidate.centerline_geojson))
                overlaps = {p: {h: metric_geometry(g).length for h, g in classes.items()}
                            for p, classes in intersections.items()}
                measurements[candidate.candidate_id] = overlaps
                candidate.modeled_overlap_m = overlaps
                parts = []
                for period, classes in intersections.items():
                    source = self.noah.manifest.scenarios[period]
                    for hazard, geometry in classes.items():
                        for part in line_parts(geometry):
                            if len(candidate.modeled_fragments) >= 512:
                                raise NoahAssetError("noah_fragment_limit")
                            parts.append(part)
                            candidate.modeled_fragments.append(PlacementFragment(
                                fragment_id=geometry_id(f"{candidate.candidate_id}:{self.noah.digest}:{period}:{hazard}", part),
                                centerline_geojson=mapping(part), approximate_length_m=metric_geometry(part).length,
                                return_period=period, hazard_class=hazard,
                                noah_source_id=source.source_id, noah_archive_sha256=source.archive_sha256))
                # The display is the modeled envelope across all three scenarios.
                # Dissolve duplicate overlap to avoid stacking transparent colors;
                # merge only touching linework, preserving every real gap.
                display = line_merge(union_all(parts)) if parts else None
                candidate.preview_geometry = mapping(display) if display is not None else None
                candidate.fragment_status = "available" if parts else "no_modeled_overlap"
            prediction = rank_measured_road_sections(evidence, measurements, metadata.get("noah_source_ids", {}))
        except (NoahAssetError, ValueError, ShapelyError) as exc:
            for candidate in output:
                candidate.preview_geometry = None
                candidate.modeled_fragments = []
                candidate.fragment_status = "source_unavailable"
            reason = str(exc) if isinstance(exc, NoahAssetError) else "invalid_noah_measurements"
            return NewsPlacementPreview(status="source_unavailable", reason=reason, candidates=output,
                                        uncertainty_reasons=uncertainties, **metadata)
        indices = {section.section_id: i for i, section in enumerate(prediction.ranked_sections)}
        output.sort(key=lambda item: indices[item.candidate_id])
        for candidate in output:
            candidate.modeled_overlap_fraction = {
                p: min(1.0, sum(values.values()) / candidate.approximate_length_m)
                for p, values in measurements[candidate.candidate_id].items()}
        selected, reason = prediction.predicted_section_id, prediction.reason
        # Incomplete candidate sets or ungrounded article qualifiers cannot be
        # promoted merely because a hazard score picked one remaining section.
        if placement.candidates_truncated:
            selected, reason = None, "candidate_set_truncated"
        elif context.reason == "local_place_not_grounded":
            selected, reason = None, context.reason
        elif is_pasig and not self.history_available:
            selected, reason = None, "pasig_history_unavailable"
        elif (claim.is_negated or claim.is_forecast or not claim.flood_mentioned
              or "photo_caption_only" in claim.uncertainty_reasons
              or "location_context_only" in claim.uncertainty_reasons):
            selected, reason = None, "claim_is_not_reported_flood_evidence"
        selected_candidate = by_id.get(selected) if selected else None
        return NewsPlacementPreview(status="predicted_candidate" if selected else "ambiguous",
            reason=reason, selected_candidate_id=selected,
            placement_kind=("reported" if selected_candidate.kind == "reported_span" else "predicted") if selected_candidate else None,
            candidates=output, uncertainty_reasons=uncertainties, **metadata)


def get_news_placement_preview_service() -> NewsPlacementPreviewService:
    return _preview_service(get_news_road_placement_provider(), get_noah_vector_catalog())


@lru_cache(maxsize=1)
def _preview_service(roads: NewsRoadPlacementProvider, noah: NoahVectorCatalog) -> NewsPlacementPreviewService:
    return NewsPlacementPreviewService(roads, noah)
