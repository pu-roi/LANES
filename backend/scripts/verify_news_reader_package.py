"""Offline image gate: authenticate the saved-reader manifest without DB/provider access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from app.services.news_native_read_context import configured_native_read_context
from app.services.news_reader_release import READER_MANIFEST_SHA256, READER_SOURCE_PATH


def verify_package(path: Path, pin: str = READER_MANIFEST_SHA256) -> dict:
    with patch.dict('os.environ', {
        'LANES_NEWS_NATIVE_READ_CONTEXT': str(path),
        'LANES_NEWS_NATIVE_READ_CONTEXT_SHA256': pin,
    }):
        context = configured_native_read_context()
    if context is None:
        raise ValueError('news_reader_package_missing')
    return {'status': 'reader_package_verified', 'manifest_sha256': pin,
            'pipeline_version': context.pipeline_version,
            'database_writes': 0, 'provider_requests': 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', type=Path, default=READER_SOURCE_PATH)
    args = parser.parse_args()
    try:
        print(json.dumps(verify_package(args.path)))
    except Exception:
        print(json.dumps({'status': 'reader_package_invalid'}))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
