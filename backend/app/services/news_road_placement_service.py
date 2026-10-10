"""Server-owned OSM snapshot placement shared by saved and discovered extraction.

Road evidence is separate from activation geometry. No HTTP, database writes,
hazard probability, flooded-width buffer, or automatic approval occurs here.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import shape, mapping
from shapely.errors import ShapelyError
from shapely.geometry.base import BaseGeometry

from app.schemas.news_extraction import ExtractedClaim, RoadPlacementCandidate, RoadPlacementEvidence
from app.services.barangay_boundary_service import BarangayBoundaryProvider, get_barangay_boundary_provider
from app.services.placement_geometry_service import geometry_id, line_parts
from app.services.article_road_context_service import _contains_name, match_article_road_context
from app.services.article_road_match_service import (
    OSMRoadWay, OSMRoadSection, ROAD_SUFFIXES, _span_cross_streets, _way_matches, match_article_road_span,
    normalize_name, split_named_road_at_intersections,
)

MAX_CATALOG_BYTES = 96 * 1024 * 1024
MAX_COMPRESSED_BYTES = 16 * 1024 * 1024
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parents[2] / "runtime_data" / "osm"
NCR_CITIES = frozenset({"manila", "quezon city", "pasig", "mandaluyong", "makati", "pasay",
    "marikina", "taguig", "caloocan", "valenzuela", "navotas", "malabon", "muntinlupa",
    "las pinas", "paranaque", "san juan", "pateros"})


def city_key(name: str) -> str:
    name = normalize_name(name)
    if name.startswith("city of "):
        name = name[8:]
    if name.endswith(" city") and name != "quezon city":
        name = name[:-5]
    return name


class CatalogRouteReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relation_id: int = Field(gt=0)
    reference: str = Field(min_length=1, max_length=100)


def road_aliases(item: CatalogWay | IncompleteWay) -> tuple[str, ...]:
    """Route membership is source evidence; the road suffix is a display form."""
    references = [name for route in item.route_references for name in (route.reference, f"{route.reference} Road")]
    return tuple(dict.fromkeys([*item.aliases, *references]))


class CatalogWay(BaseModel):
    model_config = ConfigDict(extra="forbid")
    osm_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=300)
    nodes: list[tuple[int, float, float]] = Field(min_length=2, max_length=10000)
    aliases: list[str] = Field(default_factory=list, max_length=100)
    route_references: list[CatalogRouteReference] = Field(default_factory=list, max_length=100)
    bridge: str = ""
    tunnel: str = ""
    layer: str = ""


class CatalogCity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    relation_id: int = Field(gt=0)
    boundary: dict


class IncompleteWay(BaseModel):
    model_config = ConfigDict(extra="forbid")
    osm_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=300)
    aliases: list[str] = Field(default_factory=list, max_length=100)
    route_references: list[CatalogRouteReference] = Field(default_factory=list, max_length=100)


class RoadCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format_version: int
    source_id: str = Field(min_length=1, max_length=200)
    snapshot_at: datetime
    osm_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    attribution: str
    cities: list[CatalogCity] = Field(min_length=1, max_length=17)
    ways: list[CatalogWay] = Field(max_length=100000)
    incomplete_ways: list[IncompleteWay] = Field(default_factory=list, max_length=100000)


class NewsRoadPlacementProvider:
    def __init__(self, directory: Path, barangays: BarangayBoundaryProvider | None = None) -> None:
        self.directory = directory
        self.barangays = barangays or get_barangay_boundary_provider()
        self.error: str | None = None
        self.digest: str | None = None
        self.catalog: RoadCatalog | None = None
        self.ways: tuple[OSMRoadWay, ...] = ()
        self.boundaries: dict = {}
        self.cities: dict[str, CatalogCity] = {}
        self._name_index: dict[str, dict[int, OSMRoadWay]] = {}
        self._loaded = False
        try:
            manifest_path = directory / "manifest.json"
            if manifest_path.stat().st_size > 4096:
                raise ValueError("oversized manifest")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.digest = manifest["catalog_sha256"]
            if not isinstance(self.digest, str) or len(self.digest) != 64 or any(c not in "0123456789abcdef" for c in self.digest):
                raise ValueError("invalid digest")
        except FileNotFoundError:
            self.error = "osm_catalog_not_configured"
        except (OSError, ValueError, KeyError, TypeError):
            self.error = "invalid_osm_catalog_manifest"

    @property
    def revision(self) -> str:
        self._load()
        digest = self.digest if self.digest else "none"
        road_revision = digest if self.catalog is not None and not self.error else f"bad-{digest}"
        return f"{road_revision}:barangay-{self.barangays.revision}"

    def barangay_boundary(self, claim: ExtractedClaim) -> BaseGeometry | None:
        boundary = self.boundaries.get(city_key(claim.canonical_city or ""))
        if boundary is None or not claim.canonical_barangay:
            return None
        return self.barangays.resolve(claim.canonical_city or "", claim.canonical_barangay, boundary)

    def locality_boundary(self, claim: ExtractedClaim) -> BaseGeometry | None:
        """Qualified catalog locality only; never evidence of current flooding."""
        self._load()
        if self.error:
            return None
        city = self.boundaries.get(city_key(claim.canonical_city or ""))
        if city is None:
            return None
        return self.barangay_boundary(claim) if claim.canonical_barangay else city

    def _clip_candidates(self, candidates: list[RoadPlacementCandidate], boundary: BaseGeometry) -> list[RoadPlacementCandidate]:
        clipped = []
        for candidate in candidates:
            line = shape(candidate.centerline_geojson)
            for part in line_parts(line.intersection(boundary)):
                endpoints = []
                for point in (part.coords[0], part.coords[-1]):
                    endpoints.append(next((names for original, names in zip(
                        (line.coords[0], line.coords[-1]), candidate.cross_streets) if point == original), []))
                clipped.append(candidate.model_copy(update={
                    "candidate_id": f"{candidate.candidate_id}:bgy:{geometry_id(self.barangays.revision, part)}",
                    "centerline_geojson": mapping(part),
                    "cross_streets": endpoints,
                    "approximate_length_m": None,
                }))
        return clipped

    def _load(self) -> None:
        if self._loaded or self.error:
            return
        self._loaded = True
        try:
            path = self.directory / "roads.json.gz"
            if path.stat().st_size > MAX_COMPRESSED_BYTES:
                raise ValueError("compressed catalog limit")
            compressed = path.read_bytes()
            if hashlib.sha256(compressed).hexdigest() != self.digest:
                raise ValueError("catalog checksum mismatch")
            with gzip.open(path, "rb") as stream:
                raw = stream.read(MAX_CATALOG_BYTES + 1)
            if len(raw) > MAX_CATALOG_BYTES:
                raise ValueError("expanded catalog limit")
            catalog = RoadCatalog.model_validate_json(raw)
            if catalog.format_version != 1 or catalog.snapshot_at.tzinfo is None:
                raise ValueError("catalog version or clock")
            boundaries, cities = {}, {}
            for city in catalog.cities:
                key = city_key(city.name)
                boundary = shape(city.boundary)
                if key not in NCR_CITIES or key in cities or boundary.geom_type not in {"Polygon", "MultiPolygon"} or boundary.is_empty or not boundary.is_valid:
                    raise ValueError("invalid city boundary identity")
                west, south, east, north = boundary.bounds
                if not (120 <= west < east <= 123 and 13 <= south < north <= 16):
                    raise ValueError("city outside Metro Manila region")
                cities[key], boundaries[key] = city, boundary
            node_positions: dict[int, tuple[float, float]] = {}
            ids: set[int] = set()
            ways = []
            for item in catalog.ways:
                if item.osm_id in ids:
                    raise ValueError("duplicate OSM way")
                ids.add(item.osm_id)
                for node, lon, lat in item.nodes:
                    if node <= 0 or not (120 <= lon <= 123 and 13 <= lat <= 16):
                        raise ValueError("invalid OSM node")
                    if node in node_positions and node_positions[node] != (lon, lat):
                        raise ValueError("conflicting OSM node coordinates")
                    node_positions[node] = (lon, lat)
                ways.append(OSMRoadWay(item.osm_id, item.name, tuple(item.nodes), road_aliases(item),
                                       item.bridge, item.tunnel, item.layer))
            self.catalog, self.ways, self.cities, self.boundaries = catalog, tuple(ways), cities, boundaries
            for item in catalog.incomplete_ways:
                if item.osm_id in ids:
                    raise ValueError("duplicate incomplete OSM way")
                ids.add(item.osm_id)
            for way in self.ways:
                for name in (way.name,*way.aliases):
                    normalized = normalize_name(name)
                    keys = [normalized]
                    words = normalized.split()
                    if words and words[-1] in ROAD_SUFFIXES:
                        keys.append(" ".join(words[:-1]))
                    for name_key in keys:
                        self._name_index.setdefault(name_key,{})[way.osm_id] = way
        except (OSError, ValueError, KeyError, TypeError, EOFError, ShapelyError):
            self.error = "invalid_or_incomplete_osm_catalog"

    def resolve(self, claim: ExtractedClaim) -> RoadPlacementEvidence:
        self._load()
        if self.error or self.catalog is None:
            return RoadPlacementEvidence(status="source_unavailable", reason=self.error or "osm_catalog_unavailable",
                                         catalog_sha256=self.digest)
        key = city_key(claim.canonical_city or "")
        metadata = dict(source_id=self.catalog.source_id, snapshot_at=self.catalog.snapshot_at,
                        catalog_sha256=self.digest, osm_sha256=self.catalog.osm_sha256)
        if key not in self.cities:
            return RoadPlacementEvidence(status="unresolved", reason="reported_city_not_covered", **metadata)
        metadata["city_relation_id"] = self.cities[key].relation_id
        if not claim.canonical_road:
            return RoadPlacementEvidence(status="unresolved", reason="no_reported_road", **metadata)
        names = [claim.canonical_road, *(_span_cross_streets(claim.road_segment_raw) or ())]
        local_clue = " ".join(filter(None, (claim.road_segment_raw, claim.local_area_raw)))
        if any(_way_matches(OSMRoadWay(w.osm_id,w.name,(),road_aliases(w)), name)
               for w in self.catalog.incomplete_ways for name in names) or any(
                   _contains_name(local_clue, name) for w in self.catalog.incomplete_ways
                   for name in (w.name, *road_aliases(w)) if local_clue):
            return RoadPlacementEvidence(status="unresolved", reason="incomplete_named_road_coverage", **metadata)
        barangay_boundary = None
        if claim.canonical_barangay:
            metadata.update(barangay_boundary_status="unavailable", barangay_catalog_sha256=self.barangays.digest)
            barangay_boundary = self.barangay_boundary(claim)
            if barangay_boundary is None:
                return RoadPlacementEvidence(status="unresolved",
                    reason=self.barangays.resolution_reason(claim.canonical_city or "", claim.canonical_barangay,
                        self.boundaries[key]) or "missing_valid_barangay_boundary", **metadata)
            catalog = self.barangays.catalog
            record = self.barangays.records[(key, normalize_name(claim.canonical_barangay))][0]
            metadata.update(barangay_boundary_status="available", barangay_source_id=catalog.source_id,
                            barangay_psgc_code=record.psgc_code, barangay_osm_relation_id=record.osm_relation_id,
                            barangay_source_url=record.source_url, barangay_source_classification=catalog.source_classification)
        boundary = self.boundaries[key]
        explicit_span = _span_cross_streets(claim.road_segment_raw)
        if claim.road_segment_raw and explicit_span is None and re.search(
                r"\b(?:between|from)\b", claim.road_segment_raw, re.I):
            return RoadPlacementEvidence(status="unresolved", reason="missing_explicit_bounded_span", **metadata)
        if explicit_span is not None:
            selected: dict[int, OSMRoadWay] = {}
            for name in names:
                selected.update(self._name_index.get(normalize_name(name),{}))
            match = match_article_road_span(claim, selected.values(), boundary, self.catalog.source_id,
                barangay_boundary=barangay_boundary, allow_partial_barangay=True)
            if match.status != "bounded_candidate":
                return RoadPlacementEvidence(status="unresolved", reason=match.reason, **metadata)
            candidate = RoadPlacementCandidate(candidate_id=f"osm-span:{match.junction_ids[0]}:{match.junction_ids[1]}",
                kind="reported_span", centerline_geojson=match.centerline_geojson, osm_way_ids=list(match.osm_way_ids),
                cross_streets=[[name] for name in match.cross_streets], approximate_length_m=match.approximate_length_m)
            candidates = self._clip_candidates([candidate], barangay_boundary) if barangay_boundary is not None else [candidate]
            return RoadPlacementEvidence(status="bounded_candidate" if candidates else "unresolved",
                reason=match.reason if candidates else "reported_road_outside_barangay",
                candidates=candidates[:25], total_candidate_count=len(candidates), candidates_truncated=len(candidates)>25, **metadata)
        # A corner/nearby crossing is location evidence, not a supplied span.
        # Use mapped junction-to-junction sections and preserve all alternatives
        # for the existing article/NOAH selector rather than inventing a radius.
        if re.search(r"\b(?:northbound|southbound|eastbound|westbound)\b",
                     " ".join(filter(None, (claim.road_segment_raw, claim.local_area_raw))), re.I):
            return RoadPlacementEvidence(status="unresolved", reason="reported_carriageway_requires_review", **metadata)
        main = self._name_index.get(normalize_name(claim.canonical_road),{})
        nodes = {n[0] for way in main.values() for n in way.nodes}
        related = [w for w in self.ways if w.osm_id in main or any(n[0] in nodes for n in w.nodes)] if nodes else []
        sections = split_named_road_at_intersections(claim.canonical_road, related, boundary, self.catalog.source_id)
        candidates = [RoadPlacementCandidate(candidate_id=s.section_id, kind="road_section",
            centerline_geojson=s.centerline_geojson, osm_way_ids=list(s.osm_way_ids),
            cross_streets=[list(names) for names in s.end_cross_streets], ambiguous_carriageway=s.ambiguous_carriageway)
            for s in sections]
        if barangay_boundary is not None:
            candidates = self._clip_candidates(candidates, barangay_boundary)
        # Disconnected parallel carriageways do not create a graph alternative,
        # but two lines joining the same named crossings still require review.
        endpoint_groups: dict[tuple, list[RoadPlacementCandidate]] = {}
        for candidate in candidates:
            if all(candidate.cross_streets):
                endpoints = tuple(sorted(tuple(sorted(normalize_name(name) for name in end))
                                         for end in candidate.cross_streets))
                endpoint_groups.setdefault(endpoints, []).append(candidate)
        for group in endpoint_groups.values():
            if len(group) > 1:
                for candidate in group:
                    candidate.ambiguous_carriageway = True
        if candidates and (claim.road_segment_raw or claim.local_area_raw):
            scoped_sections = [OSMRoadSection(
                c.candidate_id, claim.canonical_road, c.centerline_geojson, tuple(c.osm_way_ids),
                tuple(tuple(end) for end in c.cross_streets), self.catalog.source_id, c.ambiguous_carriageway)
                for c in candidates]
            context = match_article_road_context(claim, scoped_sections, boundary,
                                                 barangay_boundary=barangay_boundary)
            if context.reason == "local_place_not_grounded":
                return RoadPlacementEvidence(status="unresolved", reason=context.reason, **metadata)
            selected_ids = set(context.candidate_section_ids)
            candidates = [c for c in candidates if c.candidate_id in selected_ids]
        return RoadPlacementEvidence(status="ambiguous" if candidates else "unresolved",
            reason=("article_scoped_road_sections" if candidates and (claim.road_segment_raw or claim.local_area_raw)
                    else "reported_road_extent_unbounded" if candidates else "named_road_sections_not_found"),
            candidates=candidates[:25], total_candidate_count=len(candidates), candidates_truncated=len(candidates)>25, **metadata)


@lru_cache(maxsize=1)
def get_news_road_placement_provider() -> NewsRoadPlacementProvider:
    return NewsRoadPlacementProvider(Path(os.environ.get("LANES_NEWS_OSM_CATALOG_DIR", str(DEFAULT_CATALOG_DIR))))
