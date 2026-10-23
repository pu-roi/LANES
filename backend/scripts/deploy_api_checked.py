"""Deploy the API only, execute a credential-isolated read check, then promote.

Runs in Cloud SDK/Cloud Build using stdlib only. Existing worker specifications,
models, automation settings and application records are never modified.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.news_reader_release import production_reader_environment


def check_job(service: dict, *, name: str, image: str, candidate: str, baseline: str) -> dict:
    template = service['spec']['template']
    spec = template['spec']
    allowed = {'DATABASE_URL', 'SECRET_KEY', 'ENVIRONMENT', 'ALGORITHM'}
    env = [entry for entry in spec['containers'][0].get('env', []) if entry['name'] in allowed]
    if not {'DATABASE_URL', 'SECRET_KEY'}.issubset({entry['name'] for entry in env}):
        raise ValueError('reader_check_credentials_missing')
    env += [{'name': key, 'value': value} for key, value in production_reader_environment().items()]
    annotations = {key: value for key, value in template.get('metadata', {}).get('annotations', {}).items()
                   if key in {'run.googleapis.com/cloudsql-instances', 'run.googleapis.com/vpc-access-connector',
                              'run.googleapis.com/vpc-access-egress', 'run.googleapis.com/network-interfaces'}}
    task = {'serviceAccountName': spec['serviceAccountName'], 'maxRetries': 0, 'timeoutSeconds': '180',
            'containers': [{'image': image, 'command': ['python'],
                'args': ['-m', 'scripts.check_news_reader', '--candidate', candidate, '--baseline', baseline],
                'env': env, 'resources': {'limits': {'cpu': '1', 'memory': '1Gi'}}}]}
    return {'apiVersion': 'run.googleapis.com/v1', 'kind': 'Job', 'metadata': {'name': name},
            'spec': {'template': {'metadata': {'annotations': annotations},
                                 'spec': {'taskCount': 1, 'template': {'spec': task}}}}}


def deploy(*, project: str, region: str, service: str, image: str, suffix: str,
           gcloud: str = 'gcloud') -> dict:
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,42}', suffix):
        raise ValueError('reader_release_suffix_invalid')
    def run(args: list[str]) -> dict:
        result = subprocess.run([gcloud, *args, '--project=' + project, '--format=json', '--quiet'],
                                capture_output=True, timeout=900)
        if result.returncode:
            # gcloud may render credential-bearing resource bodies. Do not echo them.
            raise RuntimeError('reader_release_command_failed:' + ':'.join(args[:3]))
        return json.loads(result.stdout or b'{}')
    previous = run(['run', 'services', 'describe', service, '--region=' + region])
    baseline = previous['status']['url']
    variables = ','.join(key + '=' + value for key, value in production_reader_environment().items())
    run(['run', 'deploy', service, '--image=' + image, '--no-traffic', '--tag=reader-check',
         '--revision-suffix=' + suffix, '--update-env-vars=' + variables, '--region=' + region])
    staged = run(['run', 'services', 'describe', service, '--region=' + region])
    revision = service + '-' + suffix
    target = next(t['url'] for t in staged['status']['traffic']
                  if t.get('tag') == 'reader-check' and t.get('revisionName') == revision)
    job = service + '-reader-' + suffix
    if len(job) > 63:
        raise ValueError('reader_check_job_name_invalid')
    document = check_job(staged, name=job, image=image, candidate=target, baseline=baseline)
    descriptor, filename = tempfile.mkstemp(suffix='.json')
    try:
        # Private descriptor; it contains existing backend credentials, never log it.
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(document, stream)
        run(['run', 'jobs', 'replace', filename, '--region=' + region])
    finally:
        Path(filename).unlink(missing_ok=True)
    run(['run', 'jobs', 'execute', job, '--wait', '--region=' + region])
    # A competing release must not be overwritten after our probe completes.
    current = run(['run', 'services', 'describe', service, '--region=' + region])
    def serving(value: dict) -> list[tuple[str, int]]:
        return sorted((t.get('revisionName', ''), t['percent']) for t in value['status']['traffic'] if t.get('percent'))
    if serving(current) != serving(previous):
        raise RuntimeError('reader_release_serving_revision_changed')
    run(['run', 'services', 'update-traffic', service, '--to-revisions=' + revision + '=100', '--region=' + region])
    return {'status': 'reader_release_promoted', 'revision': revision, 'check_job': job,
            'image': image, 'provider_requests': 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('project', 'region', 'service', 'image', 'suffix'):
        parser.add_argument('--' + field, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(deploy(**vars(args))))
    except Exception as error:
        print(json.dumps({'status': 'reader_release_failed', 'error_type': type(error).__name__}))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
