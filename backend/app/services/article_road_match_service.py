"""Read-only matching of an article's bounded road claim to OSM centerlines.

This returns candidate evidence only. It never labels geometry as a verified
flood extent and never creates a report, event, or avoidance zone.
"""

from __future__ import annotations

import heapq
import math
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import osmium
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from app.schemas.news_extraction import ExtractedClaim


ROAD_SUFFIXES = {"street", "avenue", "road", "boulevard", "highway", "drive", "lane"}
ALIASES = {"sto": "santo", "sta": "santa", "st": "street", "ave": "avenue",
           "rd": "road", "blvd": "boulevard", "hwy": "highway", "dr": "drive"}


def normalize_name(value: str) -> str:
    folded = "".join(char for char in unicodedata.normalize("NFKD", value.casefold())
                     if not unicodedata.combining(char))
    return " ".join(ALIASES.get(word, word) for word in re.findall(r"[a-z0-9]+", folded))


@dataclass(frozen=True)
class OSMRoadWay:
    osm_id: int
    name: str
    nodes: tuple[tuple[int, float, float], ...]
    aliases: tuple[str, ...] = ()
    bridge: str = ""
    tunnel: str = ""
    layer: str = ""


@dataclass(frozen=True)
class RoadMatch:
    status: str  # bounded_candidate or unresolved
    reason: str
    source_id: str
    reported_road: str
    reported_span: str | None
    cross_streets: tuple[str, str] | None = None
    junction_ids: tuple[int, int] | None = None
    osm_way_ids: tuple[int, ...] = ()
    centerline_geojson: dict | None = None
    approximate_length_m: float | None = None
    grade_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class OSMRoadSection:
    section_id: str
    road_name: str
    centerline_geojson: dict
    osm_way_ids: tuple[int, ...]
    end_cross_streets: tuple[tuple[str, ...], tuple[str, ...]]
    source_id: str
    ambiguous_carriageway: bool = False


class _BoundedRoadReader(osmium.SimpleHandler):
    def __init__(self, bbox: tuple[float, float, float, float]) -> None:
        super().__init__()
        self.bbox = bbox
        self.ways: list[OSMRoadWay] = []

    def way(self, way: osmium.osm.Way) -> None:
        if "highway" not in way.tags or not way.tags.get("name"):
            return
        if any(not node.location.valid() for node in way.nodes):
            return
        nodes = tuple((node.ref, node.lon, node.lat) for node in way.nodes)
        west, south, east, north = self.bbox
        if len(nodes) < 2 or not any(west <= lon <= east and south <= lat <= north for _, lon, lat in nodes):
            return
        aliases = tuple(alias.strip() for alias in way.tags.get("alt_name", "").split(";") if alias.strip())
        self.ways.append(OSMRoadWay(
            osm_id=way.id, name=way.tags["name"], nodes=nodes, aliases=aliases,
            bridge=way.tags.get("bridge", ""), tunnel=way.tags.get("tunnel", ""),
            layer=way.tags.get("layer", ""),
        ))


def load_bounded_osm_roads(osm_pbf: str, bbox: tuple[float, float, float, float]) -> list[OSMRoadWay]:
    """Read named highways from a small Metro Manila box in a local OSM PBF."""
    west, south, east, north = bbox
    if not (120 <= west < east <= 123 and 13 <= south < north <= 16
            and east - west <= 0.15 and north - south <= 0.15):
        raise ValueError("OSM search box must be a bounded Metro Manila area")
    reader = _BoundedRoadReader(bbox)
    reader.apply_file(osm_pbf, locations=True)
    return reader.ways


def _span_cross_streets(span: str | None) -> tuple[str, str] | None:
    if not span:
        return None
    # Keep this deliberately narrow: an unrecognized expression is unresolved.
    pattern = (r"\bbetween\s+(.+?)\s+and\s+(.+?)(?:\s*,|$)|"
               r"\bfrom\s+(.+?)\s+(?:to|up to)\s+(.+?)(?:\s*,|$)")
    match = re.search(pattern, span, re.I)
    if not match:
        return None
    first, second = (match.group(1), match.group(2)) if match.group(1) else (match.group(3), match.group(4))
    first, second = first.strip(" ."), second.strip(" .")
    if not first or not second:
        return None
    # Shared plural suffix: "between Atok and Calamba Streets".
    words = normalize_name(second).split()
    if words and words[-1].removesuffix("s") in ROAD_SUFFIXES:
        suffix = words[-1].removesuffix("s")
        second = re.sub(r"\b(?:Streets|Avenues|Roads|Boulevards)$", suffix, second, flags=re.I)
        if normalize_name(first).split()[-1] not in ROAD_SUFFIXES:
            first += " " + suffix
    if normalize_name(first) == normalize_name(second):
        return None
    return first, second


def _way_matches(way: OSMRoadWay, reported: str) -> bool:
    target = normalize_name(reported)
    for name in (way.name, *way.aliases):
        candidate = normalize_name(name)
        if candidate == target:
            return True
        # A source may omit a road suffix. Match only if the remaining name is exact.
        parts = candidate.split()
        if target.split()[-1] not in ROAD_SUFFIXES and parts[-1] in ROAD_SUFFIXES:
            if " ".join(parts[:-1]) == target:
                return True
    return False


def _shortest_path(graph: dict[int, dict[int, float]], start: int, end: int,
                   excluded: tuple[int, int] | None = None) -> list[int] | None:
    queue = [(0.0, start)]
    distance = {start: 0.0}
    previous: dict[int, int] = {}
    while queue:
        cost, node = heapq.heappop(queue)
        if cost > distance[node] + 1e-8:
            continue
        if node == end:
            path = [end]
            while path[-1] != start:
                path.append(previous[path[-1]])
            return list(reversed(path))
        for neighbor, length in graph[node].items():
            if excluded and {node, neighbor} == set(excluded):
                continue
            candidate = cost + length
            if candidate + 1e-8 < distance.get(neighbor, math.inf):
                distance[neighbor] = candidate
                previous[neighbor] = node
                heapq.heappush(queue, (candidate, neighbor))
    return None


def split_named_road_at_intersections(
    road_name: str,
    ways: Iterable[OSMRoadWay],
    city_boundary: BaseGeometry,
    source_id: str,
) -> list[OSMRoadSection]:
    """Split a named road between mapped cross-street junctions, read-only.

    Only sections with two different mapped cross-street endpoints are returned.
    PBF/way endpoints and arbitrary distance windows never define a section.
    Parallel paths are retained with an ambiguity flag for caller review.
    """
    if not source_id or not road_name or city_boundary.is_empty or not city_boundary.is_valid:
        raise ValueError("Road, OSM source and valid city boundary are required")
    selected = tuple(ways)
    main = [way for way in selected if _way_matches(way, road_name)]
    if not main:
        return []
    main_nodes = {node_id for way in main for node_id, _, _ in way.nodes}
    crossings: dict[int, set[str]] = defaultdict(set)
    for way in selected:
        if _way_matches(way, road_name):
            continue
        for node_id, _, _ in way.nodes:
            if node_id in main_nodes:
                crossings[node_id].add(way.name)
    points = {node_id: (lon, lat) for way in main for node_id, lon, lat in way.nodes}
    graph: dict[int, dict[int, float]] = defaultdict(dict)
    edge_ways: dict[frozenset[int], set[int]] = defaultdict(set)
    edge_grades: dict[frozenset[int], bool] = defaultdict(bool)
    for way in main:
        for left, right in zip(way.nodes, way.nodes[1:]):
            a, b = left[0], right[0]
            if a == b:
                continue
            key = frozenset((a, b))
            graph[a][b] = graph[b][a] = 1.0
            edge_ways[key].add(way.osm_id)
            edge_grades[key] |= any(value and value not in {"no", "0"}
                                    for value in (way.bridge, way.tunnel, way.layer))
    boundary_nodes = set(crossings) | {node for node, neighbors in graph.items() if len(neighbors) != 2}
    used_edges: set[frozenset[int]] = set()
    sections: list[OSMRoadSection] = []
    for start in sorted(boundary_nodes):
        for neighbor in sorted(graph[start]):
            first_edge = frozenset((start, neighbor))
            if first_edge in used_edges:
                continue
            path = [start, neighbor]
            used_edges.add(first_edge)
            while path[-1] not in boundary_nodes:
                next_nodes = [node for node in graph[path[-1]] if node != path[-2]]
                if len(next_nodes) != 1:
                    break
                next_node = next_nodes[0]
                edge = frozenset((path[-1], next_node))
                if edge in used_edges:
                    break
                path.append(next_node)
                used_edges.add(edge)
            end = path[-1]
            if start == end or start not in crossings or end not in crossings:
                continue
            if {normalize_name(name) for name in crossings[start]} & {
                    normalize_name(name) for name in crossings[end]}:
                # Two OSM nodes for the same cross street often describe a
                # dual-carriageway junction, not a useful between-streets span.
                continue
            edges = [frozenset((a, b)) for a, b in zip(path, path[1:])]
            if any(edge_grades[edge] or len(edge_ways[edge]) != 1 for edge in edges):
                continue
            line = LineString([points[node] for node in path])
            if line.is_empty or not city_boundary.covers(line):
                continue
            # A second connected path may be the opposite carriageway.
            alternative = any(_shortest_path(graph, start, end, (a, b)) is not None
                              for a, b in zip(path, path[1:]))
            sections.append(OSMRoadSection(
                section_id=f"osm:{min(start, end)}-{max(start, end)}",
                road_name=road_name,
                centerline_geojson={"type": "LineString", "coordinates": [list(points[node]) for node in path]},
                osm_way_ids=tuple(sorted({way_id for edge in edges for way_id in edge_ways[edge]})),
                end_cross_streets=(tuple(sorted(crossings[start])), tuple(sorted(crossings[end]))),
                source_id=source_id,
                ambiguous_carriageway=alternative,
            ))
    return sections


def match_article_road_span(
    claim: ExtractedClaim,
    ways: Iterable[OSMRoadWay],
    city_boundary: BaseGeometry | None,
    source_id: str,
    barangay_boundary: BaseGeometry | None = None,
) -> RoadMatch:
    """Return one bounded OSM candidate only when source and geometry are unique.

    ``ways`` must come from a bounded, identified OSM extract. The caller must
    provide a checked city polygon; a named barangay also requires its polygon.
    """
    reported_road = claim.canonical_road or claim.raw_place_name
    span = claim.road_segment_raw

    def unresolved(reason: str) -> RoadMatch:
        return RoadMatch("unresolved", reason, source_id, reported_road, span)

    if not source_id or not claim.canonical_city or not reported_road:
        return unresolved("missing_source_city_or_road")
    crossings = _span_cross_streets(span)
    if crossings is None:
        return unresolved("missing_explicit_bounded_span")
    if city_boundary is None or city_boundary.is_empty or not city_boundary.is_valid:
        return unresolved("missing_valid_city_boundary")
    if claim.canonical_barangay and (barangay_boundary is None or barangay_boundary.is_empty or not barangay_boundary.is_valid):
        return unresolved("missing_valid_barangay_boundary")

    selected = tuple(ways)
    main = [way for way in selected if _way_matches(way, reported_road)]
    if not main:
        return unresolved("main_road_not_found")
    main_nodes = {node_id for way in main for node_id, _, _ in way.nodes}
    junctions: list[int] = []
    for crossing in crossings:
        cross = [way for way in selected if _way_matches(way, crossing)]
        shared = {node_id for way in cross for node_id, _, _ in way.nodes if node_id in main_nodes}
        if len(shared) != 1:
            return unresolved("missing_or_ambiguous_cross_street_junction")
        junctions.append(next(iter(shared)))
    start, end = junctions
    if start == end:
        return unresolved("cross_streets_share_one_junction")

    points: dict[int, tuple[float, float]] = {}
    graph: dict[int, dict[int, float]] = defaultdict(dict)
    edge_ways: dict[frozenset[int], list[OSMRoadWay]] = defaultdict(list)
    for way in main:
        for node_id, lon, lat in way.nodes:
            points[node_id] = lon, lat
        for left, right in zip(way.nodes, way.nodes[1:]):
            a, b = left[0], right[0]
            if a == b:
                continue
            mean_lat = (left[2] + right[2]) / 2
            length = math.hypot((left[1] - right[1]) * 111_320 * math.cos(math.radians(mean_lat)),
                                (left[2] - right[2]) * 110_574)
            if length <= 0:
                continue
            graph[a][b] = graph[b][a] = length
            edge_ways[frozenset((a, b))].append(way)
    path = _shortest_path(graph, start, end)
    if path is None:
        return unresolved("disconnected_named_road")
    # A second path, even a longer one, may be another carriageway. Fail closed.
    for a, b in zip(path, path[1:]):
        if _shortest_path(graph, start, end, (a, b)) is not None:
            return unresolved("multiple_named_road_paths")
    path_ways = [way for a, b in zip(path, path[1:]) for way in edge_ways[frozenset((a, b))]]
    if any(len(edge_ways[frozenset((a, b))]) != 1 for a, b in zip(path, path[1:])):
        return unresolved("overlapping_osm_ways")
    coords = [points[node] for node in path]
    line = LineString(coords)
    if not city_boundary.covers(line):
        return unresolved("outside_reported_city")
    if barangay_boundary is not None and not barangay_boundary.covers(line):
        return unresolved("outside_reported_barangay")
    grade_flags = sorted({f"{tag}={value}" for way in path_ways
                          for tag, value in (("bridge", way.bridge), ("tunnel", way.tunnel), ("layer", way.layer))
                          if value and value not in {"no", "0"}})
    if grade_flags:
        return unresolved("grade_separation_requires_review")
    approximate_length_m = sum(graph[a][b] for a, b in zip(path, path[1:]))
    return RoadMatch(
        status="bounded_candidate", reason="unique_osm_centerline_candidate",
        source_id=source_id, reported_road=reported_road, reported_span=span,
        cross_streets=crossings, junction_ids=(start, end),
        osm_way_ids=tuple(sorted({way.osm_id for way in path_ways})),
        centerline_geojson={"type": "LineString", "coordinates": [list(point) for point in coords]},
        approximate_length_m=round(approximate_length_m, 1), grade_flags=tuple(grade_flags),
    )
