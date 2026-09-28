"""Read-only article road-span check against local OSM and NOAH source vectors.

This research command never writes a map zone. A unique pair of OSM junctions
and a short named-road path are candidate geometry, not a verified flood extent.
"""

from __future__ import annotations

import argparse
import heapq
import math
import re
import sys
import unicodedata
from xml.etree import ElementTree
from collections import defaultdict
from pathlib import Path

import httpx
import osmium
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize, transform, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_noah_road_intersections import RoadWay, hazard_overlap, local_projector

MAX_BOUNDARY_XML_BYTES = 1_000_000


def normalize_road_name(value: str) -> str:
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )
    words = re.findall(r"[a-z0-9]+", folded)
    aliases = {"sto": "santo", "sta": "santa", "st": "street", "sts": "street",
               "ave": "avenue", "aves": "avenue", "rd": "road", "rds": "road",
               "blvd": "boulevard", "hwy": "highway"}
    return " ".join(aliases.get(word, word) for word in words)


def cross_streets_from_span(span: str) -> tuple[str, str]:
    """Accept only a bounded 'between A and B Streets' style span."""
    match = re.fullmatch(
        r"\s*between\s+([A-Za-zÀ-ÿ0-9. -]+?)\s+and\s+"
        r"([A-Za-zÀ-ÿ0-9. -]+?)\s+(Streets?|Avenues?|Roads?|Boulevards?)\s*",
        span, re.I,
    )
    if not match:
        raise ValueError("Article span is not a supported between-two-cross-streets phrase")
    suffix = match.group(3).removesuffix("s")
    first, second = match.group(1).strip(), match.group(2).strip()
    if not re.search(r"\b(?:Street|Avenue|Road|Boulevard|St\.|Ave\.|Rd\.)$", first, re.I):
        first += " " + suffix
    if not re.search(r"\b(?:Street|Avenue|Road|Boulevard|St\.|Ave\.|Rd\.)$", second, re.I):
        second += " " + suffix
    if normalize_road_name(first) == normalize_road_name(second):
        raise ValueError("Article span names the same cross street twice")
    return first, second


class SpanRoads(osmium.SimpleHandler):
    def __init__(self, names: tuple[str, str, str], bbox: tuple[float, float, float, float]) -> None:
        super().__init__()
        self.names = {normalize_road_name(name) for name in names}
        self.bbox = bbox
        self.ways: dict[str, list[RoadWay]] = defaultdict(list)

    def way(self, way: osmium.osm.Way) -> None:
        name = way.tags.get("name", "")
        key = normalize_road_name(name)
        if key not in self.names or "highway" not in way.tags:
            return
        if any(not node.location.valid() for node in way.nodes):
            return
        nodes = tuple((node.ref, node.lon, node.lat) for node in way.nodes)
        west, south, east, north = self.bbox
        if len(nodes) < 2 or not any(west <= lon <= east and south <= lat <= north for _, lon, lat in nodes):
            return
        self.ways[key].append(RoadWay(
            way.id, name, nodes, way.tags.get("highway", ""),
            way.tags.get("bridge", ""), way.tags.get("tunnel", ""), way.tags.get("layer", ""),
        ))


def unique_junction(main: list[RoadWay], cross: list[RoadWay], label: str) -> int:
    main_nodes = {node_id for way in main for node_id, _, _ in way.nodes}
    shared = {node_id for way in cross for node_id, _, _ in way.nodes if node_id in main_nodes}
    if len(shared) != 1:
        raise ValueError(f"{label}: expected one shared OSM junction, found {len(shared)}")
    return shared.pop()


def shortest_named_road_path(main: list[RoadWay], start: int, end: int) -> tuple[list[tuple[float, float]], set[int], set[str]]:
    """Return one bounded centerline path; reject equal-length alternatives."""
    projection = local_projector()
    points = {node_id: (lon, lat) for way in main for node_id, lon, lat in way.nodes}
    adjacency: dict[int, dict[int, tuple[float, int, RoadWay]]] = defaultdict(dict)
    for way in main:
        for left, right in zip(way.nodes, way.nodes[1:]):
            x1, y1 = projection(left[1], left[2])
            x2, y2 = projection(right[1], right[2])
            distance = math.hypot(x2 - x1, y2 - y1)
            if distance <= 0:
                continue
            for a, b in ((left[0], right[0]), (right[0], left[0])):
                existing = adjacency[a].get(b)
                if existing is None or distance < existing[0]:
                    adjacency[a][b] = (distance, way.osm_id, way)
    queue = [(0.0, start)]
    distances = {start: 0.0}
    path_counts = {start: 1}
    previous: dict[int, tuple[int, int, RoadWay]] = {}
    while queue:
        distance, node = heapq.heappop(queue)
        if distance > distances[node] + 1e-6:
            continue
        for neighbor, (edge_length, way_id, way) in adjacency[node].items():
            candidate = distance + edge_length
            if candidate + 1e-6 < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                path_counts[neighbor] = path_counts[node]
                previous[neighbor] = (node, way_id, way)
                heapq.heappush(queue, (candidate, neighbor))
            elif abs(candidate - distances.get(neighbor, math.inf)) <= 1e-6:
                path_counts[neighbor] = min(2, path_counts.get(neighbor, 0) + path_counts[node])
    if end not in distances:
        raise ValueError("No connected named-road path between the cross streets")
    if path_counts[end] != 1:
        raise ValueError("Multiple equally short named-road paths connect the cross streets")
    node_path = [end]
    way_ids: set[int] = set()
    grade_flags: set[str] = set()
    while node_path[-1] != start:
        prior, way_id, way = previous[node_path[-1]]
        way_ids.add(way_id)
        for name, value in (("bridge", way.bridge), ("tunnel", way.tunnel), ("layer", way.layer)):
            if value and value not in {"no", "0"}:
                grade_flags.add(f"{name}={value}")
        node_path.append(prior)
    return [points[node_id] for node_id in reversed(node_path)], way_ids, grade_flags


def city_boundary_from_osm_xml(content: bytes, relation_id: int, city_name: str) -> BaseGeometry:
    """Assemble a complete administrative relation; reject missing source members."""
    if len(content) > MAX_BOUNDARY_XML_BYTES or b"<!doctype" in content.lower() or b"<!entity" in content.lower():
        raise ValueError("OSM boundary response is oversized or contains forbidden XML declarations")
    root = ElementTree.fromstring(content)
    relation = next((item for item in root.findall("relation") if item.get("id") == str(relation_id)), None)
    if relation is None:
        raise ValueError("Expected OSM city relation is missing")
    tags = {tag.get("k"): tag.get("v") for tag in relation.findall("tag")}
    if (tags.get("boundary") != "administrative" or tags.get("admin_level") != "6" or
            normalize_road_name(tags.get("name") or "") != normalize_road_name(city_name)):
        raise ValueError("OSM relation does not match the reported city and administrative level")
    nodes = {
        node.get("id"): (float(node.get("lon")), float(node.get("lat")))
        for node in root.findall("node")
    }
    ways = {way.get("id"): [node.get("ref") for node in way.findall("nd")] for way in root.findall("way")}
    outlines: dict[str, list[LineString]] = {"outer": [], "inner": []}
    for member in relation.findall("member"):
        role = member.get("role")
        if member.get("type") != "way" or role not in outlines:
            continue
        node_ids = ways.get(member.get("ref"))
        if not node_ids or len(node_ids) < 2 or any(node_id not in nodes for node_id in node_ids):
            raise ValueError("OSM city relation has an incomplete boundary way")
        outlines[role].append(LineString([nodes[node_id] for node_id in node_ids]))
    if not outlines["outer"]:
        raise ValueError("OSM city relation has no outer boundary")
    outer_polygons = list(polygonize(unary_union(outlines["outer"])))
    if not outer_polygons:
        raise ValueError("OSM city outer boundary does not form a polygon")
    boundary = unary_union(outer_polygons)
    if outlines["inner"]:
        inner_polygons = list(polygonize(unary_union(outlines["inner"])))
        if not inner_polygons:
            raise ValueError("OSM city inner boundary does not form a polygon")
        boundary = boundary.difference(unary_union(inner_polygons))
    if boundary.is_empty or not boundary.is_valid:
        raise ValueError("OSM city boundary is empty or invalid")
    return boundary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("osm_pbf", type=Path)
    parser.add_argument("noah_zips", type=Path, nargs=3)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--city-name", required=True, help="Reported city to verify against its OSM administrative relation")
    parser.add_argument("--city-relation-id", type=int, required=True)
    parser.add_argument("--road", required=True, help="Road name as written in the article")
    parser.add_argument("--span", required=True, help="Explicit between-two-cross-streets phrase")
    parser.add_argument("--bbox", type=float, nargs=4, metavar=("WEST", "SOUTH", "EAST", "NORTH"), required=True)
    args = parser.parse_args()
    bbox = tuple(args.bbox)
    if not (120 <= bbox[0] < bbox[2] <= 123 and 13 <= bbox[1] < bbox[3] <= 16
            and bbox[2] - bbox[0] <= 0.15 and bbox[3] - bbox[1] <= 0.15):
        raise ValueError("Audit bbox must be a bounded Metro Manila area")
    cross_a, cross_b = cross_streets_from_span(args.span)
    main_key = normalize_road_name(args.road)
    roads = SpanRoads((args.road, cross_a, cross_b), bbox)
    roads.apply_file(str(args.osm_pbf), locations=True)
    main_ways = roads.ways[main_key]
    if not main_ways:
        raise ValueError("Named main road not found in the audit area")
    start = unique_junction(main_ways, roads.ways[normalize_road_name(cross_a)], cross_a)
    end = unique_junction(main_ways, roads.ways[normalize_road_name(cross_b)], cross_b)
    coordinates, way_ids, grade_flags = shortest_named_road_path(main_ways, start, end)
    city_url = f"https://api.openstreetmap.org/api/0.6/relation/{args.city_relation_id}/full"
    with httpx.Client(trust_env=False, timeout=20) as client:
        with client.stream("GET", city_url, headers={
            "User-Agent": "LANES-Phase36-readonly-audit/0.1 (+https://github.com/pu-roi/LANES)",
        }) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_bytes():
                content.extend(chunk)
                if len(content) > MAX_BOUNDARY_XML_BYTES:
                    raise ValueError("OSM city boundary response exceeds size limit")
    boundary = city_boundary_from_osm_xml(bytes(content), args.city_relation_id, args.city_name)
    if not boundary.covers(LineString(coordinates)):
        raise ValueError("Candidate road path is outside the reported OSM city boundary")
    line = transform(local_projector(), LineString(coordinates))
    print(f"Source: {args.source_url}")
    print(f"Article road/span: {args.road} {args.span}")
    print(f"OSM path: {line.length:.1f} m; junction nodes {start} to {end}; ways {sorted(way_ids)}")
    print(f"OSM centerline (lon, lat): {coordinates}")
    print(f"OSM city relation: {args.city_name} ({args.city_relation_id}); candidate path contained")
    print(f"Grade flags: {sorted(grade_flags) if grade_flags else 'none mapped on path'}")
    for zip_path in args.noah_zips:
        lengths = hazard_overlap(zip_path, line)
        print(f"NOAH {zip_path.name}: " + ", ".join(
            f"Var {hazard_class}={length:.1f} m" for hazard_class, length in sorted(lengths.items())
        ))
    print("Status: research candidate only; no current-flood or routing verification")


if __name__ == "__main__":
    main()
