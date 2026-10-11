"""Extract Pasig from OCHA/HDX COD-AB source ZIP using bounded byte ranges.

No national archive is installed in runtime. Selected source shapefile records,
DBF identities, metadata and transfer hashes remain under ignored data/.
Run from backend: python -m scripts.fetch_pasig_cod_boundaries
"""
import hashlib
import json
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path

import httpx
from shapely.geometry import Polygon, MultiPolygon, mapping

from scripts.qualify_pasig_duration_data import ROOT

DIRECTORY = ROOT / "data/pasig-local-model-20261008"
METADATA_URL = "https://data.humdata.org/api/3/action/package_show?id=cod-ab-phl"


def range_bytes(client: httpx.Client, url: str, start: int, end: int) -> bytes:
    if end < start or end-start > 4_000_000:
        raise ValueError("Invalid bounded range")
    with client.stream("GET", url, headers={"Range": f"bytes={start}-{end}"}) as response:
        response.raise_for_status()
        if response.status_code != 206 or not response.headers.get("content-range", "").startswith(f"bytes {start}-"):
            raise ValueError("Source does not honor exact byte ranges")
        data = bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data) > end-start+1:
                raise ValueError("Byte-range response overflow")
    if len(data) != end-start+1:
        raise ValueError("Byte-range response truncated")
    return bytes(data)


def members(tail: bytes) -> dict:
    end = tail.rfind(b"PK\x05\x06")
    if end < 0:
        raise ValueError("Missing ZIP directory")
    pos = tail.find(b"PK\x01\x02")
    result = {}
    while pos < end and tail[pos:pos+4] == b"PK\x01\x02":
        row = struct.unpack_from("<4s6H3L5H2L", tail, pos)
        name_length, extra_length, comment_length = row[10:13]
        name = tail[pos+46:pos+46+name_length].decode("utf-8")
        if name in result:
            raise ValueError("Duplicate ZIP member")
        result[name] = dict(method=row[4], crc32=row[7], compressed_size=row[8], size=row[9], offset=row[16])
        pos += 46+name_length+extra_length+comment_length
    return result


def data_offset(client: httpx.Client, url: str, member: dict) -> int:
    header = range_bytes(client, url, member["offset"], member["offset"]+29)
    values = struct.unpack("<4s5H3L2H", header)
    if values[0] != b"PK\x03\x04" or member["method"] != 8:
        raise ValueError("Unsupported source ZIP encoding")
    return member["offset"]+30+values[-2]+values[-1]


def identities(dbf: bytes, level: int) -> list[dict]:
    count = struct.unpack_from("<L", dbf, 4)[0]
    header, length = struct.unpack_from("<HH", dbf, 8)
    if count > 50000 or length > 4000 or len(dbf) < header+count*length:
        raise ValueError("Invalid source DBF bounds")
    fields, offset = [], 1
    for pos in range(32, header-1, 32):
        item = dbf[pos:pos+32]
        if item[0] == 13:
            break
        field = item[:11].split(b"\0")[0].decode("ascii")
        fields.append((field, offset, item[16]))
        offset += item[16]
    result = []
    for index in range(count):
        row = dbf[header+index*length:header+(index+1)*length]
        if row[0] == ord("*"):
            continue
        values = {name:row[start:start+size].decode("utf-8").strip() for name, start, size in fields}
        if values.get("adm3_name") == "City of Pasig" and values.get("adm3_pcode") == "PH1307403":
            result.append(dict(index=index, properties=values))
    if len(result) != (30 if level == 4 else 1):
        raise ValueError("Expected complete unique Pasig source identities")
    return result


def polygon_record(raw: bytes):
    record_number, words = struct.unpack_from(">2L", raw)
    body = raw[8:]
    if words*2 != len(body) or struct.unpack_from("<L", body)[0] not in (5, 15):
        raise ValueError("Invalid polygon shapefile record")
    count, points_count = struct.unpack_from("<2L", body, 36)
    if not 1 <= count <= 1000 or not 4 <= points_count <= 1_000_000:
        raise ValueError("Source polygon budget")
    indices = [*struct.unpack_from(f"<{count}L", body, 44), points_count]
    coordinates = [struct.unpack_from("<2d", body, 44+4*count+16*i) for i in range(points_count)]
    shells, holes = [], []
    for start, end in zip(indices, indices[1:]):
        ring = coordinates[start:end]
        if len(ring) < 4 or ring[0] != ring[-1]:
            raise ValueError("Unclosed source ring")
        polygon = Polygon(ring)
        if not polygon.is_valid or polygon.is_empty:
            raise ValueError("Invalid source ring; no automatic repair")
        # Shapefile exterior rings are clockwise; preserve their source vertices.
        (holes if polygon.exterior.is_ccw else shells).append((ring, polygon))
    if not shells:
        raise ValueError("Source polygon has no exterior")
    assigned = [[] for _ in shells]
    for ring, hole in holes:
        containing = [(area.area, i) for i, (_, area) in enumerate(shells) if area.covers(hole)]
        if not containing:
            raise ValueError("Orphan source hole")
        assigned[min(containing)[1]].append(ring)
    pieces = [Polygon(ring, assigned[i]) for i, (ring, _) in enumerate(shells)]
    result = pieces[0] if len(pieces) == 1 else MultiPolygon(pieces)
    if not result.is_valid or result.is_empty:
        raise ValueError("Invalid source polygon; no automatic repair")
    return result


def capture_shapes(client: httpx.Client, url: str, member: dict, shx: bytes, selected: list[dict], stem: str) -> list[dict]:
    targets = []
    for row in selected:
        offset, length = struct.unpack_from(">2L", shx, 100+row["index"]*8)
        targets.append((offset*2, length*2+8, row))
    last = max(offset+length for offset, length, _ in targets)
    start = data_offset(client, url, member)
    decoder, position, compressed_count = zlib.decompressobj(-15), 0, 0
    stored = {row["index"]:bytearray() for _, _, row in targets}
    compressed_path = DIRECTORY / (stem+".source-prefix.deflate")
    with client.stream("GET", url, headers={"Range":f"bytes={start}-{start+member['compressed_size']-1}"}) as response:
        response.raise_for_status()
        if response.status_code != 206 or not response.headers.get("content-range", "").startswith(f"bytes {start}-"):
            raise ValueError("Source shape range mismatch")
        with compressed_path.open("wb") as output:
            for chunk in response.iter_bytes(chunk_size=65536):
                compressed_count += len(chunk)
                if compressed_count > 192_000_000:
                    raise ValueError("Compressed source budget exceeded")
                output.write(chunk)
                expanded = decoder.decompress(chunk)
                if len(expanded) > 4_000_000:
                    raise ValueError("Source chunk expands beyond budget")
                for offset, length, row in targets:
                    left, right = max(offset, position), min(offset+length, position+len(expanded))
                    if right > left:
                        stored[row["index"]].extend(expanded[left-position:right-position])
                position += len(expanded)
                if position >= last:
                    break
    features = []
    for offset, length, row in targets:
        raw = bytes(stored[row["index"]])
        if len(raw) != length:
            raise ValueError("Selected source shape truncated")
        (DIRECTORY/f"{stem}-{row['index']}.record").write_bytes(raw)
        polygon = polygon_record(raw)
        features.append(dict(type="Feature", properties={**row["properties"], "source_record_index":row["index"],
            "source_record_sha256":hashlib.sha256(raw).hexdigest()}, geometry=mapping(polygon)))
    (DIRECTORY/(stem+".transfer.json")).write_text(json.dumps(dict(url=url, range_start=start,
        compressed_bytes=compressed_count, expanded_through=position, source_member=member,
        prefix_sha256=hashlib.sha256(compressed_path.read_bytes()).hexdigest(),
        note="Partial original ZIP-member stream; selected records are complete. Full member CRC is not claimed."),indent=2),encoding="utf-8")
    return features


def fetch() -> None:
    DIRECTORY.mkdir(exist_ok=True)
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        metadata_path = DIRECTORY/"hdx-metadata.json"
        if not metadata_path.exists():
            response = client.get(METADATA_URL); response.raise_for_status()
            metadata_path.write_bytes(response.content)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))["result"]
        if metadata["license_id"] != "cc-by-igo":
            raise ValueError("Dataset licence requires a new review")
        url = next(resource["url"] for resource in metadata["resources"] if resource["format"] == "SHP")
        tail_path = DIRECTORY/"hdx-zip-tail.bin"
        if not tail_path.exists():
            size = int(next(resource["size"] for resource in metadata["resources"] if resource["url"] == url))
            tail_path.write_bytes(range_bytes(client, url, size-131072, size-1))
        table = members(tail_path.read_bytes())
        collection = {}
        for level in (3, 4):
            stem = f"phl_admin{level}"
            for extension in ("dbf", "shx"):
                path = DIRECTORY/(stem+"."+extension)
                item = table[stem+"."+extension]
                if not path.exists():
                    start = data_offset(client, url, item)
                    packed = range_bytes(client, url, start, start+item["compressed_size"]-1)
                    path.write_bytes(zlib.decompress(packed, -15))
                raw = path.read_bytes()
                if len(raw) != item["size"] or zlib.crc32(raw) != item["crc32"]:
                    raise ValueError("Original source attribute/index CRC mismatch")
            selected = identities((DIRECTORY/(stem+".dbf")).read_bytes(), level)
            features = capture_shapes(client, url, table[stem+".shp"], (DIRECTORY/(stem+".shx")).read_bytes(), selected, stem)
            collection[str(level)] = dict(type="FeatureCollection", features=features)
            (DIRECTORY/f"pasig-cod-adm{level}.geojson").write_text(json.dumps(collection[str(level)],separators=(",", ":"))+"\n",encoding="utf-8")
            print(f"Captured {len(features)} complete Pasig ADM{level} shapes",flush=True)
        (DIRECTORY/"cod-capture-receipt.json").write_text(json.dumps(dict(dataset=metadata["title"],
            metadata_url=METADATA_URL, source_url=url, licence=metadata["license_title"],
            retrieved_at=datetime.now(timezone.utc).isoformat(), publisher="OCHA Philippines / HDX",
            source=metadata.get("dataset_source"), source_geometry_modified=False),indent=2),encoding="utf-8")


if __name__ == "__main__":
    fetch()
