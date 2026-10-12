"""Generated construction remains strictly contained; source assets never move."""
import pytest
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon, box, mapping
from shapely.affinity import scale
from app.crud.news_evaluation import canonical_sha256
from app.services.barangay_boundary_service import get_barangay_boundary_provider
from app.services.generated_corridor_geometry_service import generated_corridor_intersection
from app.services.noah_vector_catalog_service import metric_geometry, X_METRES, Y_METRES


def test_real_santo_domingo_corner_constructs_valid_contained_corridor_without_source_changes():
    # Source way 43080699/60449493, clipped original Santo Domingo core used by
    # both immutable replay claims. No database/provider/publication operation.
    parent = get_barangay_boundary_provider().records[("quezon city","santo domingo")][1]
    core = LineString([(121.0017254,14.6327076),(121.0023183,14.6329815)])
    buffer = scale(metric_geometry(core).buffer(25.0),xfact=1/X_METRES,yfact=1/Y_METRES,origin=(0,0))
    originals = [canonical_sha256(mapping(g)) for g in (parent,core,buffer)]
    raw = buffer.intersection(parent)
    assert not parent.covers(raw) and parent.covers(core)
    result = generated_corridor_intersection(buffer,parent,core)
    assert result.is_valid and result.area > 0
    assert parent.covers(result) and buffer.covers(result) and result.covers(core)
    assert result.difference(parent).is_empty
    assert set(core.coords).issubset(set(result.exterior.coords))
    assert [canonical_sha256(mapping(g)) for g in (parent,core,buffer)] == originals
    assert canonical_sha256(mapping(result)) == canonical_sha256(mapping(generated_corridor_intersection(buffer,parent,core)))


def test_contained_input_keeps_exact_output_coordinates():
    buffer,parent,core = box(0,0,1,1),box(-1,-1,2,2),LineString([(0.2,0.5),(0.8,0.5)])
    expected = buffer.intersection(parent)
    assert generated_corridor_intersection(buffer,parent,core).equals_exact(expected,0)


def test_an_original_outside_vertex_is_never_rounded_into_the_parent(monkeypatch):
    import math,shapely
    buffer=box(0,0,math.nextafter(1.0,math.inf),1)
    parent=box(0,0,1,1)
    core=LineString([(0.2,0.5),(0.8,0.5)])
    original=shapely.intersection
    # Simulate a bad constructor retaining an original outside buffer vertex.
    # Even an adjacent representable coordinate must not repair that input.
    monkeypatch.setattr(shapely,'intersection',lambda a,b,**kwargs:buffer if a is buffer else original(a,b,**kwargs))
    with pytest.raises(ValueError,match='generated_corridor_precision_unresolved'):
        generated_corridor_intersection(buffer,parent,core)


def test_holes_and_disconnected_components_are_not_dropped_or_joined():
    parent = MultiPolygon([Polygon([(0,0),(2,0),(2,2),(0,2)],
        [[(0.4,0.4),(0.6,0.4),(0.6,0.6),(0.4,0.6)]]),box(3,0,5,2)])
    buffer=box(-1,-1,6,3)
    core=MultiLineString([[(0.8,1),(1.2,1)],[(3.8,1),(4.2,1)]])
    result=generated_corridor_intersection(buffer,parent,core)
    assert result.geom_type=='MultiPolygon' and len(result.geoms)==2
    assert sum(len(part.interiors) for part in result.geoms)==1
    assert result.equals_exact(buffer.intersection(parent),0)


@pytest.mark.parametrize('core',[LineString([(0.5,0.5),(1.5,0.5)]),
                                LineString([(0.5,0.5),(0.8,0.5)])])
def test_genuine_unsupported_core_or_empty_intersection_fails_closed(core):
    parent=box(0,0,1,1)
    buffer=box(0,0,2,1) if core.coords[-1][0]>1 else box(2,2,3,3)
    with pytest.raises(ValueError,match='generated_corridor_precision_unresolved'):
        generated_corridor_intersection(buffer,parent,core)
