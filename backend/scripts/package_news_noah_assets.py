"""Copy an existing checksummed Metro Manila NOAH catalog into a new bundle.

No downloads, geometry changes, database operations, or provider requests.
Run from backend: python -m scripts.package_news_noah_assets SOURCE OUTPUT
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from app.services.noah_vector_catalog_service import NoahVectorCatalog


def package_assets(source: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("Output must be a new directory; never replace an in-use catalog")
    catalog = NoahVectorCatalog(source)
    revision = catalog.revision  # Checks every declared tile before copying.
    if catalog.error or catalog.manifest is None:
        raise ValueError(catalog.error or "invalid_noah_catalog")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source / "manifest.json", output / "manifest.json")
    count, size = 0, 0
    for period, scenario in sorted(catalog.manifest.scenarios.items()):
        folder = output / str(period)
        folder.mkdir()
        for key in sorted(scenario.tiles):
            filename = f"{key.replace(':', '_')}.json.gz"
            shutil.copyfile(source / str(period) / filename, folder / filename)
            count += 1
            size += (folder / filename).stat().st_size
    copied = NoahVectorCatalog(output)
    if copied.revision != revision or copied.error:
        raise ValueError("copied_noah_catalog_mismatch")
    return dict(noah_catalog_sha256=revision, tile_count=count, compressed_bytes=size,
                license=catalog.manifest.license, attribution=catalog.manifest.attribution,
                proves_current_flood=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(package_assets(args.source, args.output), indent=2))


if __name__ == "__main__":
    main()
