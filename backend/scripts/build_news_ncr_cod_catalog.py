"""Qualify missing NCR news boundaries from archived original COD records.

OSM retains precedence. Reject stale identities, source/OSM parent disagreement,
invalid geometry or missing original record hashes. Never repair or clip shapes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED

from shapely.geometry import shape
from app.services.article_road_match_service import normalize_name
from app.services.barangay_boundary_service import BarangayBoundaryProvider
from app.services.news_road_placement_service import NewsRoadPlacementProvider, DEFAULT_CATALOG_DIR, city_key
from scripts.build_news_barangay_catalog import metro_reference, DEFAULT_PSGC_REFERENCE
from scripts.fetch_news_ncr_cod_boundaries import source_rows
from scripts.fetch_pasig_cod_boundaries import polygon_record


def validated_original_polygon(feature: dict, capture: Path, level: int, attributes: dict[int, dict]):
    properties = feature["properties"]
    index = properties["source_record_index"]
    if type(index) is not int or not 0 <= index < 50_000 or index not in attributes:
        raise ValueError("Invalid original source record index")
    if {key: value for key, value in properties.items() if key not in {"source_record_index", "source_record_sha256"}} != attributes[index]:
        raise ValueError("Captured source attributes differ from original DBF")
    original = capture / f"phl_admin{level}-{index}.record"
    if original.stat().st_size > 32_000_000:
        raise ValueError("Original record size budget")
    raw = original.read_bytes()
    if hashlib.sha256(raw).hexdigest() != properties["source_record_sha256"]:
        raise ValueError("Original source record hash mismatch")
    polygon = shape(feature["geometry"])
    if not polygon.equals_exact(polygon_record(raw), 0):
        raise ValueError("Captured geometry differs from original binary record")
    return polygon


def source_reference(properties: dict, references: dict[str, dict]) -> tuple[dict | None, str | None]:
    if properties.get("adm1_pcode") != "PH13" or properties.get("adm1_name") != "National Capital Region (NCR)":
        return None, "source_outside_ncr"
    code = properties.get("adm4_pcode", "")
    digits = code[2:] if code.startswith("PH") else ""
    parent = city_key(properties.get("adm3_name", ""))
    if len(digits) != 10 or not digits.isdigit() or digits[:3] != "130":
        return None, "source_pcode_invalid"
    # COD expands the zero-padded province part of nine-digit PSA correspondence
    # codes. Manila's source assigns city-wide numbers instead of district rows.
    correspondence = digits[:2] + digits[3:]
    row = references.get(correspondence)
    if row is None and parent == "manila":
        matches = {r["psgc_code"]: r for r in references.values() if city_key(r["city_municipality"]) == "manila"
            and normalize_name(r["name"]) == normalize_name(properties.get("adm4_name", ""))}
        if len(matches) == 1:
            row = next(iter(matches.values()))
    if row is None:
        return None, "source_identity_not_in_current_reference"
    if parent != city_key(row["city_municipality"]):
        return None, "source_parent_identity_disagreement"
    source_name = re.sub(r"\s*\((?:pob\.?|poblacion)\)\s*$", "", properties.get("adm4_name", ""), flags=re.I)
    if normalize_name(row["name"]) != normalize_name(source_name):
        return None, "source_name_identity_disagreement"
    return row, None


def build(capture: Path, output: Path, *, osm_boundaries: Path,
          osm_directory: Path = DEFAULT_CATALOG_DIR, psgc_reference: Path = DEFAULT_PSGC_REFERENCE) -> dict:
    if output.exists():
        raise ValueError("Output must be an immutable new version directory")
    metadata = json.loads((capture / "hdx-metadata.json").read_text(encoding="utf-8"))["result"]
    if metadata["license_id"] != "cc-by-igo":
        raise ValueError("Unqualified source licence")
    receipt = json.loads((capture / "cod-capture-receipt.json").read_text(encoding="utf-8"))
    if receipt["source_geometry_modified"] is not False:
        raise ValueError("Original source geometry required")
    existing = BarangayBoundaryProvider(osm_boundaries)
    roads = NewsRoadPlacementProvider(osm_directory, existing)
    roads._load()
    if existing.error or roads.error:
        raise ValueError(existing.error or roads.error)
    references = metro_reference(psgc_reference)
    attributes = {level: {row["index"]: row["properties"] for row in source_rows(
        (capture / f"phl_admin{level}.dbf").read_bytes())} for level in (3, 4)}
    parents = {}
    for feature in json.loads((capture / "ncr-cod-adm3.geojson").read_text(encoding="utf-8"))["features"]:
        properties = feature["properties"]
        key = city_key(properties["adm3_name"])
        polygon = validated_original_polygon(feature, capture, 3, attributes[3])
        if key in parents or key not in roads.boundaries or not polygon.is_valid or polygon.is_empty:
            raise ValueError("Invalid or duplicate source parent")
        parents[key] = (properties["adm3_pcode"], polygon)
    if len(parents) != 17:
        raise ValueError("Complete source parents required")
    features = json.loads((capture / "ncr-cod-adm4.geojson").read_text(encoding="utf-8"))["features"]
    assigned = [source_reference(feature["properties"], references) for feature in features]
    from collections import Counter
    counts = Counter(row["psgc_code"] for row, reason in assigned if row)
    accepted, excluded, dates = [], [], set()
    for feature, (row, reason) in zip(features, assigned):
        properties = feature["properties"]
        polygon = validated_original_polygon(feature, capture, 4, attributes[4])
        if not reason and counts[row["psgc_code"]] != 1:
            reason = "duplicate_current_source_identity"
        key = city_key(row["city_municipality"]) if row else None
        if not reason and (key, normalize_name(row["name"])) in existing.records:
            reason = "qualified_osm_precedence"
        if not reason and (polygon.is_empty or not polygon.is_valid or polygon.geom_type not in {"Polygon", "MultiPolygon"}):
            reason = "invalid_original_source_polygon"
        if not reason and (key not in parents or properties["adm3_pcode"] != parents[key][0]
                           or not parents[key][1].covers(polygon)):
            reason = "source_boundary_parent_mismatch"
        if not reason and not roads.boundaries[key].covers(polygon):
            reason = "checked_osm_city_containment_mismatch"
        if reason:
            excluded.append(dict(source_pcode=properties["adm4_pcode"], name=properties["adm4_name"],
                city=properties["adm3_name"], psgc_code=row["psgc_code"] if row else None, reason=reason))
            continue
        dates.add(properties["valid_on"])
        accepted.append(dict(city=row["city_municipality"], barangay=row["name"], psgc_code=row["psgc_code"],
            source_url=receipt["source_url"] + "#adm4-record-" + str(properties["source_record_index"]),
            geometry=feature["geometry"]))
    if not accepted or len(dates) != 1:
        raise ValueError("No qualified consistent-vintage source gap records")
    snapshot = datetime.strptime(next(iter(dates)), "%Y%m%d").replace(tzinfo=timezone.utc).isoformat()
    output.mkdir(parents=True, exist_ok=False)
    # Private archive contains exact selected source records/attributes, not a
    # fabricated polygon source or the full national archive.
    archive = capture / "news-qualified-original-records.zip"
    source_paths = sorted(capture.glob("*.record")) + [capture / name for name in
        ("hdx-metadata.json", "hdx-zip-tail.bin", "cod-capture-receipt.json", "phl_admin3.transfer.json",
         "phl_admin4.transfer.json", "phl_admin3.prj", "phl_admin4.prj", "phl_admin3.dbf", "phl_admin4.dbf")]
    if archive.exists():
        # A new review version may reuse an identical original archive. Prove
        # every member rather than overwriting or trusting its previous receipt.
        if archive.stat().st_size > 128 * 1024 * 1024:
            raise ValueError("Original source subset size budget")
        with ZipFile(archive) as zipped:
            if len(zipped.namelist()) != len(source_paths) or set(zipped.namelist()) != {path.name for path in source_paths}:
                raise ValueError("Original subset archive membership mismatch")
            for path in source_paths:
                if zipped.getinfo(path.name).file_size != path.stat().st_size:
                    raise ValueError("Original archive member size mismatch")
                actual, expected = hashlib.sha256(), hashlib.sha256()
                with zipped.open(path.name) as stream:
                    for piece in iter(lambda: stream.read(1_048_576), b""):
                        actual.update(piece)
                with path.open("rb") as stream:
                    for piece in iter(lambda: stream.read(1_048_576), b""):
                        expected.update(piece)
                if actual.digest() != expected.digest():
                    raise ValueError("Original archive member hash mismatch")
    else:
        with ZipFile(archive, "x", compression=ZIP_STORED) as zipped:
            for path in source_paths:
                zipped.write(path, path.name)
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    payload = dict(format_version=1, source_id=f"cod-ncr-news:{snapshot[:10]}:{archive_sha[:16]}",
        source_url=receipt["source_url"], source_sha256=archive_sha, snapshot_at=snapshot,
        verified_at=datetime.now(timezone.utc).isoformat(), verified_by="Codex automated source/identity/topology review",
        review_method="Original OCHA/HDX COD records, exact NCR source parent/code and current PSA identity/name crosswalk; "
            "Manila numbered barangays match unique canonical city/name across source city-wide versus PSA district codes. "
            "Complete unsimplified WGS84 polygons; original binary hashes, same-source parent and checked OSM city containment. "
            "No legal/cadastral/field verification, clipping or repair.",
        source_classification="reviewed_source", attribution=metadata["title"] + "; OCHA Philippines/HDX; NAMRIA and PSA. "
            "CC BY 3.0 IGO; https://creativecommons.org/licenses/by/3.0/igo/. Geometry unchanged; identity crosswalk added. "
            "Humanitarian administrative geometry, not a legal boundary or observed inundation; no publisher endorsement.", records=accepted)
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    (output / "boundaries.json").write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    (output / "manifest.json").write_text(json.dumps(dict(catalog_sha256=digest)), encoding="utf-8")
    review = dict(catalog_sha256=digest, source_sha256=archive_sha, source_archive=str(archive),
        osm_catalog_sha256=roads.digest, osm_boundary_sha256=existing.digest,
        licence_id=metadata["license_id"], licence_url=metadata.get("license_url"), source_classification="reviewed_source",
        accepted_records=len(accepted), excluded_records=excluded, source_geometry_modified=False,
        psgc_reference_sha256=hashlib.sha256(psgc_reference.read_bytes()).hexdigest(), proves_current_flood=False,
        builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        may_affect_routing=False)
    (output / "review_receipt.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
    if BarangayBoundaryProvider(output).error:
        raise ValueError("Qualified source catalog failed runtime validation")
    return review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--osm-boundaries", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.capture, args.output, osm_boundaries=args.osm_boundaries)
    print(json.dumps({key: result[key] for key in ("accepted_records", "source_sha256", "catalog_sha256")}, indent=2))


if __name__ == "__main__":
    main()
