"""Deploy and explicitly dispatch only the unscheduled archive worker.

Use an ignored private receipt directory. Images and config are immutable pins;
every dispatch is claimed before the API call and is never automatically retried.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from uuid import uuid4

JOB = 'lanes-news-history-seed'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('deploy', 'run', 'status', 'logs', 'disable'))
    parser.add_argument('--project', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--mode', choices=('inspect','register','preflight','process','preview','apply','batch'), default='inspect')
    parser.add_argument('--batch', type=int, default=0)
    parser.add_argument('--execution')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = args.receipts.resolve()
    if (not output.is_relative_to(root/'data') or output == root/'data'
            or not re.fullmatch(r'[a-f0-9]{64}', args.config_sha256)
            or not re.fullmatch(r'[a-z0-9.\-/:]+@sha256:[a-f0-9]{64}', args.image)):
        parser.error('Private receipts and immutable image/config pins are required')
    if subprocess.run(['git','check-ignore','--quiet','--',str(output)],cwd=root).returncode:
        parser.error('Receipt directory must be ignored')
    output.mkdir(parents=True, exist_ok=True)
    operation = uuid4().hex
    gcloud = shutil.which('gcloud') or str(Path(os.environ['LOCALAPPDATA'])/'Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd')
    common = ['--project='+args.project, '--region='+args.region, '--format=json', '--quiet']

    def call(label: str, command: list[str], *, allow_missing: bool = False) -> dict | None:
        result = subprocess.run([gcloud,*command],capture_output=True,timeout=55)
        for suffix, content in (('stdout',result.stdout),('stderr',result.stderr)):
            with (output/f'{operation}-{label}-{suffix}.bin').open('xb') as stream:
                stream.write(content)
        if result.returncode:
            if allow_missing and (b'NOT_FOUND' in result.stderr or b'does not exist' in result.stderr
                    or b'Cannot find job [' in result.stderr):
                return None
            raise RuntimeError('cloud_history_'+label+'_failed')
        return json.loads(result.stdout) if result.stdout.strip() else {}

    source_cache: list[tuple[str, str, str]] = []

    def source_settings() -> tuple[str, str, str]:
        if source_cache:
            return source_cache[0]
        original = call('source', ['run','jobs','describe','lanes-news-discovery',*common])
        template = original['spec']['template']; spec = template['spec']['template']['spec']
        value = next(e['value'] for e in spec['containers'][0].get('env',[]) if e['name']=='DATABASE_URL')
        binding = template['metadata']['annotations']['run.googleapis.com/cloudsql-instances']
        source_cache.append((value, spec['serviceAccountName'], binding))
        return source_cache[0]

    def verify(job: dict) -> None:
        template = job['spec']['template']; parent = template['spec']; task = parent['template']['spec']
        container = task['containers'][0]; limits = container['resources']['limits']
        if not (container['image']==args.image and str(limits['cpu']) in ('1','1000m')
                and limits['memory']=='3Gi' and parent['taskCount']==1 and parent.get('parallelism',1)==1
                and task['maxRetries']==0 and str(task['timeoutSeconds'])=='600'
                and job['metadata'].get('labels',{}).get('lanes-purpose')=='history-archive'
                and not container.get('command')):
            raise RuntimeError('cloud_history_configuration_mismatch')
        db_url, account, binding = source_settings()
        if (task['serviceAccountName']!=account
                or template['metadata']['annotations'].get('run.googleapis.com/cloudsql-instances')!=binding
                or next(e.get('value') for e in container.get('env',[]) if e['name']=='DATABASE_URL')!=db_url):
            raise RuntimeError('cloud_history_database_binding_mismatch')

    try:
        if args.action=='disable':
            existing = call('existing',['run','jobs','describe',JOB,*common])
            if existing['metadata'].get('labels',{}).get('lanes-purpose')!='history-archive':
                raise RuntimeError('cloud_history_unowned_job')
            call('disable',['run','jobs','update',JOB,'--command=python',
                '--args=-c,raise SystemExit(0)',*common])
            disabled = call('verify-disabled',['run','jobs','describe',JOB,*common])
            container = disabled['spec']['template']['spec']['template']['spec']['containers'][0]
            if container.get('command') != ['python'] or container.get('args') != ['-c','raise SystemExit(0)']:
                raise RuntimeError('cloud_history_disable_not_verified')
            print(json.dumps({'status':'disabled','job':JOB,'operation':operation,
                'database_writes_performed':False}))
        elif args.action=='deploy':
            existing = call('existing',['run','jobs','describe',JOB,*common],allow_missing=True)
            if existing and existing['metadata'].get('labels',{}).get('lanes-purpose')!='history-archive':
                raise RuntimeError('cloud_history_unowned_job')
            db_url, account, binding = source_settings()
            environment = {'DATABASE_URL':db_url,'ENVIRONMENT':'production',
                'LANES_HISTORY_RESOURCE_PROFILE':'cloud-run-v1'}
            environment_file = output/f'{operation}-environment-private.json'
            with environment_file.open('x',encoding='utf-8') as stream:
                json.dump(environment,stream)
            call('deploy',['run','jobs','deploy' if existing else 'create',JOB,'--image='+args.image,
                '--service-account='+account,'--set-cloudsql-instances='+binding,
                '--cpu=1','--memory=3Gi','--tasks=1','--parallelism=1','--max-retries=0','--task-timeout=600s',
                '--labels=lanes-purpose=history-archive','--env-vars-file='+str(environment_file),
                '--args=inspect,--config-sha256,'+args.config_sha256,*common])
            job = call('verify',['run','jobs','describe',JOB,*common]); verify(job)
            print(json.dumps({'status':'deployed','job':JOB,'operation':operation}))
        elif args.action=='run':
            job = call('verify',['run','jobs','describe',JOB,*common]); verify(job)
            claim = {'operation':operation,'image':args.image,'config_sha256':args.config_sha256,
                'mode':args.mode,'batch':args.batch,'dispatch_status':'claimed_before_dispatch'}
            with (output/f'{operation}-dispatch-claim.json').open('x',encoding='utf-8') as stream:
                json.dump(claim,stream)
            result = call('dispatch',['run','jobs','execute',JOB,'--async',
                '--args='+','.join((args.mode,'--batch',str(args.batch),'--config-sha256',args.config_sha256)),*common])
            print(json.dumps({'status':'dispatched','operation':operation,'execution':result['metadata']['name']}))
        else:
            if not args.execution or not re.fullmatch(JOB+r'-[a-z0-9]+',args.execution):
                raise RuntimeError('cloud_history_execution_invalid')
            if args.action=='status':
                result = call('status',['run','jobs','executions','describe',args.execution,*common])
                status=result.get('status',{})
                print(json.dumps({'execution':args.execution,'completed':status.get('completionTime'),
                    'succeeded':status.get('succeededCount',0),'failed':status.get('failedCount',0),
                    'conditions':status.get('conditions',[])}))
            else:
                # Read the same authenticated Logging API directly. The CLI's
                # unbounded historical search can delay every two-article batch.
                # Access tokens remain in memory and never enter saved receipts.
                import httpx
                token = subprocess.run([gcloud,'auth','print-access-token'],capture_output=True,timeout=30)
                if token.returncode:
                    raise RuntimeError('cloud_history_log_auth_failed')
                from datetime import datetime, timedelta, timezone
                execution = call('log-window',['run','jobs','executions','describe',args.execution,*common])
                start = datetime.fromisoformat(execution['metadata']['creationTimestamp'].replace('Z','+00:00')) - timedelta(seconds=30)
                completed = execution.get('status',{}).get('completionTime')
                end = (datetime.fromisoformat(completed.replace('Z','+00:00')) if completed else datetime.now(timezone.utc)) + timedelta(seconds=30)
                result = []
                request = {'resourceNames':['projects/'+args.project],
                    'filter':'resource.type="cloud_run_job" AND resource.labels.job_name="'+JOB+'" AND labels."run.googleapis.com/execution_name"="'+args.execution+'"'
                        +' AND timestamp >= "'+start.isoformat()+'" AND timestamp <= "'+end.isoformat()+'"',
                    'orderBy':'timestamp asc', 'pageSize':1000}
                with httpx.Client(timeout=45, headers={'Authorization':'Bearer '+token.stdout.decode().strip()}) as client:
                    for page in range(8):
                        response = client.post('https://logging.googleapis.com/v2/entries:list', json=request)
                        with (output/f'{operation}-logs-page-{page}.bin').open('xb') as stream:
                            stream.write(response.content)
                        response.raise_for_status()
                        document = response.json()
                        result.extend(document.get('entries',[]))
                        if not document.get('nextPageToken'):
                            break
                        request['pageToken'] = document['nextPageToken']
                    else:
                        raise RuntimeError('cloud_history_log_page_limit')
                events=[r['jsonPayload'] for r in result if r.get('jsonPayload',{}).get('schema') in
                    ('news-history-seed-receipt-v1', 'lanes-historical-attempt-v1')
                    and r['jsonPayload'].get('attempt_id') == args.execution
                    and r['jsonPayload'].get('stage') in ('inspect','register','preflight','process','preview','apply','batch')]
                print(json.dumps({'execution':args.execution,'events':events}))
        return 0
    except Exception as error:
        print(json.dumps({'status':'failed','operation':operation,'error_type':type(error).__name__,
            'error_code':str(error) if isinstance(error,RuntimeError) else 'cloud_history_operation_failed'}))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
