"""Validate a pinned exported receipt locally; no network or database access."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from app.services.news_claim_auditor import AuditorConfig
from app.services.news_gemini_receipts import replay_bundle
from app.services.news_ner_durable.resolution import ResolutionError

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    args=parser.parse_args()
    try:
        raw=args.receipt.read_bytes()
        if len(raw)>1_048_576:raise ResolutionError('native_resolution_receipt_too_large')
        bundle=json.loads(raw)
        config=AuditorConfig(provider='gemini',model='gemini-3.5-flash-lite',gemini_api_key='offline-only')
        result=replay_bundle(bundle,args.sha256,config=config)
    except ResolutionError as exc:
        result={'status':'rejected','error_code':exc.code,'diagnostic':getattr(exc,'provider_diagnostic',{}),'provider_requests':0}
    except (ValueError,OSError,TypeError):
        result={'status':'rejected','error_code':'native_resolution_receipt_invalid','provider_requests':0}
    print(json.dumps(result,sort_keys=True))
    return 0 if result['status']=='evidence_references_passed' else 1

if __name__=='__main__':raise SystemExit(main())
