"""Source code/name/parent and binary geometry checks cannot be bypassed."""
import hashlib
import struct

import pytest
from shapely.geometry import box, mapping
from scripts.build_news_ncr_cod_catalog import source_reference, validated_original_polygon


def references():
    row = dict(psgc_code="1380400016", correspondence_code="137502016", name="San Agustin",
        city_municipality="City of Malabon")
    return {row["psgc_code"]: row, row["correspondence_code"]: row}


@pytest.mark.parametrize("changes,reason", [({}, None), ({"adm3_name": "Quezon City"}, "source_parent_identity_disagreement"),
    ({"adm4_name": "San Antonio"}, "source_name_identity_disagreement"),
    ({"adm1_pcode": "PH03"}, "source_outside_ncr"), ({"adm4_pcode": "PH1307502999"}, "source_identity_not_in_current_reference")])
def test_source_crosswalk_requires_exact_current_code_name_and_parent(changes, reason):
    properties = dict(adm1_pcode="PH13", adm1_name="National Capital Region (NCR)", adm3_name="City of Malabon",
        adm4_name="San Agustin", adm4_pcode="PH1307502016")
    row, actual = source_reference({**properties, **changes}, references())
    assert actual == reason
    assert (row is not None) == (reason is None)


def test_poblacion_descriptor_does_not_change_exact_code_parent_identity():
    properties = dict(adm1_pcode="PH13", adm1_name="National Capital Region (NCR)", adm3_name="City of Malabon",
        adm4_name="San Agustin (Pob.)", adm4_pcode="PH1307502016")
    row, reason = source_reference(properties, references())
    assert reason is None and row["psgc_code"] == "1380400016"
    assert source_reference({**properties, "adm4_name": "San Agustin (West)"}, references())[1] == "source_name_identity_disagreement"


@pytest.mark.parametrize("tamper", [None, "geometry", "attributes", "binary"])
def test_original_binary_and_attributes_prove_geometry_without_silent_repair(tmp_path, tamper):
    from shapely.geometry.polygon import orient
    polygon = orient(box(121, 14.6, 121.01, 14.61), sign=-1)
    coordinates = list(polygon.exterior.coords)
    body = struct.pack("<L4d2L", 5, *polygon.bounds, 1, len(coordinates)) + struct.pack("<L", 0)
    body += b"".join(struct.pack("<2d", *point) for point in coordinates)
    original = struct.pack(">2L", 1, len(body)//2) + body
    path = tmp_path / "phl_admin4-1.record"
    path.write_bytes(original)
    attributes = {1: {"adm4_name": "San Agustin"}}
    feature = dict(properties={**attributes[1], "source_record_index": 1,
        "source_record_sha256": hashlib.sha256(original).hexdigest()}, geometry=mapping(polygon))
    if tamper == "geometry":
        feature["geometry"] = mapping(box(121, 14.6, 121.005, 14.61))
    elif tamper == "attributes":
        feature["properties"]["adm4_name"] = "Other barangay"
    elif tamper == "binary":
        path.write_bytes(original[:-2]+b"xx")
    if tamper:
        with pytest.raises(ValueError):
            validated_original_polygon(feature, tmp_path, 4, attributes)
    else:
        assert validated_original_polygon(feature, tmp_path, 4, attributes).equals_exact(polygon, 0)
