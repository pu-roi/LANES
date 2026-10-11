"""Review source-backed Pasig OSM COMMUNITY polygons from the same local PBF.

Retain only explicit PSGC-ref/name/parent matches and complete valid rings.
This is automated topology/identity review, not official legal verification.
Never repair, simplify, buffer, install synthetic polygons or overwrite a version.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

import osmium
from shapely.geometry import LineString, mapping
from shapely.ops import polygonize_full, unary_union

from app.services.article_road_match_service import normalize_name
from app.services.barangay_boundary_service import BarangayBoundaryProvider
from app.services.news_road_placement_service import DEFAULT_CATALOG_DIR, NewsRoadPlacementProvider, city_key

DEFAULT_PSGC_REFERENCE = Path(__file__).resolve().parents[1] / "runtime_data" / "philippines_psgc_reference.csv"
OSM_LICENSE_URL = "https://www.openstreetmap.org/copyright"
REVIEW_METHOD = ("Automated review by Codex geometry agent: exact PSGC current/correspondence reference, "
    "barangay name and Pasig parent cross-check; complete source rings without cuts/dangles; "
    "valid unsimplified WGS84 polygon and strict containment in checked same-snapshot OSM city. "
    "Community map geometry; no human, cadastral, field or legal-boundary verification.")


def pasig_reference(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        records = [row for row in csv.DictReader(stream) if row["level"] == "Bgy"
                   and city_key(row["city_municipality"]) == "pasig"]
    if len(records) != 30 or len({row["psgc_code"] for row in records}) != 30:
        raise ValueError("Expected complete distinct 30-barangay Pasig PSGC reference")
    return {code: row for row in records for code in (row["psgc_code"], row["correspondence_code"]) if code}


class BarangayRelations(osmium.SimpleHandler):
    def __init__(self, references: dict[str, dict]) -> None:
        super().__init__()
        self.references = references
        self.names = {normalize_name(row["name"]) for row in references.values()}
        self.relations: list[dict] = []

    def relation(self, relation: osmium.osm.Relation) -> None:
        tags = dict(relation.tags)
        if (tags.get("boundary") != "administrative" or tags.get("admin_level") not in ("9", "10")
                or (tags.get("ref") not in self.references and normalize_name(tags.get("name", "")) not in self.names)):
            return
        self.relations.append(dict(relation_id=relation.id, tags=tags,
            members=[(member.type, member.ref, member.role) for member in relation.members]))
        if len(self.relations) > 500:
            raise ValueError("Unexpected bounded administrative relation count")


class BoundaryWays(osmium.SimpleHandler):
    def __init__(self, required: set[int]) -> None:
        super().__init__()
        self.required = required
        self.coordinates: dict[int, list[tuple[float, float]]] = {}

    def way(self, way: osmium.osm.Way) -> None:
        if way.id not in self.required:
            return
        if not 2 <= len(way.nodes) <= 10000 or any(not node.location.valid() for node in way.nodes):
            return
        self.coordinates[way.id] = [(node.lon, node.lat) for node in way.nodes]


def reviewed_polygon(members: list[tuple[str, int, str]], coordinates: dict) -> tuple[object | None, str | None]:
    if any(kind == "r" or (kind == "w" and role not in ("outer", "inner")) for kind, _, role in members):
        return None, "unsupported_boundary_members"
    parts = {role:[coordinates.get(ref) for kind, ref, selected in members if kind == "w" and selected == role]
             for role in ("outer", "inner")}
    if not parts["outer"] or any(points is None for rings in parts.values() for points in rings):
        return None, "incomplete_boundary_members"
    polygons = {}
    for role, rings in parts.items():
        if not rings:
            continue
        lines = [LineString(points) for points in rings]
        if any(not line.is_simple for line in lines):
            return None, "invalid_boundary_source_linework"
        formed, cuts, dangles, invalid = polygonize_full(lines)
        if formed.is_empty or not all(piece.is_empty for piece in (cuts, dangles, invalid)):
            return None, "unclosed_boundary_rings"
        polygons[role] = unary_union(formed)
    polygon = polygons["outer"].difference(polygons["inner"]) if "inner" in polygons else polygons["outer"]
    if polygon.is_empty or not polygon.is_valid or polygon.geom_type not in ("Polygon", "MultiPolygon"):
        return None, "invalid_boundary_polygon"
    return polygon, None


def review_records(relations: list[dict], coordinates: dict, references: dict[str, dict], city_boundary: object) -> tuple[list[dict], list[dict]]:
    accepted, excluded, identities = [], [], set()
    counts = Counter(references[item["tags"]["ref"]]["psgc_code"] for item in relations
        if item["tags"].get("ref") in references)
    for item in sorted(relations, key=lambda row: row["relation_id"]):
        tags = item["tags"]
        row = references.get(tags.get("ref", ""))
        reason = None
        if row is None:
            reason = "no_explicit_pasig_psgc_reference"
        elif normalize_name(tags.get("name", "")) != normalize_name(row["name"]):
            reason = "psgc_boundary_name_mismatch"
        elif counts[row["psgc_code"]] > 1:
            reason = "duplicate_barangay_identity"
        polygon, geometry_reason = reviewed_polygon(item["members"], coordinates)
        if reason is None:
            reason = geometry_reason
        if reason is None and not city_boundary.covers(polygon):
            reason = "barangay_boundary_parent_mismatch"
        if reason is None and row["psgc_code"] in identities:
            reason = "duplicate_barangay_identity"
        if reason:
            excluded.append(dict(osm_relation_id=item["relation_id"], name=tags.get("name"), ref=tags.get("ref"), reason=reason))
            continue
        identities.add(row["psgc_code"])
        accepted.append(dict(city=row["city_municipality"], barangay=row["name"], psgc_code=row["psgc_code"],
            osm_relation_id=item["relation_id"], source_url=f"https://www.openstreetmap.org/relation/{item['relation_id']}",
            geometry=mapping(polygon)))
    return accepted, excluded


def build_catalog(pbf: Path, output: Path, *, osm_directory: Path = DEFAULT_CATALOG_DIR,
                  psgc_reference: Path = DEFAULT_PSGC_REFERENCE) -> dict:
    if output.exists():
        raise ValueError("Output must be a new version directory")
    if pbf.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("Only the bounded Metro Manila extract is supported")
    source_sha = hashlib.sha256(pbf.read_bytes()).hexdigest()
    roads = NewsRoadPlacementProvider(osm_directory)
    roads._load()
    if roads.error or roads.catalog is None or roads.catalog.osm_sha256 != source_sha:
        raise ValueError("PBF must match checked OSM road/city snapshot")
    references = pasig_reference(psgc_reference)
    relations = BarangayRelations(references)
    relations.apply_file(str(pbf), locations=False)
    required = {ref for item in relations.relations for kind, ref, _ in item["members"] if kind == "w"}
    if len(required) > 10000:
        raise ValueError("Unexpected bounded administrative way count")
    ways = BoundaryWays(required)
    ways.apply_file(str(pbf), locations=True)
    records, excluded = review_records(relations.relations, ways.coordinates, references, roads.boundaries["pasig"])
    if not records:
        raise ValueError("No valid explicit-identity community boundaries")
    snapshot = roads.catalog.snapshot_at.isoformat()
    payload = dict(format_version=1, source_id=f"osm-pasig-barangays:{snapshot}:{source_sha[:16]}",
        source_url="https://download.openstreetmap.fr/extracts/asia/philippines/", source_sha256=source_sha,
        snapshot_at=snapshot, verified_at=datetime.now(timezone.utc).isoformat(),
        verified_by="Codex geometry agent (automated asset validation)", review_method=REVIEW_METHOD,
        source_classification="osm_community",
        attribution="OpenStreetMap contributors (ODbL); https://www.openstreetmap.org/copyright. "
            "PSGC identity crosswalk: Philippine Statistics Authority. Community boundaries are not official legal delineations.",
        records=records)
    blob = json.dumps(payload,ensure_ascii=False,separators=(",", ":"),allow_nan=False).encode()
    receipt = dict(catalog_sha256=hashlib.sha256(blob).hexdigest(), source_sha256=source_sha,
        osm_catalog_sha256=roads.digest, source_classification="osm_community",
        review_method=REVIEW_METHOD, license_url=OSM_LICENSE_URL,
        psgc_reference_sha256=hashlib.sha256(psgc_reference.read_bytes()).hexdigest(),
        accepted_records=len(records), excluded_relations=excluded,
        missing_or_excluded_barangays=sorted({row["name"] for row in references.values()} - {row["barangay"] for row in records}),
        proves_current_flood=False, may_affect_routing=False)
    output.mkdir(parents=True,exist_ok=False)
    (output / "boundaries.json").write_bytes(blob)
    (output / "manifest.json").write_text(json.dumps({"catalog_sha256":receipt["catalog_sha256"]}) + "\n",encoding="utf-8")
    (output / "review_receipt.json").write_text(json.dumps(receipt,indent=2) + "\n",encoding="utf-8")
    if BarangayBoundaryProvider(output).error:
        raise ValueError("Constructed catalog failed runtime validation")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("osm_pbf",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--osm-directory",type=Path,default=DEFAULT_CATALOG_DIR)
    args = parser.parse_args()
    print(json.dumps(build_catalog(args.osm_pbf,args.output,osm_directory=args.osm_directory),indent=2))


if __name__ == "__main__":
    main()
