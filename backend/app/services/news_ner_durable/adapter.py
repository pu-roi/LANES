"""Build and verify native durable evidence without inference, IO or DB writes."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from app.schemas.news_ner_result import NewsNerResult, parse_saved_result
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner.projection import LIMITATIONS, project
from app.services.news_ner_runtime.protocol import verify_result
from .assets import TrustedAssets
from .contracts import NerEvidenceError, PROJECTION_VERSION, RunEvidence, sha
from .projection import project_observations

ENRICHMENT_FIELDS=frozenset({'ranked_location','road_placement','placement_preview'})


def build_native_result(context: RunEvidence, inference: dict, trusted: TrustedAssets, *, extracted_at: datetime) -> NewsNerResult:
    source=context.source();trusted.validate()
    if context.pipeline_version!=trusted.pipeline_version:
        raise NerEvidenceError('ner_configuration_invalid')
    request=source.runtime_request(context.input_fingerprint)
    try:
        if extracted_at.utcoffset() is None:raise ValueError('aware_extraction_clock_required')
        if inference['provenance']!=trusted.provenance:raise ValueError('runtime_provenance_mismatch')
        verify_result(request,inference,trusted.manifest['model']['bundle_sha256'],trusted._code)
        measurements=inference['measurements']
        if (set(measurements)!={'extraction_seconds','peak_worker_rss_bytes'}
                or type(measurements['extraction_seconds']) not in (float,int) or not 0<=measurements['extraction_seconds']<=60
                or type(measurements['peak_worker_rss_bytes']) is not int or measurements['peak_worker_rss_bytes']<0):
            raise ValueError('invalid_measurements')
        graph=inference['graph'];proposal=inference['proposal']
        claims,projection=project_observations(source,graph,trusted.catalog)
        limitations=[v for v in LIMITATIONS if v not in {'preview_only_not_verified_flood_data','no_database_history_or_map_policy_applied'}]
        limitations+=['source_consistency_not_field_verification','publication_and_geometry_gates_not_applied']
        result=NewsNerResult(schema_version='lanes-news-ner-result-v1',processing_method='ner_rules_v1',
            article_id=context.article_id,canonical_url=source.canonical_url,is_metadata_only=False,
            processed_text_length=len(source.article_text),claims=claims,extracted_at=extracted_at,
            extractor_version=PROJECTION_VERSION,errors=[],source={'article_version_id':context.article_version_id,
                'input_fingerprint':context.input_fingerprint,'canonical_url':source.canonical_url,'text_field':'article_text',
                'text_sha256':request['text_sha256'],'published_at':context.input_snapshot['published_at'],
                'publication_timezone_known':source.publication_evidence.timezone_known},
            provenance={'manifest':trusted.manifest,'manifest_sha256':sha(trusted.manifest),'runtime':deepcopy(inference['provenance'])},
            native={'neural_mentions':proposal['neural_mentions'],'effective_mentions':proposal['effective_mentions'],
                    'proposals':proposal['proposals'],'abstentions':proposal['abstentions'],'graph':graph,
                    'groups':project({**request,'mentions':proposal['effective_mentions']},graph)},
            projection=projection.model_dump(mode='json'),measurements=measurements,limitations=limitations)
        # Enforce C1's exact public JSON representation and response bound too.
        return parse_saved_result('ner_rules_v1',result)
    except NerEvidenceError:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        raise NerEvidenceError('ner_result_contract_invalid') from exc


def verify_saved_result(context: RunEvidence, saved: object, trusted: TrustedAssets) -> NewsNerResult:
    """Recompute extraction facts; geometry enrichment remains a separate gate."""
    context.source();trusted.validate()
    try:
        result=parse_saved_result(context.mode,saved)
        if not isinstance(result,NewsNerResult):raise ValueError('native_result_required')
        request=context.source().runtime_request(context.input_fingerprint)
        proposal=from_neural_mentions({**request,'mentions':[m.model_dump(mode='json') for m in result.native.neural_mentions]})['proposal']
        expected=build_native_result(context,{'proposal':proposal,'graph':result.native.graph.model_dump(mode='json',by_alias=True),
            'provenance':result.provenance['runtime'],'measurements':result.measurements},trusted,extracted_at=result.extracted_at)
        resolution_identity = trusted.manifest['projection'].get('llm_resolution')
        if resolution_identity is not None:
            from .resolution import apply_resolution
            expected = apply_resolution(context.source(),expected,result.provenance['llm_resolution'],trusted.catalog,resolution_identity)
        elif 'llm_resolution' in result.provenance:
            raise ValueError('unconfigured_native_resolution')
        actual_json=result.model_dump(mode='json',by_alias=True);expected_json=expected.model_dump(mode='json',by_alias=True)
        if result.read_projection is not None:
            from .read_projection import build_read_projection
            expected_json['read_projection'] = build_read_projection(context.source(), expected, trusted.catalog).model_dump(mode='json')
        # Compare the whole artifact. Only the existing placement fields may be
        # enriched downstream; their full values remain in the final claim hash.
        for claim in actual_json['claims']:
            for key in ENRICHMENT_FIELDS:claim[key]=None
        if actual_json!=expected_json:raise ValueError('native_recomputation_mismatch')
        return result
    except NerEvidenceError:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as exc:
        raise NerEvidenceError('ner_result_contract_invalid') from exc
