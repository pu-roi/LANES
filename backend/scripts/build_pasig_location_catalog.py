"""Validate the source-consistent 30-barangay COD subset for flood location.

This catalog is separate from the OSM/NOAH operational news-placement assets.
No polygon repair, clipping, simplification, geocoding guesses or DB write.
Run from backend: python -m scripts.build_pasig_location_catalog
"""
import hashlib
import json
import csv
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import unary_union

from app.services.barangay_boundary_service import BoundaryCatalog, BarangayBoundaryProvider
from scripts.clean_pasig_flood_history import load_barangay_reference, barangay_key
from scripts.qualify_pasig_duration_data import ROOT

INPUT = ROOT/"data/pasig-local-model-20261008"
OUTPUT = ROOT/"backend/runtime_data/flood-location"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(source: Path = INPUT, output: Path = OUTPUT) -> dict:
    city_source, barangay_source = source/"pasig-cod-adm3.geojson", source/"pasig-cod-adm4.geojson"
    before = {p.name:digest(p) for p in (city_source, barangay_source, source/"hdx-metadata.json")}
    metadata = json.loads((source/"hdx-metadata.json").read_text(encoding="utf-8"))["result"]
    if metadata["license_id"] != "cc-by-igo":
        raise ValueError("Dataset licence changed")
    reference_path = ROOT/"data/pasig_barangay_reference.csv"
    references = load_barangay_reference(reference_path)
    with reference_path.open(encoding="utf-8", newline="") as handle:
        by_source_code = {"PH"+row["psgc_correspondence_code"][:2]+"0"+row["psgc_correspondence_code"][2:]:row for row in csv.DictReader(handle)}
    city_features = json.loads(city_source.read_text(encoding="utf-8"))["features"]
    if len(city_features) != 1 or city_features[0]["properties"]["adm3_pcode"] != "PH1307403":
        raise ValueError("Wrong or ambiguous parent city")
    city = shape(city_features[0]["geometry"])
    if city.is_empty or not city.is_valid or city.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError("Invalid original city polygon")
    records, polygons, identities = [], [], set()
    for feature in json.loads(barangay_source.read_text(encoding="utf-8"))["features"]:
        props = feature["properties"]
        row = by_source_code.get(props["adm4_pcode"])
        raw_name = props["adm4_name"]
        reviewed_name = "San Nicolas" if raw_name == "San Nicolas (Pob.)" else raw_name
        if (row is None or props["adm3_pcode"] != "PH1307403" or props["adm3_name"] != "City of Pasig"
                or barangay_key(reviewed_name) != barangay_key(row["barangay_name"])):
            raise ValueError("Barangay code/name/parent crosswalk conflict")
        polygon = shape(feature["geometry"])
        if polygon.is_empty or not polygon.is_valid or not city.covers(polygon):
            raise ValueError("Invalid source geometry or parent disagreement")
        if row["psgc_10_digit_code"] in identities:
            raise ValueError("Duplicate barangay identity")
        identities.add(row["psgc_10_digit_code"])
        polygons.append(polygon)
        records.append(dict(city="City of Pasig", barangay=row["barangay_name"],
            psgc_code=row["psgc_10_digit_code"], source_url="https://data.humdata.org/dataset/cod-ab-phl",
            geometry=feature["geometry"]))
    if len(records) != 30 or len(identities) != len(references):
        raise ValueError("Incomplete current 30-barangay identity coverage")
    if any(a.intersection(b).area > 1e-12 for i,a in enumerate(polygons) for b in polygons[i+1:]):
        raise ValueError("Overlapping source interiors require review")
    if city.symmetric_difference(unary_union(polygons)).area > 1e-12:
        raise ValueError("Source barangays do not partition the source parent")
    subset = dict(type="FeatureCollection", features=city_features+json.loads(barangay_source.read_text(encoding="utf-8"))["features"])
    subset_bytes = (json.dumps(subset, sort_keys=True, separators=(",", ":"))+"\n").encode()
    source_digest = hashlib.sha256(subset_bytes).hexdigest()
    catalog = BoundaryCatalog(format_version=1, source_id=f"ocha-phl-cod-v03:pasig:{source_digest[:16]}",
        source_url="https://data.humdata.org/dataset/cod-ab-phl", source_sha256=source_digest,
        snapshot_at=datetime(2025,2,13,tzinfo=timezone.utc), verified_at=datetime.now(timezone.utc),
        verified_by="Codex source/identity/topology validation", source_classification="reviewed_source",
        review_method="OCHA/HDX COD source records, exact current/legacy PSGC parent/code/name crosswalk; valid complete unsimplified polygons, disjoint interiors and exact partition of the same-source Pasig parent. No clipping/repair or cadastral/field verification. Prediction locality only; not operational flood extent.",
        attribution="OCHA Philippines/HDX; source NAMRIA and PSA; CC BY-IGO. Humanitarian administrative geometry, not a legal boundary or observed inundation.",
        records=sorted(records,key=lambda r:r["barangay"]))
    output.mkdir(parents=True, exist_ok=True)
    (output/"source_subset.geojson").write_bytes(subset_bytes)
    (output/"city.geojson").write_text(json.dumps(city_features[0],sort_keys=True,separators=(",", ":"))+"\n",encoding="utf-8")
    (output/"boundaries.json").write_text(catalog.model_dump_json()+"\n",encoding="utf-8")
    manifest = dict(catalog_sha256=digest(output/"boundaries.json"), city_sha256=digest(output/"city.geojson"),
        source_subset_sha256=source_digest, expected_pasig_barangays=30,
        source_url=catalog.source_url, licence=metadata["license_title"], licence_id=metadata["license_id"],
        purpose="prediction_locality_not_news_activation_or_flood_footprint", builder_sha256=digest(Path(__file__)),
        source_input_sha256=before, geometry_modified=False, proves_current_flood=False, may_affect_routing=False)
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    if any(digest(source/name) != expected for name,expected in before.items()):
        raise ValueError("Original source changed during validation")
    if BarangayBoundaryProvider(output).error:
        raise ValueError("Catalog failed PSGC/runtime validation")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(),indent=2))
