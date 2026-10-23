"""Opt-in road-network/NOAH estimates, independent of administrative clipping.

The source establishes flood facts, OSM establishes a physical connected road,
and NOAH supplies modeled susceptible fragments. None proves measured extent.
Existing source-normalization and legacy placement contracts are unchanged.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

from shapely import set_srid, union_all
from shapely.affinity import scale
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import linemerge

from app.crud.news_publication import NewsPublicationError
from app.services.article_road_match_service import normalize_name
from app.services.news_ner_durable.contracts import sha
from app.services.noah_vector_catalog_service import NoahVectorCatalog, X_METRES, Y_METRES, metric_geometry, tile_keys
from app.services.operational_footprint_service import validate_operational_shape
from app.services.placement_geometry_service import LINE_PRECISION_METRES, line_parts, source_aligned_line_union

VERSION = 'connected-road-noah-v1'
MAX_WAYS = 1000
MAX_SOURCE_VERTICES = 10000
MAX_COMPONENTS = 25
SNAP_METRES = 50.0  # Candidate identity only; never a geometry radius.
SNAP_TIE_METRES = 1.0
MARGIN_METRES = 25.0


def require(ok: bool, code: str) -> None:
    if not ok:
        raise NewsPublicationError(code)


def road_name(value: str) -> str:
    words = normalize_name(value).split()
    aliases = {'ave': 'avenue', 'extn': 'extension', 'ext': 'extension', 'blvd': 'boulevard',
               'st': 'street', 'rd': 'road', 'hwy': 'highway'}
    return ' '.join(aliases.get(w, w) for w in words)


def way_line(way: dict) -> LineString:
    return LineString([(n[1], n[2]) for n in way['nodes']])


def components(ways: dict[int, dict]) -> list[set[int]]:
    nodes: dict[int, set[int]] = defaultdict(set)
    for identity, way in ways.items():
        for node in way['nodes']:
            nodes[node[0]].add(identity)
    remaining = set(ways)
    found = []
    while remaining:
        todo = deque([min(remaining)])
        current = set()
        while todo:
            identity = todo.popleft()
            if identity in current:
                continue
            current.add(identity)
            for node in ways[identity]['nodes']:
                todo.extend(nodes[node[0]] - current)
        remaining -= current
        found.append(current)
    return found


@dataclass(frozen=True)
class ConnectedRoadZone:
    geometry: dict
    evidence: dict
    checksum: str


class ConnectedRoadService:
    def __init__(self, roads_directory: Path, noah_directory: Path, *,
                 feature_path: Path | None = None, feature_sha256: str | None = None) -> None:
        path = roads_directory / 'roads.json.gz'
        require(path.stat().st_size <= 16 * 1024 * 1024, 'connected_road_catalog_size_limit')
        with gzip.open(path, 'rb') as stream:
            expanded = stream.read(96 * 1024 * 1024 + 1)
        require(len(expanded) <= 96 * 1024 * 1024, 'connected_road_catalog_size_limit')
        manifest = json.loads((roads_directory / 'manifest.json').read_text(encoding='utf-8'))
        self.catalog_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        require(self.catalog_sha256 == manifest['catalog_sha256'], 'connected_road_catalog_changed')
        self.catalog = json.loads(expanded)
        self.ways = {w['osm_id']: w for w in self.catalog['ways']}
        require(len(self.ways) == len(self.catalog['ways']), 'connected_road_duplicate_way')
        self.noah = NoahVectorCatalog(noah_directory)
        self.features = None
        if feature_path is not None:
            raw = feature_path.read_bytes()
            require(len(raw) <= 2_000_000 and hashlib.sha256(raw).hexdigest() == feature_sha256,
                    'connected_road_feature_asset_changed')
            self.features = json.loads(raw)
            require(self.features.get('schema_version') == 'connected-road-reviewed-features-v1'
                and self.features['osm_catalog_sha256'] == self.catalog_sha256,
                'connected_road_feature_catalog_mismatch')
        self.feature_sha256 = feature_sha256

    @property
    def identity(self) -> dict:
        return {'policy': VERSION, 'osm_catalog_sha256': self.catalog_sha256,
                'osm_source_id': self.catalog['source_id'], 'osm_snapshot_at': self.catalog['snapshot_at'],
                'osm_source_sha256': self.catalog['osm_sha256'],
                'noah_catalog_sha256': self.noah.revision, 'feature_asset_sha256': self.feature_sha256}

    def _named_network(self, name: str, city: str, hint: list[float] | None) -> tuple[list[dict], dict]:
        key = road_name(name)
        require(bool(key), 'connected_road_name_missing')
        require(not any(key in {road_name(n) for n in (w['name'], *w.get('aliases', []))}
                        for w in self.catalog.get('incomplete_ways', [])), 'connected_road_incomplete_coverage')
        matches = {i: w for i, w in self.ways.items()
                   if key in {road_name(n) for n in (w['name'], *w.get('aliases', []))}}
        require(bool(matches), 'connected_road_name_unmatched')
        city_name = re.sub(r'^(?:city of )|(?: city)$', '', normalize_name(city))
        cities = [shape(c['boundary']) for c in self.catalog['cities']
                  if re.sub(r'^(?:city of )|(?: city)$', '', normalize_name(c['name'])) == city_name]
        require(len(cities) == 1, 'connected_road_city_identity_unresolved')
        networks = components(matches)
        # City context selects a candidate, never clips the connected network.
        networks = [ids for ids in networks if any(cities[0].intersects(way_line(matches[i])) for i in ids)]
        if hint is not None:
            require(len(hint) == 2 and all(math.isfinite(x) for x in hint)
                    and -90 <= hint[0] <= 90 and -180 <= hint[1] <= 180, 'connected_road_hint_invalid')
            point = metric_geometry(Point(hint[1], hint[0]))
            distances = sorted((min(metric_geometry(way_line(matches[i])).distance(point) for i in ids), min(ids), ids)
                               for ids in networks)
            require(bool(distances) and distances[0][0] <= SNAP_METRES, 'connected_road_hint_not_on_reported_road')
            require(len(distances) == 1 or distances[1][0] - distances[0][0] > SNAP_TIE_METRES,
                    'connected_road_hint_ambiguous')
            selected = distances[0][2]
            evidence = {'origin': 'user_supplied', 'latitude_longitude': hint,
                        'distance_to_network_metres': distances[0][0], 'establishes_geometry': False}
        else:
            require(len(networks) == 1, 'connected_road_disconnected_identity_ambiguous')
            selected, evidence = networks[0], {'origin': 'source_road_and_city', 'establishes_geometry': False}
        ways = [matches[i] for i in sorted(selected)]
        for way in ways:
            require(way.get('bridge', '') in ('', 'no') and way.get('layer', '') in ('', '0')
                    and way.get('tunnel', '') in ('', 'no'), 'connected_road_grade_unresolved')
        return ways, {'selection': 'connected_named_road', 'location_hint': evidence}

    def _verified_loop(self, ways: list[dict], degree: dict[int, int]) -> dict:
        """Accept one source-tagged directed loop, never pick one of its arms."""
        require(self.features is not None, 'connected_road_network_branch_unresolved')
        ids = {w['osm_id'] for w in ways}
        reviews = [r for r in self.features.get('named_network_reviews', [])
                   if set(r['way_ids']) == ids]
        require(len(reviews) == 1, 'connected_road_network_branch_unresolved')
        review = reviews[0]
        require(sha(ways) == review['network_sha256'], 'connected_road_network_review_changed')
        # Peel leaf chains; the remainder must be a single simple cycle.
        graph = defaultdict(set)
        for w in ways:
            for a, b in zip(w['nodes'], w['nodes'][1:]):
                graph[a[0]].add(b[0]); graph[b[0]].add(a[0])
        alive = set(graph)
        todo = deque(n for n, ns in graph.items() if len(ns) == 1)
        while todo:
            n = todo.popleft()
            if n not in alive:
                continue
            alive.remove(n)
            for neighbor in graph[n] & alive:
                if len(graph[neighbor] & alive) == 1:
                    todo.append(neighbor)
        require(alive and all(len(graph[n] & alive) == 2 for n in alive)
            and len([n for n in degree if degree[n] == 3]) == 2
            and max(degree.values()) == 3, 'connected_road_loop_topology_unresolved')
        incoming, outgoing = defaultdict(int), defaultdict(int)
        cycle_ways = []
        for w in ways:
            cyclic = [(a,b) for a,b in zip(w['nodes'],w['nodes'][1:]) if a[0] in alive and b[0] in alive]
            if not cyclic:
                continue
            tags = review['way_tags'].get(str(w['osm_id']), {})
            require(tags.get('oneway') == 'yes' and road_name(tags.get('name', '')) == road_name(w['name'])
                and tags.get('highway') in ('primary','secondary','tertiary','residential'),
                'connected_road_loop_direction_unverified')
            cycle_ways.append(w['osm_id'])
            for a,b in cyclic:
                outgoing[a[0]] += 1; incoming[b[0]] += 1
        require(all(incoming[n] == outgoing[n] == 1 for n in alive),
                'connected_road_loop_direction_unverified')
        return {'kind': 'source_tagged_oneway_loop', 'cycle_way_ids': sorted(cycle_ways),
                'network_review_sha256': sha(review), 'branches_retained': True}

    def _feature_network(self, section: str, city: str, hint: list[float] | None) -> tuple[list[dict], dict]:
        require(self.features is not None, 'connected_road_feature_asset_missing')
        features = [f for f in self.features['features'] if road_name(f['reported_section']) == road_name(section)
                    and normalize_name(f['city']) == normalize_name(city)]
        require(len(features) == 1, 'connected_road_feature_identity_ambiguous')
        feature = features[0]
        require(feature['feature_kind'] == 'underloop' and bool(feature['source_pbf_sha256'])
                and len(feature['source_pbf_sha256']) == 64, 'connected_road_feature_provenance_invalid')
        ways = feature['ways']
        lookup = {w['osm_id']: w for w in ways}
        require(len(lookup) == len(ways) and len(components(lookup)) == 1,
                'connected_road_feature_disconnected')
        require(hint is not None, 'connected_road_feature_hint_required')
        require(len(hint) == 2 and all(math.isfinite(x) for x in hint)
                and -90 <= hint[0] <= 90 and -180 <= hint[1] <= 180, 'connected_road_hint_invalid')
        point = metric_geometry(Point(hint[1], hint[0]))
        distance = min(metric_geometry(way_line(w)).distance(point) for w in ways)
        require(distance <= SNAP_METRES, 'connected_road_feature_hint_remote')
        bridges = [self.ways.get(i) for i in feature['overhead_way_ids']]
        require(bridges and all(w and w.get('bridge') == 'yes' and w.get('layer') == '1'
                and 'marcos' in road_name(w['name']) for w in bridges), 'connected_road_overhead_identity_changed')
        overhead = union_all([way_line(w) for w in bridges])
        overhead_nodes = {n[0] for w in bridges for n in w['nodes']}
        crossing = []
        for way in ways:
            tags = way['tags']
            require(tags.get('highway') == 'primary_link' and tags.get('access') == 'yes'
                and tags.get('destination:street') == 'C-5' and tags.get('bridge', '') in ('', 'no')
                and tags.get('layer', '') in ('', '0') and tags.get('tunnel', '') in ('', 'building_passage'),
                'connected_road_underloop_grade_or_access_changed')
            require(not overhead_nodes.intersection(n[0] for n in way['nodes']), 'connected_road_underloop_not_grade_separated')
            if way_line(way).intersects(overhead):
                crossing.append(way['osm_id'])
        require(bool(crossing) and any(w['tags'].get('tunnel') == 'building_passage' for w in ways),
                'connected_road_underloop_crossing_unproved')
        ends = defaultdict(int)
        for w in ways:
            ends[w['nodes'][0][0]] += 1
            ends[w['nodes'][-1][0]] += 1
        require(max(ends.values()) <= 2, 'connected_road_underloop_branch_ambiguous')
        endpoints = sorted(n for n, degree in ends.items() if degree == 1)
        require(endpoints == sorted(feature['junction_bounds']) and len(endpoints) == 2,
                'connected_road_underloop_bounds_changed')
        for endpoint in endpoints:
            incident = feature['junction_evidence'].get(str(endpoint), [])
            require(len({w['osm_id'] for w in incident}) >= 2
                    and all(endpoint in (w.get('node_ids') or [n[0] for n in w['nodes']]) for w in incident),
                    'connected_road_underloop_junction_unverified')
        return ways, {'selection': 'reviewed_physical_underloop', 'feature_asset_sha256': self.feature_sha256,
            'source_pbf_sha256': feature['source_pbf_sha256'], 'overhead_way_ids': feature['overhead_way_ids'],
            'grade_separated_crossing_way_ids': crossing, 'junction_bounds': endpoints,
            'location_hint': {'origin': 'user_supplied', 'latitude_longitude': hint,
                             'distance_to_network_metres': distance, 'establishes_geometry': False}}

    def build(self, claim: object, *, hint: list[float] | None = None) -> ConnectedRoadZone:
        section = claim.road_segment_raw or ''
        physical = bool(re.search(r'\b(?:underloop|underpass)\b', section, re.I))
        if physical:
            ways, selected = self._feature_network(section, claim.canonical_city or '', hint)
        else:
            # Explicit physical spans require their own authenticated bounded
            # adapter; do not silently expand them into the full named road.
            require(not re.search(r'\b(?:between|from|corner|intersection|frontage|service road)\b', section, re.I),
                    'connected_road_explicit_section_adapter_required')
            ways, selected = self._named_network(claim.canonical_road or claim.raw_place_name, claim.canonical_city or '', hint)
        require(1 <= len(ways) <= MAX_WAYS and sum(len(w['nodes']) for w in ways) <= MAX_SOURCE_VERTICES,
                'connected_road_source_limit')
        lines = [way_line(w) for w in ways]
        require(all(l.is_valid and l.is_simple and not l.is_empty for l in lines), 'connected_road_invalid_source_line')
        core_source = union_all(lines)
        merged = linemerge(core_source) if core_source.geom_type != 'LineString' else core_source
        # Unresolved same-road branches cannot be silently removed by ranking.
        degree = defaultdict(int)
        segments = set()
        for way in ways:
            for a, b in zip(way['nodes'], way['nodes'][1:]):
                edge = tuple(sorted((a[0], b[0])))
                if edge not in segments:
                    degree[a[0]] += 1; degree[b[0]] += 1; segments.add(edge)
        if max(degree.values()) > 2:
            selected['network_topology'] = self._verified_loop(ways, degree)
        else:
            require(merged.geom_type == 'LineString', 'connected_road_source_not_single_path')
        pieces, scenario_evidence = [], []
        for way in ways:
            line = way_line(way)
            intersections = self.noah.intersections(line)
            fragments = []
            for period, classes in intersections.items():
                for hazard, geometry in classes.items():
                    for part in line_parts(geometry):
                        require(len(scenario_evidence) < 512, 'connected_road_noah_fragment_limit')
                        fragments.append(part)
                        scenario_evidence.append({'osm_way_id': way['osm_id'], 'return_period': period,
                            'hazard_class': hazard, 'noah_source_id': self.noah.manifest.scenarios[period].source_id,
                            'centerline': mapping(part)})
            if fragments:
                pieces.extend(line_parts(source_aligned_line_union(line, fragments)))
        require(bool(pieces), 'connected_road_no_modeled_overlap')
        if merged.geom_type == 'LineString':
            wet = source_aligned_line_union(merged, pieces)
        else:
            # Each fragment has already been reconstructed along its own exact
            # source way. A reviewed road loop retains both directed arms.
            wet = union_all(pieces)
        wet_parts = line_parts(wet)
        require(1 <= len(wet_parts) <= MAX_COMPONENTS, 'connected_road_component_limit')
        source_metric = metric_geometry(merged)
        require(all(source_metric.buffer(LINE_PRECISION_METRES).covers(metric_geometry(p)) for p in wet_parts),
                'connected_road_fragment_outside_source')
        # Group only fragments touching on source linework. Keep the 25-m
        # margin, but intersect it with the actual modeled envelope: a margin
        # must never fill a modeled dry hole or bridge a dry road interval.
        groups: list[list] = []
        remaining = set(range(len(wet_parts)))
        while remaining:
            ids = {remaining.pop()}
            changed = True
            while changed:
                adjacent = {j for j in remaining if any(wet_parts[j].intersects(wet_parts[i]) for i in ids)}
                changed = bool(adjacent); ids |= adjacent; remaining -= adjacent
            groups.append([wet_parts[i] for i in sorted(ids)])
        polygons = [scale(metric_geometry(union_all(g)).buffer(MARGIN_METRES), xfact=1 / X_METRES,
            yfact=1 / Y_METRES, origin=(0, 0)) for g in groups]
        buffered = union_all(polygons)
        keys = tile_keys(buffered.bounds, self.noah.manifest.tile_size)
        require(len(keys) <= 128, 'connected_road_noah_query_limit')
        envelope = union_all([g for period in (5,25,100) for key in keys
                              for g in self.noah._tile(period, key).values()])
        intersection = buffered.intersection(envelope)
        require(intersection.geom_type in ('Polygon', 'MultiPolygon') and intersection.is_valid,
                'connected_road_corridor_invalid_intersection')
        raw_parts = [intersection] if intersection.geom_type == 'Polygon' else list(intersection.geoms)
        bound_parts, excluded_islands = [], []
        for polygon in raw_parts:
            if any(line_parts(p.intersection(polygon)) for p in wet_parts):
                bound_parts.append(polygon)
            else:
                # A hazard island beside the road is not an affected road
                # fragment. Exclusion is recorded and no source core is lost.
                excluded_islands.append({'geometry_sha256': sha(mapping(polygon)),
                    'area_square_metres': metric_geometry(polygon).area,
                    'reason': 'no_intersection_with_modeled_road_centerline'})
        require(bool(bound_parts) and len(excluded_islands) <= 512, 'connected_road_component_binding_unresolved')
        extent = set_srid(union_all(bound_parts), 4326)
        coverage = box(*self.noah.manifest.bounds)
        require(coverage.covers(extent), 'connected_road_corridor_outside_asset_coverage')
        validation = validate_operational_shape(extent, geometry_srid=4326)
        require(validation.is_eligible, validation.reason_code)
        cores = []
        for polygon in validation.polygon_parts:
            poly = shape(polygon)
            contained = [p.intersection(poly) for p in wet_parts if p.intersects(poly)]
            linear = [l for piece in contained for l in line_parts(piece)]
            require(bool(linear), 'connected_road_component_binding_unresolved')
            core = union_all(linear)
            cores.append(mapping(core))
        actual_core = union_all([shape(c) for c in cores])
        require(abs(metric_geometry(actual_core).length - metric_geometry(wet).length)
            <= LINE_PRECISION_METRES * max(1, len(scenario_evidence)), 'connected_road_core_coverage_changed')
        evidence = {'policy_version': VERSION, 'identity': self.identity, 'selection': selected,
            'osm_way_ids': sorted(w['osm_id'] for w in ways), 'source_centerlines': [mapping(l) for l in lines],
            'source_node_coordinates': sorted({tuple(n) for w in ways for n in w['nodes']}),
            'source_network_sha256': sha(ways), 'source_length_metres': metric_geometry(merged).length,
            'modeled_fragment_length_metres': metric_geometry(wet).length,
            'buffer_radius_metres': MARGIN_METRES, 'component_centerlines': cores,
            'scenario_fragments': scenario_evidence, 'administrative_boundaries_clip': False,
            'corridor_clipped_to_modeled_envelope': True,
            'excluded_off_road_hazard_islands': excluded_islands,
            'reported_locality': {'city': claim.canonical_city, 'barangay': claim.canonical_barangay},
            'geometry_basis': 'estimated_road_corridor', 'measured_flood_extent': False}
        return ConnectedRoadZone(validation.geojson, evidence, sha({'geometry': validation.geojson, 'evidence': evidence}))


def qualified_junction_overlap(first: dict, second: dict) -> dict | None:
    """Two low-depth presentation roads may share their actual mapped junction.

    This does not permit overlaps with an existing active event, disconnected
    roads, grade-separated crossings, or overlap away from that junction.
    """
    left, right = shape(first['geometry']), shape(second['geometry'])
    if not left.intersects(right):
        return None
    a = {n[0]: n[1:] for n in first['geometry_evidence'].get('source_node_coordinates', [])}
    b = {n[0]: n[1:] for n in second['geometry_evidence'].get('source_node_coordinates', [])}
    shared = sorted(i for i in a.keys() & b.keys() if tuple(a[i]) == tuple(b[i]))
    require(bool(shared), 'connected_road_selected_overlap_without_shared_junction')
    boundary = union_all([metric_geometry(Point(*a[i])).buffer(2 * MARGIN_METRES) for i in shared])
    overlap = left.intersection(right)
    require(boundary.covers(metric_geometry(overlap)), 'connected_road_selected_overlap_outside_junction')
    return {'kind': 'same_observation_low_depth_passable_road_junction', 'shared_osm_node_ids': shared,
        'other_group_id': second['group_id'], 'intersection_sha256': sha(mapping(overlap)),
        'junction_check_distance_metres': 2 * MARGIN_METRES, 'changes_geometry': False}
