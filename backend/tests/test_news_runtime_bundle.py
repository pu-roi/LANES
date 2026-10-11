"""Release assets must retain geometry/identity and fail before deployment."""
from pathlib import Path

import pytest
from shapely.geometry import LineString

from app.services.noah_vector_catalog_service import NoahVectorCatalog
from scripts.package_news_noah_assets import package_assets
from scripts.verify_news_runtime_assets import verify_assets
from test_news_placement_preview import noah_catalog
from test_news_spatial_assets import provisioning_inputs


def test_packaged_catalog_retains_hazard_intersections_and_exact_source_bytes(tmp_path: Path) -> None:
    source = noah_catalog(tmp_path / "source")
    output = tmp_path / "packaged"
    receipt = package_assets(source.directory, output)
    copied = NoahVectorCatalog(output)
    line = LineString([(121.01, 14.61), (121.01, 14.65)])
    assert copied.overlaps(line) == source.overlaps(line)
    assert copied.revision == source.revision == receipt["noah_catalog_sha256"]
    assert (output / "manifest.json").read_bytes() == (source.directory / "manifest.json").read_bytes()
    assert not receipt["proves_current_flood"]


def test_corrupted_source_cannot_create_release_bundle(tmp_path: Path) -> None:
    source = noah_catalog(tmp_path / "source")
    next((source.directory / "5").glob("*.gz")).write_bytes(b"corrupt")
    output = tmp_path / "packaged"
    with pytest.raises(ValueError, match="missing_or_invalid_noah_tile"):
        package_assets(source.directory, output)
    assert not output.exists()


def test_packaging_never_overwrites_existing_snapshot(tmp_path: Path) -> None:
    source = noah_catalog(tmp_path / "source")
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_bytes(b"existing snapshot")
    with pytest.raises(ValueError, match="new directory"):
        package_assets(source.directory, output)
    assert marker.read_bytes() == b"existing snapshot"


@pytest.mark.parametrize("failure", [None, "tile", "boundary", "history"])
def test_runtime_check_rejects_incomplete_or_wrong_parent_bundle(tmp_path: Path, failure: str | None) -> None:
    _, _, _, roads = provisioning_inputs(tmp_path, outside=failure == "boundary")
    noah = tmp_path / "noah"
    noah_catalog(noah)
    history = tmp_path / "history.csv"
    history.write_text("source_year,source_record_no,barangay_canonical,street_normalized,landmark_normalized\n")
    if failure == "tile":
        next((noah / "100").glob("*.gz")).unlink()
    if failure == "history":
        history.write_text("unrelated,columns\n")
    if failure:
        with pytest.raises(ValueError):
            verify_assets(noah, roads, tmp_path / "reviewed", history)
    else:
        result = verify_assets(noah, roads, tmp_path / "reviewed", history)
        assert result["status"] == "assets_ok" and result["qualified_barangay_count"] == 1
        assert not result["proves_current_flood"]
