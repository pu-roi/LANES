import struct
from typing import List, Any
from pydantic import BaseModel

# ==========================================
# 1. EWKB Binary Geometry Parsers
# ==========================================

def parse_ewkb_point(data: bytes) -> List[float]:
    """
    Parses a PostGIS EWKB (Extended Well-Known Binary) Point into [longitude, latitude].
    """
    byte_order = '<' if data[0] == 1 else '>'
    geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
    
    offset = 5
    # If EWKB has SRID flag (0x20000000)
    if geom_type & 0x20000000:
        offset += 4
        
    # Read X and Y (8 bytes each, double precision float)
    x, y = struct.unpack(f"{byte_order}dd", data[offset:offset+16])
    return [x, y]


def parse_ewkb_polygon(data: bytes) -> List[List[List[float]]]:
    """
    Parses a PostGIS EWKB (Extended Well-Known Binary) Polygon into a list of coordinate rings.
    """
    byte_order = '<' if data[0] == 1 else '>'
    geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
    
    offset = 5
    # If EWKB has SRID flag (0x20000000)
    if geom_type & 0x20000000:
        offset += 4
        
    num_rings = struct.unpack(f"{byte_order}I", data[offset:offset+4])[0]
    offset += 4
    
    rings = []
    for _ in range(num_rings):
        num_points = struct.unpack(f"{byte_order}I", data[offset:offset+4])[0]
        offset += 4
        points = []
        for _ in range(num_points):
            x, y = struct.unpack(f"{byte_order}dd", data[offset:offset+16])
            offset += 16
            points.append([x, y])
        rings.append(points)
    return rings


def parse_ewkb_linestring(data: bytes) -> List[List[float]]:
    """
    Parses a PostGIS EWKB (Extended Well-Known Binary) LineString into [[longitude, latitude], ...].
    """
    byte_order = '<' if data[0] == 1 else '>'
    geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
    
    offset = 5
    # If EWKB has SRID flag (0x20000000)
    if geom_type & 0x20000000:
        offset += 4
        
    num_points = struct.unpack(f"{byte_order}I", data[offset:offset+4])[0]
    offset += 4
    
    points = []
    for _ in range(num_points):
        x, y = struct.unpack(f"{byte_order}dd", data[offset:offset+16])
        offset += 16
        points.append([x, y])
    return points


def parse_ewkb_multilinestring(data: bytes) -> List[List[List[float]]]:
    """
    Parses a PostGIS EWKB (Extended Well-Known Binary) MultiLineString into a list of LineStrings.
    """
    byte_order = '<' if data[0] == 1 else '>'
    geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
    
    offset = 5
    # If EWKB has SRID flag (0x20000000)
    if geom_type & 0x20000000:
        offset += 4
        
    num_lines = struct.unpack(f"{byte_order}I", data[offset:offset+4])[0]
    offset += 4
    
    lines = []
    for _ in range(num_lines):
        # Skip the byte order (1 byte) and geometry type (4 bytes) of each LineString
        offset += 5
        num_points = struct.unpack(f"{byte_order}I", data[offset:offset+4])[0]
        offset += 4
        
        points = []
        for _ in range(num_points):
            x, y = struct.unpack(f"{byte_order}dd", data[offset:offset+16])
            offset += 16
            points.append([x, y])
        lines.append(points)
    return lines


# ==========================================
# 2. GeoJSON Pydantic Helper Schemas
# ==========================================

class PointGeometry(BaseModel):
    """
    GeoJSON Point geometry.
    """
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class LineStringGeometry(BaseModel):
    """
    GeoJSON LineString geometry.
    """
    type: str = "LineString"
    coordinates: List[List[float]]  # Points -> [longitude, latitude]


class MultiLineStringGeometry(BaseModel):
    """
    GeoJSON MultiLineString geometry.
    """
    type: str = "MultiLineString"
    coordinates: List[List[List[float]]]  # Lines -> Points -> [longitude, latitude]


class PolygonGeometry(BaseModel):
    """
    GeoJSON Polygon geometry.
    """
    type: str = "Polygon"
    coordinates: List[List[List[float]]]  # Rings -> Points -> [longitude, latitude]


class MultiPolygonGeometry(BaseModel):
    """
    GeoJSON MultiPolygon geometry.
    """
    type: str = "MultiPolygon"
    coordinates: List[List[List[List[float]]]]  # Polygons -> Rings -> Points -> [longitude, latitude]


class GeometryCollectionGeometry(BaseModel):
    """
    GeoJSON GeometryCollection geometry.
    """
    type: str = "GeometryCollection"
    geometries: List[Any]
