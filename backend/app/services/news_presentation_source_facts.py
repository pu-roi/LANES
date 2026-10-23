"""Read exact saved news facts for the restricted active-only presentation set."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.news_publication import NewsPublicationError
from app.models.news import NewsExtractionRun
from app.schemas.historical_news import HistoricalNewsMetadata
from app.services.news_ner_durable.contracts import sha


def source_facts(db: Session, metadata: dict[int, HistoricalNewsMetadata]) -> dict[int, dict]:
    from app.services.news_gma_active_outputs import DATASET
    selected = {key: m for key, m in metadata.items() if m.dataset_id == DATASET}
    if not selected:
        return {}
    runs = {r.id: r for r in db.scalars(select(NewsExtractionRun).where(
        NewsExtractionRun.id.in_({m.run_id for m in selected.values()})))}
    hashes = {key: sha(run.result) for key, run in runs.items()}
    values = {}
    for event_id, m in selected.items():
        run = runs.get(m.run_id)
        if (run is None or run.status != 'completed' or hashes[run.id] != m.result_sha256
                or run.article_version_id != m.article_version_id):
            raise NewsPublicationError('presentation_source_result_changed')
        groups = [g for g in run.result['projection']['groups'] if g['group_id'] == m.group_id
                  and g['disposition'] == 'projected']
        if len(groups) != 1:
            raise NewsPublicationError('presentation_source_group_changed')
        claim = run.result['claims'][groups[0]['claim_index']]
        # Gauge category is retained in storage. The read projection must not
        # turn its conventional gauge conversion into a measured source value.
        depth = claim['depth_raw'] or claim['depth_canonical']
        values[event_id] = {'depth': depth, 'depth_inches': claim['depth_inches'],
            'depth_meters': claim['depth_meters'], 'depth_formatted': claim['depth_formatted'] or depth,
            'location_label': ', '.join(x for x in (m.label, m.canonical_barangay, m.canonical_city) if x)}
    return values
