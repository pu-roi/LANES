"""Independently configured inference/reference identities, without model loading."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from app.services.news_ner.bundle import digest, verify_bundle
from app.services.news_ner.contract import object_sha
from app.services.news_ner_runtime.protocol import code_bindings
from app.services.news_processing_identity import native_pipeline_version
from app.services.philippine_location_service import NATIONWIDE_PSGC_CSV, PhilippineLocationService
from .contracts import NerEvidenceError, PROJECTION_VERSION, SOURCE_VERSION, sha
from .locality import Catalog


def normalizer_bindings() -> dict:
    services=Path(__file__).resolve().parent.parent
    files=[*sorted(Path(__file__).parent.glob('*.py')),
           services.parent/'crud/news_processing.py',
           *(services/name for name in ('philippine_location_service.py','taglish_extraction_service.py',
                                       'flood_depth.py','news_evidence_policy.py','news_evaluation_service.py',
                                       'news_claim_auditor.py','news_processing_identity.py')),
           *(services.parent/'schemas'/name for name in ('news_ner_result.py','news_extraction.py','news_audit.py','news_ner_preview.py'))]
    files += [services.parent/'crud'/name for name in ('news.py', 'news_evaluation.py')]
    files += [services/name for name in ('news_discovery_service.py','news_feed_service.py',
        'news_road_placement_service.py','news_placement_preview_service.py','news_pipeline_service.py',
        'news_publication_service.py')]
    files += [services/name for name in ('article_road_context_service.py','article_road_match_service.py',
        'news_locality_anchor_service.py','placement_geometry_service.py','noah_road_prediction_service.py',
        'noah_vector_catalog_service.py','pasig_historical_service.py','news_placement_display_service.py',
        'news_road_corridor_service.py','barangay_boundary_service.py')]
    files += [services/name for name in ('news_footprint_worker_service.py','news_estimated_road_service.py',
        'operational_footprint_service.py','operational_footprint_evidence_service.py','generated_corridor_geometry_service.py')]
    files += [services.parent/'crud/news_publication.py', services.parent/'schemas/news_publication.py',
              services.parent/'schemas/news_placement.py']
    return {p.relative_to(services.parent).as_posix():digest(p) for p in files}


@dataclass(frozen=True)
class TrustedAssets:
    """Create from operator-pinned assets, never from an extraction JSON object."""
    _manifest: dict
    _code: dict
    _normalizer: dict
    _manifest_sha256: str
    catalog: Catalog

    @property
    def manifest(self) -> dict:
        return deepcopy(self._manifest)

    @property
    def pipeline_version(self) -> str:
        return native_pipeline_version(self._manifest)

    @property
    def provenance(self) -> dict:
        m=self._manifest
        return {'runtime':m['runtime']['version'],'model':m['model']['name'],
                'bundle_sha256':m['model']['bundle_sha256'],'model_manifest_sha256':m['model']['model_manifest_sha256'],
                'resource_manifest_sha256':m['model']['resource_manifest_sha256'],'tokenizer_sha256':m['tokenizer']['sha256'],
                'code_sha256':m['runtime']['code_sha256'],'location_rules':m['location_rules']['version'],
                'location_method':'combined','context_rules':m['context_rules']['version']}

    def validate(self) -> None:
        try:
            services=Path(__file__).resolve().parent.parent
            if (sha(self._manifest)!=self._manifest_sha256 or normalizer_bindings()!=self._normalizer or code_bindings(services)!=self._code
                    or sha(self._normalizer)!=self._manifest['projection']['code_sha256']
                    or sha(self._normalizer)!=self._manifest['source_check']['code_sha256']
                    or object_sha(self._code)!=self._manifest['runtime']['code_sha256']
                    or digest(NATIONWIDE_PSGC_CSV)!=self._manifest['geography']['psgc_sha256']):
                raise ValueError('assets_changed')
            if 'placement' in self._manifest['geography'] and placement_identity() != self._manifest['geography']['placement']:
                raise ValueError('placement_assets_changed')
        except (ValueError,KeyError,OSError,TypeError) as exc:
            raise NerEvidenceError('ner_assets_unavailable') from exc


def load_trusted_assets(bundle: Path, expected_bundle_sha256: str, *, expected_worker_code_sha256: str) -> TrustedAssets:
    try:
        bundle_identity=verify_bundle(bundle,expected_bundle_sha256)
        services=Path(__file__).resolve().parent.parent;code=code_bindings(services)
        if object_sha(code)!=expected_worker_code_sha256:raise ValueError('runtime_identity_mismatch')
        normalizer=normalizer_bindings();normalizer_sha=sha(normalizer)
        manifest={'model':{'name':'v19-control-seed-0','bundle_sha256':expected_bundle_sha256,
                          'model_manifest_sha256':bundle_identity['model_manifest_sha256'],
                          'resource_manifest_sha256':bundle_identity['resource_manifest_sha256']},
                  'tokenizer':{'sha256':digest(bundle/'model/tokenizer')},
                  'runtime':{'version':'lanes-ner-subprocess-v1','code_sha256':expected_worker_code_sha256},
                  'location_rules':{'version':'lanes-location-repair-v40+v44','method':'combined'},
                  'context_rules':{'version':'lanes-context-association-v42'},
                  'projection':{'version':PROJECTION_VERSION,'code_sha256':normalizer_sha},
                  'source_check':{'version':SOURCE_VERSION,'code_sha256':normalizer_sha},
                  'geography':{'psgc_sha256':digest(NATIONWIDE_PSGC_CSV),'scope':'metro_manila',
                               'lookup_code_sha256':digest(services/'philippine_location_service.py')}}
        return TrustedAssets(manifest,code,normalizer,sha(manifest),Catalog(PhilippineLocationService(NATIONWIDE_PSGC_CSV)))
    except (ValueError,TypeError,KeyError,OSError) as exc:
        raise NerEvidenceError('ner_assets_unavailable') from exc


def placement_identity() -> dict:
    from app.services.news_road_placement_service import get_news_road_placement_provider
    from app.services.news_placement_preview_service import get_news_placement_preview_service
    return {'roads':get_news_road_placement_provider().revision,
            'preview':get_news_placement_preview_service().revision}


def with_placement_assets(trusted: TrustedAssets) -> TrustedAssets:
    trusted.validate()
    manifest = trusted.manifest
    manifest['geography']['placement'] = placement_identity()
    return TrustedAssets(manifest,trusted._code,trusted._normalizer,sha(manifest),trusted.catalog)
