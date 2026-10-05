import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

root = Path(__file__).resolve().parents[3] / 'backend'
parser = argparse.ArgumentParser(description='Guarded disposable PostGIS verification; never live publication.')
parser.add_argument('--additional-regressions', action='store_true')
parser.add_argument('--event-regressions-only', action='store_true')
parser.add_argument('--zone-metadata-regressions', action='store_true',
                    help='Extend --additional-regressions with related zone schema/news depth checks.')
args = parser.parse_args()
container = 'lanes_postgis_db'
suffix = uuid4().hex[:12]
databases = ['lanes_publication_lifecycle_test_' + suffix, 'lanes_evaluation_test_' + suffix]
metadata = json.loads(subprocess.check_output(['docker', 'inspect', container], text=True))[0]
config = dict(item.split('=', 1) for item in metadata['Config']['Env'] if '=' in item)
user = config.get('POSTGRES_USER', 'postgres')
password = config.get('POSTGRES_PASSWORD', '')
from sqlalchemy.engine import URL
def connection(name):
    return URL.create('postgresql+psycopg', username=user, password=password, host='127.0.0.1', port=5432, database=name).render_as_string(hide_password=False)

env = dict(os.environ)
env['DATABASE_URL'] = connection(databases[1])
env['LANES_NEWS_PUBLICATION_LIFECYCLE_TEST_DATABASE_URL'] = connection(databases[0])
env['LANES_NEWS_EVALUATION_TEST_DATABASE_URL'] = connection(databases[1])
env['PYTHONPATH'] = str(root) + os.pathsep + str(root / 'tests')
created = []
exit_code = 0
try:
    for name in databases:
        assert name.startswith(('lanes_publication_lifecycle_test_', 'lanes_evaluation_test_'))
        subprocess.run(['docker', 'exec', container, 'createdb', '-U', user, name], check=True)
        created.append(name)
    tests = [
        'tests/test_operational_footprint.py', 'tests/test_news_pipeline.py',
        'tests/test_operational_footprint_evidence.py',
        'tests/test_news_publication_lifecycle.py', 'tests/test_news_publication_api.py',
        'tests/test_routing_service.py', 'tests/test_flood_routing_policy.py',
        'tests/test_news_publication_lifecycle_postgres.py',
        'tests/test_news_publication_reads_postgres.py',
    ]
    if args.additional_regressions:
        tests = ['tests/test_news_claim_auditor.py', 'tests/test_news_evaluation.py',
                 'tests/test_news_evaluation_postgres.py']
        if args.zone_metadata_regressions:
            tests += ['tests/test_zone_edit_geometry_schema.py', 'tests/test_news_reported_depth_presentation.py',
                      'tests/test_news_road_placement.py', 'tests/test_news_barangay_catalog.py',
                      'tests/test_barangay_placement.py']
    event_seed = r'''
import os
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Role, User
url=os.environ['DATABASE_URL']
parsed=make_url(url)
assert parsed.host=='127.0.0.1' and parsed.database.startswith('lanes_evaluation_test_')
settings.DATABASE_URL=url
command.upgrade(Config('alembic.ini'),'head')
engine=create_engine(url)
with sessionmaker(bind=engine)() as db, db.begin():
    role=db.scalar(select(Role).where(Role.name=='Admin'))
    if role is None:
        role=Role(name='Admin',permissions={'reports':'full'})
        db.add(role)
        db.flush()
    assert db.get(User,1) is None, 'Event fixture expects an unused user ID 1'
    db.add(User(id=1,username='admin',email='event-fixture@example.org',hashed_password='fixture-not-login',role_id=role.id))
engine.dispose()
'''
    if args.event_regressions_only:
        subprocess.run([sys.executable, '-c', event_seed], cwd=root, env=env, check=True)
        tests = ['tests/test_flood_event_service.py']
    if not os.environ.get('LANES_PHASE36_PROBE_ONLY'):
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '--tb=short', *tests], cwd=root, env=env)
        exit_code = result.returncode
        print('BASELINE_EXIT=' + str(result.returncode), flush=True)
        if args.additional_regressions and result.returncode == 0:
            subprocess.run([sys.executable, '-c', event_seed], cwd=root, env=env, check=True)
            events = subprocess.run([sys.executable, '-m', 'pytest', '-q', '--tb=short',
                                     'tests/test_flood_event_service.py'], cwd=root, env=env)
            exit_code = events.returncode
            print('EVENT_REGRESSION_EXIT=' + str(events.returncode), flush=True)
    probe = r'''
import json, os
from datetime import timedelta
from uuid import uuid4
from dataclasses import replace
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely import set_srid
from app.services import operational_footprint_evidence_service as footprint_evidence
from tests.operational_footprint_fixtures import SyntheticLocalityProvider
footprint_evidence.get_news_road_placement_provider = lambda: SyntheticLocalityProvider()
from tests.test_news_publication_lifecycle_postgres import NOW, POLICY, SOURCES, seed_evaluation, publish, staff_user
from app.services.news_publication_service import activate_operational_footprint, expire_case, clear_case_from_evaluation, apply_staff_decision
from app.services.operational_footprint_service import validate_operational_footprint
from app.models.news_publication import NewsClaimDecision, NewsClaimZoneLink
from app.models.report import FloodAvoidanceZone, FloodEvent, FloodEventStatus
from app.schemas.news_publication import NewsStaffDecisionRequest
from app.services.flood_depth import get_flood_depth_measurement
from app.crud.news_publication import NewsPublicationError
engine = create_engine(os.environ['LANES_NEWS_PUBLICATION_LIFECYCLE_TEST_DATABASE_URL'])
factory = sessionmaker(bind=engine)
if os.environ.get('LANES_PHASE36_PROBE_ONLY'):
    from alembic import command
    from alembic.config import Config
    from app.core.config import settings
    settings.DATABASE_URL = os.environ['LANES_NEWS_PUBLICATION_LIFECYCLE_TEST_DATABASE_URL']
    command.upgrade(Config('alembic.ini'), 'head')
poly = mapping(Polygon([(121.070,14.580),(121.071,14.580),(121.071,14.581),(121.070,14.581)]))
other = mapping(Polygon([(121.075,14.585),(121.076,14.585),(121.076,14.586),(121.075,14.586)]))
actor = staff_user(factory)
def activation(depth='waist', now=NOW, policy=POLICY, request=None):
    ev, case, article = seed_evaluation(factory, depth=depth)
    publish(factory, ev)
    with factory() as db, db.begin():
        d = apply_staff_decision(db,case,NewsStaffDecisionRequest(request_id=request or uuid4(),expected_revision=1,operation='correct',reason='Diagnostic fixture footprint',evaluation_id=ev,operational_footprint=poly,operational_footprint_srid=4326),policy=policy,now=now,actor_user_id=actor,sources=SOURCES)
        return case, article, d.id, d.snapshot['linked_zone_ids'][0]
rows = []
boundary = set_srid(Polygon([(121.05,14.55),(121.10,14.55),(121.10,14.60),(121.05,14.60)]),4326)
cross = Polygon([(121.099,14.58),(121.11,14.58),(121.11,14.59),(121.099,14.59)])
v = validate_operational_footprint(mapping(cross),geometry_srid=4326,parent_boundary=boundary,provenance_source='arbitrary_label')
rows.append({'probe':'parent_overlap_and_freeform_provenance','eligible':v.is_eligible,'fully_contained':boundary.covers(cross),'reason':v.reason_code})
case, article, did, zid = activation()
with factory() as db:
    z = db.get(FloodAvoidanceZone,zid)
    event = db.get(FloodEvent,z.event_id)
    rows.append({'probe':'zone_reported_depth','zone_severity':z.severity,'zone_depth':z.depth,'event_peak_severity':event.peak_severity.value,'event_peak_depth':event.peak_depth,'expected_severity':get_flood_depth_measurement('waist').severity.value})
for label, kwargs in [('staff_expired_observation',{'now':NOW+timedelta(hours=3)}),('staff_changed_policy',{'policy':replace(POLICY,fingerprint='b'*64)})]:
    try:
        c,a,d,z = activation(**kwargs)
        with factory() as db:
            row=db.get(NewsClaimDecision,d)
            rows.append({'probe':label,'accepted':True,'state':row.public_state,'already_expired':row.expires_at <= kwargs.get('now',NOW)})
    except NewsPublicationError as exc:
        rows.append({'probe':label,'accepted':False,'reason':exc.code})
c,a,d,z=activation()
with factory() as db:
    ev=db.get(NewsClaimDecision,d).evaluation_id
with factory() as db, db.begin():
    replacement=apply_staff_decision(db,c,NewsStaffDecisionRequest(request_id=uuid4(),expected_revision=2,operation='correct',reason='Retain same existing zone',evaluation_id=ev,operational_zone_id=z),policy=POLICY,now=NOW,actor_user_id=actor,sources=SOURCES)
    zone=db.get(FloodAvoidanceZone,z)
    rows.append({'probe':'staff_relink_same_zone','decision_state':replacement.public_state,'zone_active':zone.is_active,'zone_expiry_at_or_before_now':zone.expires_at<=NOW})
for operation in ['expire','clear']:
    c,a,d,z=activation()
    if operation=='expire':
        with factory() as db, db.begin(): expire_case(db,c,now=NOW+timedelta(hours=2))
    else:
        ev,_,_=seed_evaluation(factory,article_id=a,condition='subsided',observed=NOW)
        with factory() as db, db.begin(): clear_case_from_evaluation(db,c,ev,expected_revision=2,request_id=uuid4(),policy=POLICY,now=NOW,sources=SOURCES)
    with factory() as db:
        zone=db.get(FloodAvoidanceZone,z)
        event=db.get(FloodEvent,zone.event_id)
        rows.append({'probe':'linked_zone_'+operation,'zone_active':zone.is_active,'event_status':event.status.value})
with factory() as db:
    head=db.execute(text('select version_num from alembic_version')).scalar_one()
print('AUDIT_PROBES='+json.dumps({'migration_head':head,'results':rows}))
engine.dispose()
'''
    outcome = (subprocess.CompletedProcess([], 0) if args.additional_regressions or args.event_regressions_only
               else subprocess.run([sys.executable, '-c', probe], cwd=root, env=env))
    exit_code = exit_code or outcome.returncode
    if not (args.additional_regressions or args.event_regressions_only):
        print('PROBE_EXIT=' + str(outcome.returncode), flush=True)
finally:
    for name in created:
        subprocess.run(['docker', 'exec', container, 'dropdb', '-U', user, '--force', name], check=True)
    print('DISPOSABLE_DATABASES_REMOVED=' + str(len(created)), flush=True)
raise SystemExit(exit_code)
