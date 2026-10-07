"""Read public place activity without loading or exposing community post content."""
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def read_trending_hotspots(
    db: Session, *, now: datetime, cutoff: datetime, half_life_hours: int,
    minimum_contributors: int, cluster_radius_meters: int, limit: int,
) -> list[dict[str, Any]]:
    rows = db.execute(text(r"""
        WITH candidates AS (
            SELECT p.id, p.user_id,
                COALESCE(NULLIF(trim(r.human_readable_location), ''), NULLIF(trim(p.location_tag), '')) AS name,
                CASE WHEN r.geometry IS NOT NULL THEN ST_PointOnSurface(r.geometry)
                     ELSE ST_SetSRID(ST_MakePoint(p.location_lng, p.location_lat), 4326) END AS point,
                LEAST(p.created_at, COALESCE(r.created_at, p.created_at)) AS activity_at
            FROM community_posts p
            LEFT JOIN flood_reports r ON r.id = p.flood_report_id
            JOIN users u ON u.id = p.user_id
            WHERE p.deleted_at IS NULL AND p.hidden_at IS NULL
              AND u.deleted_at IS NULL AND u.is_active = true
              AND p.created_at >= :cutoff AND p.created_at <= :now
              AND (p.flood_report_id IS NULL OR
                   (r.id IS NOT NULL AND r.is_public = true AND r.deleted_at IS NULL
                    AND r.status IN ('pending', 'approved') AND r.created_at >= :cutoff AND r.created_at <= :now))
        ), located AS (
            SELECT *, lower(regexp_replace(trim(name), '\s+', ' ', 'g')) AS place_key
            FROM candidates
            WHERE name IS NOT NULL AND point IS NOT NULL AND NOT ST_IsEmpty(point)
              AND ST_Y(point) BETWEEN -90 AND 90 AND ST_X(point) BETWEEN -180 AND 180
        ), clustered AS (
            SELECT *, ST_ClusterDBSCAN(ST_Transform(point, 3857), :cluster_radius_meters, 1)
                OVER (PARTITION BY place_key ORDER BY id) AS cluster_id
            FROM located
        ), contributors AS (
            SELECT place_key, cluster_id, user_id, count(*) AS post_count, max(activity_at) AS latest_at
            FROM clustered GROUP BY place_key, cluster_id, user_id
        ), totals AS (
            SELECT place_key, cluster_id, sum(post_count)::int AS post_count, count(*)::int AS contributor_count,
                sum(power(2.0, -extract(epoch FROM (:now - latest_at)) / (3600.0 * :half_life_hours))) AS score
            FROM contributors GROUP BY place_key, cluster_id HAVING count(*) >= :minimum_contributors
        ), representatives AS (
            SELECT *, row_number() OVER (PARTITION BY place_key, cluster_id ORDER BY activity_at DESC, id DESC) AS position
            FROM clustered
        )
        SELECT c.id::text AS id, regexp_replace(trim(c.name), '\s+', ' ', 'g') AS name,
            ST_Y(c.point) AS latitude, ST_X(c.point) AS longitude,
            t.post_count, t.contributor_count, c.activity_at AS latest_post_at
        FROM totals t JOIN representatives c USING (place_key, cluster_id)
        WHERE c.position = 1
        ORDER BY t.score DESC, c.activity_at DESC, c.id DESC
        LIMIT :limit
    """), {
        "now": now, "cutoff": cutoff, "half_life_hours": half_life_hours,
        "minimum_contributors": minimum_contributors,
        "cluster_radius_meters": cluster_radius_meters, "limit": limit,
    })
    return [dict(row) for row in rows.mappings()]
