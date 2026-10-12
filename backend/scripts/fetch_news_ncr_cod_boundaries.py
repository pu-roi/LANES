"""Archive complete NCR COD source records using bounded original ZIP ranges.

No national ZIP installation, geometry repair, runtime adoption or flood writes.
An existing reviewed partial transfer can be reused after exact metadata/hash and
source-range checks. New output directories only; previous captures survive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path

import httpx
from scripts.fetch_pasig_cod_boundaries import METADATA_URL, range_bytes, members, data_offset, polygon_record

MAX_COMPRESSED = 192_000_000


def source_rows(dbf: bytes) -> list[dict]:
    count = struct.unpack_from("<L", dbf, 4)[0]
    header, length = struct.unpack_from("<HH", dbf, 8)
    if count > 50_000 or not 1 <= length <= 4000 or len(dbf) < header + count * length:
        raise ValueError("Invalid bounded source attributes")
    fields, offset = [], 1
    for pos in range(32, header - 1, 32):
        item = dbf[pos:pos + 32]
        if item[0] == 13:
            break
        fields.append((item[:11].split(b"\0")[0].decode("ascii"), offset, item[16]))
        offset += item[16]
    rows = []
    for index in range(count):
        row = dbf[header + index * length:header + (index + 1) * length]
        if row[0] == ord("*"):
            continue
        values = {name: row[start:start + size].decode("utf-8").strip() for name, start, size in fields}
        if values.get("adm1_pcode") == "PH13" and values.get("adm1_name") == "National Capital Region (NCR)":
            rows.append(dict(index=index, properties=values))
    return rows


def capture_selected(client, url: str, member: dict, shx: bytes, selected: list[dict], stem: str,
                     output: Path, reuse: Path | None) -> list[dict]:
    targets = []
    for row in selected:
        offset, length = struct.unpack_from(">2L", shx, 100 + row["index"] * 8)
        targets.append((offset * 2, length * 2 + 8, row))
    last = max(offset + length for offset, length, _ in targets)
    base = data_offset(client, url, member)
    decoder, position, compressed_count = zlib.decompressobj(-15), 0, 0
    stored = {row["index"]: bytearray() for _, _, row in targets}

    def consume(piece: bytes) -> None:
        nonlocal position, compressed_count
        compressed_count += len(piece)
        if compressed_count > MAX_COMPRESSED:
            raise ValueError("Compressed source budget exceeded")
        expanded = decoder.decompress(piece, 4_000_001)
        if len(expanded) > 4_000_000 or decoder.unconsumed_tail:
            raise ValueError("Source chunk expansion budget exceeded")
        for offset, length, row in targets:
            left, right = max(offset, position), min(offset + length, position + len(expanded))
            if right > left:
                stored[row["index"]].extend(expanded[left - position:right - position])
        position += len(expanded)

    reused = None
    if reuse is not None:
        prefix = reuse / (stem + ".source-prefix.deflate")
        receipt = json.loads((reuse / (stem + ".transfer.json")).read_text(encoding="utf-8"))
        if receipt["source_member"] != member or receipt["url"] != url or prefix.stat().st_size > MAX_COMPRESSED:
            raise ValueError("Reused source identity mismatch")
        digest = hashlib.sha256()
        with prefix.open("rb") as stream:
            for piece in iter(lambda: stream.read(65_536), b""):
                digest.update(piece)
        if digest.hexdigest() != receipt["prefix_sha256"] or prefix.stat().st_size != receipt["compressed_bytes"]:
            raise ValueError("Reused source transfer hash mismatch")
        with prefix.open("rb") as stream:
            stream.seek(-16_384, 2)
            tail = stream.read()
        if range_bytes(client, url, base + prefix.stat().st_size - len(tail), base + prefix.stat().st_size - 1) != tail:
            raise ValueError("Archived source differs from current range")
        with prefix.open("rb") as stream:
            for piece in iter(lambda: stream.read(65_536), b""):
                consume(piece)
                if position >= last:
                    break
        reused = dict(archive_path=str(prefix), sha256=receipt["prefix_sha256"], bytes=prefix.stat().st_size)
    delta = output / (stem + ".source-tail.deflate")
    if position < last:
        begin = base + compressed_count
        with client.stream("GET", url, headers={"Range": f"bytes={begin}-{base + member['compressed_size'] - 1}"}) as response:
            response.raise_for_status()
            if response.status_code != 206 or not response.headers.get("content-range", "").startswith(f"bytes {begin}-"):
                raise ValueError("Source did not honor continuation range")
            with delta.open("wb") as stream:
                for piece in response.iter_bytes(chunk_size=65_536):
                    stream.write(piece)
                    consume(piece)
                    if position >= last:
                        break
    features, exclusions = [], []
    for offset, length, row in targets:
        raw = bytes(stored[row["index"]])
        if len(raw) != length:
            raise ValueError("Selected source record incomplete")
        (output / f"{stem}-{row['index']}.record").write_bytes(raw)
        try:
            polygon = polygon_record(raw)
        except ValueError:
            exclusions.append(dict(index=row["index"], properties=row["properties"], reason="invalid_original_source_polygon"))
            continue
        from shapely.geometry import mapping
        features.append(dict(type="Feature", properties={**row["properties"], "source_record_index": row["index"],
            "source_record_sha256": hashlib.sha256(raw).hexdigest()}, geometry=mapping(polygon)))
    receipt = dict(url=url, source_member=member, range_start=base, expanded_through=position,
        compressed_bytes_processed=compressed_count, reused_archive=reused,
        continuation_sha256=hashlib.sha256(delta.read_bytes()).hexdigest() if delta.exists() else None,
        selected_records=len(selected), valid_polygons=len(features), exclusions=exclusions,
        note="Complete selected original records; full national member CRC is not claimed.")
    (output / (stem + ".transfer.json")).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return features


def fetch(output: Path, *, reuse: Path | None = None) -> dict:
    if output.exists():
        raise ValueError("Output must be a fresh capture directory")
    output.mkdir(parents=True, exist_ok=False)
    with httpx.Client(timeout=httpx.Timeout(60, connect=10), follow_redirects=True) as client:
        response = client.get(METADATA_URL)
        response.raise_for_status()
        if len(response.content) > 4_000_000:
            raise ValueError("Metadata size budget")
        (output / "hdx-metadata.json").write_bytes(response.content)
        metadata = response.json()["result"]
        if metadata["license_id"] != "cc-by-igo":
            raise ValueError("Source licensing requires a new review")
        resource = next(item for item in metadata["resources"] if item["format"] == "SHP")
        url, size = resource["url"], int(resource["size"])
        if not url.startswith("https://data.humdata.org/") or not 131_072 <= size <= 2_000_000_000:
            raise ValueError("Unqualified source archive location/size")
        tail = range_bytes(client, url, size - 131_072, size - 1)
        (output / "hdx-zip-tail.bin").write_bytes(tail)
        table = members(tail)
        counts = {}
        for level in (3, 4):
            stem = f"phl_admin{level}"
            for extension in ("dbf", "shx", "prj"):
                item = table[stem + "." + extension]
                if item["size"] > 128_000_000:
                    raise ValueError("Source member size budget")
                prior = reuse / (stem + "." + extension) if reuse else None
                if prior and prior.exists():
                    raw = prior.read_bytes()
                else:
                    begin = data_offset(client, url, item)
                    packed = range_bytes(client, url, begin, begin + item["compressed_size"] - 1)
                    raw = zlib.decompressobj(-15).decompress(packed, item["size"] + 1)
                if len(raw) != item["size"] or zlib.crc32(raw) != item["crc32"]:
                    raise ValueError("Original member size/CRC mismatch")
                (output / (stem + "." + extension)).write_bytes(raw)
                if extension == "prj" and (b"WGS_1984" not in raw or b"PROJCS" in raw):
                    raise ValueError("Unqualified source CRS")
            selected = source_rows((output / (stem + ".dbf")).read_bytes())
            if not selected or len(selected) > (17 if level == 3 else 2000):
                raise ValueError("Unexpected bounded NCR source count")
            if level == 3 and len(selected) != 17:
                raise ValueError("Missing NCR parent source records")
            features = capture_selected(client, url, table[stem + ".shp"],
                (output / (stem + ".shx")).read_bytes(), selected, stem, output, reuse)
            (output / f"ncr-cod-adm{level}.geojson").write_text(json.dumps(
                dict(type="FeatureCollection", features=features), separators=(",", ":")), encoding="utf-8")
            counts[str(level)] = dict(selected=len(selected), valid_polygons=len(features))
            print(json.dumps(dict(stage="capture", level=level, **counts[str(level)])), flush=True)
        receipt = dict(metadata_url=METADATA_URL, source_url=url, licence=metadata["license_title"],
            retrieved_at=datetime.now(timezone.utc).isoformat(), publisher="OCHA Philippines / HDX",
            source=metadata.get("dataset_source"), source_geometry_modified=False, counts=counts)
        (output / "cod-capture-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reuse-capture-directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(fetch(args.output, reuse=args.reuse_capture_directory), indent=2))


if __name__ == "__main__":
    main()
