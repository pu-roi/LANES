"""Operator-owned asset integrity, separate from caller provenance labels."""
from copy import deepcopy
import json

import pytest
from shapely.geometry import Polygon, mapping

from app.crud.news_evaluation import canonical_sha256
from app.services.operational_footprint_evidence_service import IncidentFootprintProvider
from tests.operational_footprint_fixtures import write_catalog


def record():
    geometry = mapping(Polygon([(121.07,14.58),(121.071,14.58),(121.071,14.581),(121.07,14.581)]))
    return dict(record_id="synthetic-record",source_id="synthetic-authority",source_url="https://example.org/incident",
        source_sha256="a"*64,evidence_kind="authoritative_current_incident",article_id=1,input_sha256="b"*64,
        claim_sha256="c"*64,incident_identity="d"*64,observed_at="2026-10-05T03:00:00Z",city="City of Pasig",
        barangay=None,srid=4326,geometry=geometry,component_sha256=[canonical_sha256(geometry)])


def test_catalog_is_explicitly_unconfigured():
    provider = IncidentFootprintProvider(None)
    assert provider.error == "operational_footprint_catalog_not_configured" and not provider.records


def test_valid_operator_catalog_loads_exact_geometry_and_digest(tmp_path):
    value = record()
    write_catalog(tmp_path,[value])
    provider = IncidentFootprintProvider(tmp_path)
    assert provider.error is None and len(provider.digest) == 64
    assert canonical_sha256(provider.records[value["record_id"]].geometry) == canonical_sha256(value["geometry"])


@pytest.mark.parametrize("case", ["checksum","unapproved_source","duplicate_id","modeled_susceptibility",
    "historical_evidence","naive_time","srid","components","bad_geometry","unexpected_field","oversized_manifest","invalid_manifest"])
def test_malformed_or_unapproved_catalog_fails_closed(tmp_path,case):
    value = record()
    records = [value]
    if case == "duplicate_id": records.append(deepcopy(value))
    elif case == "modeled_susceptibility": value["evidence_kind"] = "modeled_susceptibility"
    elif case == "historical_evidence": value["evidence_kind"] = "historical_drrmo"
    elif case == "naive_time": value["observed_at"] = "2026-10-05T03:00:00"
    elif case == "srid": value["srid"] = 3857
    elif case == "components": value["component_sha256"] = ["f"*64]
    elif case == "bad_geometry": value["geometry"] = {"type":"Point","coordinates":[121.07,14.58]}
    elif case == "unexpected_field": value["approved"] = True
    write_catalog(tmp_path,records,approved=["different"] if case == "unapproved_source" else None)
    if case == "checksum": (tmp_path/"footprints.json").write_bytes((tmp_path/"footprints.json").read_bytes()+b" ")
    elif case == "oversized_manifest": (tmp_path/"manifest.json").write_text(" "*8193)
    elif case == "invalid_manifest": (tmp_path/"manifest.json").write_text("[]")
    provider = IncidentFootprintProvider(tmp_path)
    assert provider.error == "invalid_operational_footprint_catalog" and not provider.records
