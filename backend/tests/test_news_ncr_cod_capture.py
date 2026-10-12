"""Bounded source-region selection, not geometry qualification or activation."""
import struct

import pytest
from scripts.fetch_news_ncr_cod_boundaries import source_rows


def dbf(rows):
    fields = [("adm1_pcode", 4), ("adm1_name", 40), ("adm3_name", 40)]
    header_size = 32 + 32 * len(fields) + 1
    length = 1 + sum(size for name, size in fields)
    header = bytearray(32)
    struct.pack_into("<L", header, 4, len(rows))
    struct.pack_into("<HH", header, 8, header_size, length)
    for name, size in fields:
        field = bytearray(32)
        field[:len(name)] = name.encode()
        field[16] = size
        header.extend(field)
    header.append(13)
    body = b"".join(b" " + b"".join(row.get(name, "").encode().ljust(size, b" ") for name, size in fields) for row in rows)
    return bytes(header) + body


def test_only_exact_ncr_code_and_label_are_selected_with_original_record_index():
    values = dbf([dict(adm1_pcode="PH13", adm1_name="National Capital Region (NCR)", adm3_name="City of Malabon"),
        dict(adm1_pcode="PH03", adm1_name="Central Luzon", adm3_name="City of Malabon"),
        dict(adm1_pcode="PH13", adm1_name="Unmatched region", adm3_name="City of Malabon")])
    selected = source_rows(values)
    assert len(selected) == 1 and selected[0]["index"] == 0
    assert selected[0]["properties"]["adm3_name"] == "City of Malabon"


def test_truncated_attribute_file_cannot_supply_partially_read_source_identity():
    values = dbf([dict(adm1_pcode="PH13", adm1_name="National Capital Region (NCR)")])
    with pytest.raises(ValueError, match="bounded source"):
        source_rows(values[:-1])
