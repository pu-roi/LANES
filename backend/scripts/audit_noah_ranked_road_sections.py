"""Read-only ranking of real OSM between-intersection road sections with NOAH.

This diagnostic does not use a recent article and cannot create a Flood Zone.
Run with the locally ignored Metro Manila PBF and three NOAH ZIP archives.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import LineString, shape
from shapely.ops import transform

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.article_road_match_service import load_bounded_osm_roads, split_named_road_at_intersections
from app.services.noah_road_prediction_service import RoadSectionEvidence, rank_noah_road_sections
from scripts.audit_noah_road_intersections import hazard_overlap, local_projector


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("osm_pbf", type=Path)
    parser.add_argument("noah_zips", type=Path, nargs=3)
    parser.add_argument("--road", default="C. Raymundo Avenue")
    parser.add_argument("--city-boundary", type=Path, required=True)
    parser.add_argument("--bbox", type=float, nargs=4, required=True)
    args = parser.parse_args()
    boundary = shape(json.loads(args.city_boundary.read_text(encoding="utf-8-sig")))
    ways = load_bounded_osm_roads(str(args.osm_pbf), tuple(args.bbox))
    sections = split_named_road_at_intersections(
        args.road, ways, boundary, f"local-osm-pbf:{args.osm_pbf.name}",
    )
    if not sections:
        raise ValueError("No between-intersection sections matched the named road and city")
    evidence = [RoadSectionEvidence(
        section_id=section.section_id,
        metric_centerline=transform(local_projector(), LineString(section.centerline_geojson["coordinates"])),
        osm_source_id=section.source_id,
        bounded_road_section=not section.ambiguous_carriageway,
    ) for section in sections]
    prediction = rank_noah_road_sections(
        evidence, dict(zip((5, 25, 100), args.noah_zips)), hazard_overlap,
    )
    by_id = {section.section_id: section for section in sections}
    print(f"Named road: {args.road}; mapped between-intersection sections: {len(sections)}")
    print(f"Alternative-carriageway sections: {sum(section.ambiguous_carriageway for section in sections)}")
    for item in prediction.ranked_sections[:10]:
        section = by_id[item.section_id]
        fractions = ", ".join(f"{period}yr={item.modeled_overlap_fraction[period]:.2f}"
                              for period in (5, 25, 100))
        print(f"{item.section_id}: {section.end_cross_streets}; {fractions}; "
              f"high-class={item.average_class_fraction[3]:.2f}; "
              f"ambiguous_carriageway={section.ambiguous_carriageway}")
    print(f"Predicted location: {prediction.predicted_section_id or 'unresolved'} ({prediction.reason})")
    print("Status: historical susceptibility only; current flood evidence and routing gates not evaluated")


if __name__ == "__main__":
    main()
