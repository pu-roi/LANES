"""Constructed network fixtures only; no news, models, database or live API."""
import gzip
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner.bounded_discovery import BoundaryError, DeferredRequest, Session, _PacingGate, _registry

URL='https://www.gmanetwork.com/news/test/12345/constructed/story/'
QUERY='(flood OR flooding) domain:gmanetwork.com'
START='20260801000000';END='20261014155959'

def article(url=URL,**extra):
    return {'url':url,'url_mobile':'','title':'Constructed article','seendate':'20260802T000000Z',
            'socialimage':'','domain':'gmanetwork.com','language':'Unknown','sourcecountry':'Philippines',**extra}


class Clock:
    def __init__(self):
        self.value = datetime(2026,10,17,tzinfo=timezone.utc)
        self.waits = []

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.value += timedelta(seconds=seconds)

class BoundedDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.out=self.base/'new-private'
        self.clock=Clock()

    def session(self,urls=None,attempts=66):
        s=Session.create(self.out,urls or [],baseline_attempts=attempts)
        self.addCleanup(s.close);return s

    def client(self,payload=None,status=200,headers=None,handler=None):
        def fallback(request):return httpx.Response(status,json=payload if payload is not None else {'articles':[article()]},headers=headers)
        c=httpx.Client(transport=httpx.MockTransport(handler or fallback));self.addCleanup(c.close);return c

    def discover(self,s,c=None,records=1,**kw):
        s._clock=self.clock.now;s._sleep=self.clock.sleep
        s._test_transport=(c or self.client())._transport
        return s.discover(query=kw.get('query',QUERY),start=kw.get('start',START),end=kw.get('end',END),max_records=records)

    def test_reservation_precedes_request(self):
        s=self.session()
        def send(request):
            self.assertEqual(s.status()['reserved_url_slots'],3)
            self.assertEqual(s.events[-1]['kind'],'discovery_reserved')
            self.assertEqual(request.url.params['maxrecords'],'1')
            return httpx.Response(200,json={'articles':[article()]})
        batch=self.discover(s,self.client(handler=send))
        self.assertEqual(batch.observed_urls,(URL,));self.assertTrue(s.verified)
        self.assertEqual(s.status()['reserved_url_slots'],0)

    def test_no_larger_request_before_nonempty_probe(self):
        s=self.session()
        with self.assertRaises(BoundaryError):self.discover(s,records=5)
        self.assertEqual(len(s.events),1)

    def test_empty_probe_is_not_verified(self):
        s=self.session();self.discover(s,self.client({'articles':[]}))
        self.assertFalse(s.verified)
        with self.assertRaises(BoundaryError):self.discover(s,records=2)

    def test_five_after_probe(self):
        s=self.session();self.discover(s)
        rows=[article(URL+str(i)) for i in range(5)]
        self.assertEqual(len(self.discover(s,self.client({'articles':rows}),records=5).articles),5)

    def test_invalid_record_limits(self):
        s=self.session()
        for n in [0,-1,6,True,1.0]:
            with self.subTest(n=n),self.assertRaises(BoundaryError):self.discover(s,records=n)

    def test_budget_exhaustion_stops_before_network(self):
        s=self.session([f'https://example.invalid/{i}' for i in range(298)])
        with self.assertRaises(BoundaryError):self.discover(s)
        self.assertEqual(len(s.events),1)

    def test_raw_aliases_and_images_count_before_filtering(self):
        s=self.session();amp=URL+'?output=amp';image='https://media.example.invalid/constructed.jpg'
        batch=self.discover(s,self.client({'articles':[article(url_mobile=amp,socialimage=image)]}))
        self.assertEqual(s.status()['exposed_urls'],3)
        self.assertEqual(set(batch.observed_urls),{URL,amp,image})

    def test_repeat_raw_urls_are_accounted_without_double_debit(self):
        s=self.session();self.discover(s);self.discover(s)
        self.assertEqual(s.status()['exposed_urls'],1)
        self.assertEqual(sum(x['kind']=='discovery_completed' for x in s.events),2)

    def test_overreturn_not_sliced_and_evidence_preserved(self):
        s=self.session();payload={'articles':[article(),article(URL+'two')]}
        with self.assertRaises(BoundaryError):self.discover(s,self.client(payload))
        self.assertEqual(s.status()['exposed_urls'],2);self.assertTrue(s.halted)
        evidence=s.events[-1]['data']['evidence'];raw=(s.directory/evidence['file']).read_bytes()
        self.assertEqual(json.loads(raw),payload);self.assertEqual(hashlib.sha256(raw).hexdigest(),evidence['sha256'])

    def test_unexpected_url_field_retained_and_rejected(self):
        s=self.session();extra='https://example.invalid/unexpected'
        with self.assertRaises(BoundaryError):self.discover(s,self.client({'articles':[article(extra_url=extra)]}))
        self.assertIn(extra,s.seen);self.assertTrue(s.halted)

    def test_nested_unexpected_urls_are_not_hidden(self):
        s=self.session();extra='https://example.invalid/nested'
        with self.assertRaises(BoundaryError):self.discover(s,self.client({'articles':[article(extra={'nested':[extra]})]}))
        self.assertIn(extra,s.seen)

    def test_more_url_exposures_than_reservation(self):
        s=self.session();title=' '.join('https://example.invalid/'+str(i) for i in range(5))
        with self.assertRaises(BoundaryError):self.discover(s,self.client({'articles':[article(title=title)]}))
        self.assertEqual(s.status()['exposed_urls'],6)

    def test_malformed_json_retains_reservation(self):
        s=self.session();c=self.client(handler=lambda r:httpx.Response(200,content=b'{broken',headers={'content-type':'application/json'}))
        with self.assertRaises(BoundaryError):self.discover(s,c)
        self.assertEqual(s.status()['reserved_url_slots'],3);self.assertTrue(s.halted)

    def test_duplicate_json_fields_rejected(self):
        s=self.session();c=self.client(handler=lambda r:httpx.Response(200,content=b'{"articles":[],"articles":[]}',headers={'content-type':'application/json'}))
        with self.assertRaises(BoundaryError):self.discover(s,c)

    def test_html_not_treated_as_valid_json(self):
        s=self.session();c=self.client(handler=lambda r:httpx.Response(200,text='<a href="'+URL+'">fixture</a>'))
        with self.assertRaises(BoundaryError):self.discover(s,c)
        self.assertIn(URL,s.seen)

    def test_discovery_redirect_not_followed(self):
        s=self.session();calls=[]
        def send(r):calls.append(r);return httpx.Response(302,headers={'location':URL})
        with self.assertRaises(BoundaryError):self.discover(s,self.client(handler=send))
        self.assertEqual(len(calls),1);self.assertIn(URL,s.seen)

    def test_http_error_no_automatic_retry(self):
        s=self.session();calls=[]
        def send(r):calls.append(r);return httpx.Response(503,text='unavailable')
        with self.assertRaises(BoundaryError):self.discover(s,self.client(handler=send))
        self.assertEqual(len(calls),1)
        with self.assertRaises(BoundaryError):self.discover(s)

    def test_network_error_keeps_pending_reservation(self):
        s=self.session()
        def fail(r):raise httpx.ConnectError('constructed failure')
        with self.assertRaises(BoundaryError):self.discover(s,self.client(handler=fail))
        self.assertEqual(s.status()['reserved_url_slots'],3)

    def test_oversize_response_is_held_not_truncated_to_results(self):
        s=self.session()
        with patch('training.flood_ner.bounded_discovery.MAX_BYTES',8):
            with self.assertRaises(BoundaryError):self.discover(s)
        self.assertTrue(s.halted);self.assertTrue(s.events[-1]['data']['evidence']['incomplete'])

    def test_pending_reservation_survives_reopen(self):
        s=self.session();s._append('discovery_reserved',{'request_id':'fixture','slots':3});s.close()
        with Session(self.out) as restored:
            self.assertEqual(restored.status()['reserved_url_slots'],3)
            with self.assertRaises(BoundaryError):self.discover(restored)

    def test_single_writer_lock(self):
        self.session()
        with self.assertRaises(BoundaryError):Session(self.out)

    def test_completed_state_reopens_without_reset(self):
        s=self.session();self.discover(s);s.close()
        with Session(self.out) as restored:
            self.assertEqual(restored.status()['exposed_urls'],1);self.assertTrue(restored.verified)
            self.assertEqual(restored.attempts,66)

    def test_chain_tamper_rejected(self):
        s=self.session();s.close();p=self.out/'journal.jsonl';raw=p.read_bytes()
        p.write_bytes(raw.replace(b'66',b'65',1))
        with self.assertRaises(BoundaryError):Session(self.out)

    def test_partial_append_rejected(self):
        s=self.session();s.close()
        with (self.out/'journal.jsonl').open('ab') as f:f.write(b'{partial')
        with self.assertRaises(BoundaryError):Session(self.out)

    def test_empty_existing_journal_cannot_reset_baseline(self):
        self.out.mkdir();(self.out/'journal.jsonl').touch()
        with self.assertRaises(BoundaryError):Session(self.out)

    def test_second_initialize_event_rejected_on_reopen(self):
        s=self.session();s._append('initialize',s.events[0]['data']);s.close()
        with self.assertRaises(BoundaryError):Session(self.out)

    def test_unknown_chained_event_rejected_on_reopen(self):
        s=self.session();s._append('invented_event',{});s.close()
        with self.assertRaises(BoundaryError):Session(self.out)

    def test_query_domain_and_dates_checked_before_network(self):
        s=self.session()
        for kw in [{'query':'unbounded flood'},{'query':'domain:gmanetwork.com.evil flood'},
                   {'start':'20260701000000'},{'end':'20261015160000'},{'start':'invalid'}]:
            with self.subTest(kw=kw),self.assertRaises(BoundaryError):self.discover(s,**kw)
        self.assertEqual(len(s.events),1)

    def test_duplicate_baseline_raw_url_rejected(self):
        with self.assertRaises(BoundaryError):Session.create(self.out,[URL,URL])

    def test_output_never_overwrites_existing_directory(self):
        s=self.session();s.close()
        before=(self.out/'journal.jsonl').read_bytes()
        with self.assertRaises(FileExistsError):Session.create(self.out,[])
        self.assertEqual(before,(self.out/'journal.jsonl').read_bytes())

    def test_capture_debit_before_get(self):
        s=self.session([URL])
        def send(r):self.assertEqual(s.attempts,67);return httpx.Response(200,text='constructed body')
        with s.article_client(httpx.MockTransport(send)) as c:self.assertEqual(c.get(URL).text,'constructed body')
        self.assertEqual(s.attempts,67);self.assertEqual(s.status()['reserved_url_slots'],0)

    def test_capture_http_failure_still_counted(self):
        s=self.session([URL])
        with s.article_client(httpx.MockTransport(lambda r:httpx.Response(404))) as c:self.assertEqual(c.get(URL).status_code,404)
        self.assertEqual(s.attempts,67)

    def test_capture_redirect_and_target_both_counted(self):
        s=self.session([URL]);target=URL+'?redirect=1'
        def send(r):return httpx.Response(302,headers={'location':target}) if str(r.url)==URL else httpx.Response(200,text='body')
        with s.article_client(httpx.MockTransport(send)) as c:
            self.assertEqual(c.get(URL).status_code,302);self.assertEqual(c.get(target).status_code,200)
        self.assertEqual(s.attempts,68);self.assertIn(target,s.seen)

    def test_outside_capture_route_is_not_fetched(self):
        s=self.session([URL]);calls=[]
        target='https://outside.example.invalid/news/'
        with s.article_client(httpx.MockTransport(lambda r:calls.append(r))) as c:
            with self.assertRaises(BoundaryError):c.get(target)
        self.assertEqual(calls,[]);self.assertEqual(s.attempts,66)

    def test_unknown_capture_url_requires_discovery(self):
        s=self.session()
        with s.article_client(httpx.MockTransport(lambda r:httpx.Response(200))) as c:
            with self.assertRaises(BoundaryError):c.get(URL)
        self.assertEqual(s.attempts,66)

    def test_capture_attempt_limit(self):
        s=self.session([URL],attempts=100)
        with s.article_client(httpx.MockTransport(lambda r:httpx.Response(200))) as c:
            with self.assertRaises(BoundaryError):c.get(URL)

    def test_capture_network_failure_counted_and_held(self):
        s=self.session([URL])
        def fail(r):raise httpx.ReadTimeout('constructed timeout')
        with s.article_client(httpx.MockTransport(fail)) as c:
            with self.assertRaises(BoundaryError):c.get(URL)
        self.assertEqual(s.attempts,67);self.assertTrue(s.halted);self.assertEqual(s.status()['reserved_url_slots'],1)

    def test_capture_gzip_matches_normal_httpx_decoded_body(self):
        s=self.session([URL]);body=b'constructed original body'
        def send(r):return httpx.Response(200,content=gzip.compress(body),headers={'content-encoding':'gzip'})
        with s.article_client(httpx.MockTransport(send)) as c:self.assertEqual(c.get(URL).content,body)

    def test_capture_oversize_keeps_attempt(self):
        s=self.session([URL])
        with patch('training.flood_ner.bounded_discovery.MAX_BYTES',8):
            with s.article_client(httpx.MockTransport(lambda r:httpx.Response(200,text='a'*20))) as c:
                with self.assertRaises(BoundaryError):c.get(URL)
        self.assertEqual(s.attempts,67);self.assertTrue(s.halted)

    def test_cross_thread_writer_stops_before_network(self):
        import concurrent.futures
        s=self.session()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            result=executor.submit(lambda:self.discover(s))
            with self.assertRaises(BoundaryError):result.result()
        self.assertEqual(len(s.events),1)


class ControlledContinuationTests(unittest.TestCase):
    setUp = BoundedDiscoveryTests.setUp
    session = BoundedDiscoveryTests.session
    client = BoundedDiscoveryTests.client
    discover = BoundedDiscoveryTests.discover

    def predecessor(self, headers=None, count=202):
        s=self.session([f'https://example.invalid/baseline/{i}' for i in range(count)])
        with self.assertRaises(BoundaryError):
            self.discover(s,self.client({'error':'See https://example.invalid/a and https://example.invalid/b'},429,headers))
        s.close()
        return hashlib.sha256((self.out/'journal.jsonl').read_bytes()).hexdigest()

    def continuation(self, digest, output=None, **overrides):
        args=dict(expected_journal_sha256=digest,expected_exposed_urls=204,
                  expected_attempts=66,expected_reserved_slots=1,reconciliation_sha256='a'*64)
        args.update(overrides)
        s=Session.continue_after_rate_limit(output or self.base/'continued',self.out,**args)
        self.addCleanup(s.close)
        return s

    def test_continuation_carries_full_budget_without_refund(self):
        digest=self.predecessor();before=(self.out/'journal.jsonl').read_bytes()
        s=self.continuation(digest)
        self.assertEqual((s.status()['exposed_urls'],s.attempts,s.status()['reserved_url_slots']),(204,66,1))
        self.assertEqual(s.status()['remaining_url_slots'],95)
        def send(request):
            self.assertEqual(s.status()['reserved_url_slots'],4)
            self.assertEqual(request.url.params['maxrecords'],'1')
            return httpx.Response(200,json={'articles':[article()]})
        self.discover(s,self.client(handler=send))
        self.assertEqual(s.status()['reserved_url_slots'],1)
        self.assertEqual(s.status()['remaining_url_slots'],94)
        self.assertEqual(before,(self.out/'journal.jsonl').read_bytes())

    def test_stale_baseline_expectations_rejected(self):
        digest=self.predecessor()
        for kwargs in [{'expected_exposed_urls':202},{'expected_attempts':65},{'expected_reserved_slots':0}]:
            with self.subTest(kwargs=kwargs),self.assertRaises(BoundaryError):self.continuation(digest,**kwargs)
        self.assertFalse((self.base/'continued').exists())

    def test_changed_predecessor_journal_rejected(self):
        digest=self.predecessor()
        with (self.out/'journal.jsonl').open('ab') as f:f.write(b'\n')
        with self.assertRaises(BoundaryError):self.continuation(digest)

    def test_changed_predecessor_receipt_rejected(self):
        digest=self.predecessor();next(self.out.glob('*.response.bin')).write_bytes(b'altered')
        with self.assertRaises(BoundaryError):self.continuation(digest)

    def test_second_continuation_claim_rejected_even_after_close(self):
        digest=self.predecessor();s=self.continuation(digest);s.close()
        with self.assertRaises(BoundaryError):self.continuation(digest,self.base/'other')

    def test_busy_predecessor_rejected(self):
        digest=self.predecessor()
        with Session(self.out):
            with self.assertRaises(BoundaryError):self.continuation(digest)

    def test_existing_destination_rejected_without_claim(self):
        digest=self.predecessor();(self.base/'continued').mkdir()
        with self.assertRaises(BoundaryError):self.continuation(digest)
        self.assertEqual(list(self.base.glob('.controlled-retry-*')),[])

    def test_future_retry_header_stops_before_claim(self):
        digest=self.predecessor({'retry-after':'Fri, 01 Jan 2100 00:00:00 GMT'})
        with self.assertRaisesRegex(BoundaryError,'2100'):self.continuation(digest)
        self.assertFalse((self.base/'continued').exists())

    def test_future_curator_deadline_stops_before_claim(self):
        digest=self.predecessor()
        with self.assertRaisesRegex(BoundaryError,'2100'):
            self.continuation(digest,not_before_utc='2100-01-01T00:00:00Z')

    def test_retry_seconds_persist_deadline(self):
        digest=self.predecessor({'retry-after':'86400'})
        fixture_now=self.clock.now()
        class BeforeDeadline(datetime):
            @classmethod
            def now(cls,tz=None):
                return fixture_now.astimezone(tz) if tz else fixture_now.replace(tzinfo=None)
        # The receipt uses the constructed clock; continuation must compare with
        # that clock too, even after the real calendar passes its recorded date.
        with patch('training.flood_ner.bounded_discovery.datetime',BeforeDeadline):
            with self.assertRaises(BoundaryError):self.continuation(digest)
        events=[json.loads(x) for x in (self.out/'journal.jsonl').read_text().splitlines()]
        self.assertIsNotNone(events[-1]['data']['evidence']['retry_not_before_utc'])

    def test_invalid_retry_header_not_silently_ignored(self):
        digest=self.predecessor({'retry-after':'invalid'})
        with self.assertRaises(BoundaryError):self.continuation(digest)

    def test_elapsed_retry_header_allows_one_probe(self):
        digest=self.predecessor({'retry-after':'0'})
        s=self.continuation(digest);self.discover(s)
        self.assertTrue(s.verified)

    def test_continuation_failure_preserves_inherited_plus_new_reservation(self):
        digest=self.predecessor();s=self.continuation(digest)
        with self.assertRaises(BoundaryError):self.discover(s,self.client({'error':'busy'},429))
        self.assertTrue(s.halted);self.assertEqual(s.status()['reserved_url_slots'],4)
        s.close()
        with Session(self.base/'continued') as reopened:
            self.assertEqual(reopened.status()['reserved_url_slots'],4)
            with self.assertRaises(BoundaryError):self.discover(reopened)

    def test_no_chaining_another_retry(self):
        digest=self.predecessor();s=self.continuation(digest)
        with self.assertRaises(BoundaryError):self.discover(s,self.client({'error':'busy'},429))
        s.close();source=self.base/'continued'
        with self.assertRaises(BoundaryError):
            Session.continue_after_rate_limit(self.base/'third',source,
                expected_journal_sha256=hashlib.sha256((source/'journal.jsonl').read_bytes()).hexdigest(),
                expected_exposed_urls=204,expected_attempts=66,expected_reserved_slots=4,reconciliation_sha256='b'*64)

    def test_interrupted_continuation_keeps_claim(self):
        digest=self.predecessor()
        with patch.object(Session,'_append',side_effect=OSError('constructed disk error')):
            with self.assertRaises(OSError):self.continuation(digest)
        with self.assertRaises(BoundaryError):self.continuation(digest,self.base/'another')

    def test_inherited_reservation_exhaustion(self):
        digest=self.predecessor(count=295)
        s=self.continuation(digest,expected_exposed_urls=297)
        self.assertEqual(s.status()['remaining_url_slots'],2)
        with self.assertRaises(BoundaryError):self.discover(s)
        self.assertEqual(len(s.events),1)

    def test_two_concurrent_claims_cannot_both_continue(self):
        import concurrent.futures
        digest=self.predecessor()
        def attempt(index):
            try:
                with Session.continue_after_rate_limit(self.base/str(index),self.out,
                    expected_journal_sha256=digest,expected_exposed_urls=204,
                    expected_attempts=66,expected_reserved_slots=1,reconciliation_sha256='a'*64):
                    return True
            except BoundaryError:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(sum(executor.map(attempt,range(2))),1)

    def test_artifacts_claim_stays_outside_preserved_curator_package(self):
        # Real journals are nested inside immutable versioned curator packages.
        artifacts=self.base/'artifacts';artifacts.mkdir();old=artifacts/'old';old.mkdir()
        self.out=old/'acquisition';digest=self.predecessor()
        before={p.relative_to(old):p.read_bytes() for p in old.rglob('*') if p.is_file()}
        s=self.continuation(digest,artifacts/'new');s.close()
        self.assertEqual(before,{p.relative_to(old):p.read_bytes() for p in old.rglob('*') if p.is_file()})
        self.assertEqual(len(list(artifacts.glob('.controlled-retry-*.claim.json'))),1)

class FinalDiagnosticTests(unittest.TestCase):
    setUp = BoundedDiscoveryTests.setUp
    session = BoundedDiscoveryTests.session
    client = BoundedDiscoveryTests.client
    discover = BoundedDiscoveryTests.discover
    predecessor = ControlledContinuationTests.predecessor
    continuation = ControlledContinuationTests.continuation

    def diagnostic(self):
        digest=self.predecessor();s=self.continuation(digest)
        with self.assertRaises(BoundaryError):self.discover(s,self.client({'error':'busy'},429))
        source=s.directory;s.close()
        digest=hashlib.sha256((source/'journal.jsonl').read_bytes()).hexdigest()
        result=Session.final_diagnostic(self.base/'final',source,
            expected_journal_sha256=digest,reconciliation_sha256='b'*64)
        self.addCleanup(result.close)
        return result,source,digest

    def receipt(self,s):
        evidence=s.events[-1]['data']['evidence']
        return evidence,json.loads((s.directory/evidence['headers_file']).read_text())

    def test_owned_client_headers_and_timeout(self):
        s=self.session();calls=[]
        def send(request):
            calls.append(request)
            self.assertEqual(request.headers['user-agent'],'LANES-NER-Research/1.0')
            self.assertEqual(request.headers['accept'],'application/json')
            self.assertTrue(all(x==30 for x in request.extensions['timeout'].values()))
            return httpx.Response(200,json={'articles':[article()]})
        self.discover(s,self.client(handler=send));self.assertEqual(len(calls),1)

    def test_external_client_argument_no_longer_accepted(self):
        s=self.session()
        with self.assertRaises(TypeError):s.discover(self.client(),query=QUERY,start=START,end=END)

    def test_only_mock_transport_injection_allowed(self):
        s=self.session();s._test_transport=httpx.HTTPTransport()
        with self.assertRaises(BoundaryError):s._discovery_client()
        s._test_transport.close()

    def test_initial_quiet_period_and_completion_based_cooldown(self):
        s=self.session()
        def send(request):
            self.clock.value+=timedelta(seconds=12)
            return httpx.Response(200,json={'articles':[article()]})
        self.discover(s,self.client(handler=send));self.discover(s)
        self.assertEqual(self.clock.waits,[30,30])
        self.assertEqual(self.clock.value,datetime(2026,10,17,tzinfo=timezone.utc)+timedelta(seconds=72))

    def test_shared_pacing_across_sessions_and_restarts(self):
        s=self.session();self.discover(s);s.close()
        other=Session.create(self.base/'other',[]);self.addCleanup(other.close)
        self.discover(other)
        self.assertEqual(self.clock.waits,[30,30])
        other.close()
        with Session(self.base/'other') as reopened:self.discover(reopened)
        self.assertEqual(self.clock.waits,[30,30,30])

    def test_competing_pacer_rejected_without_request(self):
        s=self.session()
        with _PacingGate(self.base,self.clock.now,self.clock.sleep):
            with self.assertRaises(BoundaryError):self.discover(s)
        self.assertEqual(len(s.events),1)

    def test_unresolved_interruption_blocks_other_session(self):
        with _PacingGate(self.base,self.clock.now,self.clock.sleep) as gate:
            gate.wait();gate.start('constructed-interrupted')
        s=self.session()
        with self.assertRaises(BoundaryError):self.discover(s)
        self.assertEqual(len(s.events),1)

    def test_tampered_pacer_rejected(self):
        s=self.session();self.discover(s)
        p=self.base/'.gdelt-pacing.jsonl';p.write_bytes(p.read_bytes().replace(b'completed',b'altered'))
        other=Session.create(self.base/'other',[]);self.addCleanup(other.close)
        with self.assertRaises(BoundaryError):self.discover(other)

    def test_clock_backwards_does_not_shorten_quiet_period(self):
        s=self.session();self.discover(s);self.clock.value-=timedelta(seconds=100)
        other=Session.create(self.base/'other',[]);self.addCleanup(other.close)
        with self.assertRaises(BoundaryError):self.discover(other)

    def test_small_wall_clock_quantum_is_waited_out(self):
        waits=[]
        def coarse_sleep(seconds):
            waits.append(seconds)
            self.clock.value+=timedelta(seconds=seconds-.015625 if len(waits)==1 else seconds)
        with _PacingGate(self.base,self.clock.now,coarse_sleep) as gate:
            gate.wait()
        self.assertEqual(waits,[30,.015625])

    def test_high_resolution_elapsed_guard_waits_instead_of_false_failure(self):
        elapsed=[0.0];waits=[]
        def coarse_sleep(seconds):
            waits.append(seconds)
            elapsed[0]+=seconds-.015625 if len(waits)==1 else seconds
            self.clock.value+=timedelta(seconds=seconds)
        with patch('training.flood_ner.bounded_discovery.time.sleep',new=coarse_sleep), \
             patch('training.flood_ner.bounded_discovery.time.perf_counter',side_effect=lambda:elapsed[0]), \
             patch('training.flood_ner.bounded_discovery.time.monotonic',side_effect=AssertionError('coarse clock not used')):
            with _PacingGate(self.base,self.clock.now,coarse_sleep) as gate:
                gate.wait()
        self.assertEqual(waits,[30,.015625])

    def test_wait_does_not_exceed_total_cap_after_clock_rollback(self):
        elapsed=[0.0]
        def rollback_sleep(seconds):
            elapsed[0]+=seconds
            self.clock.value-=timedelta(seconds=90)
        with patch('training.flood_ner.bounded_discovery.time.sleep',new=rollback_sleep), \
             patch('training.flood_ner.bounded_discovery.time.perf_counter',side_effect=lambda:elapsed[0]):
            with _PacingGate(self.base,self.clock.now,rollback_sleep) as gate:
                with self.assertRaises(DeferredRequest):gate.wait()

    def test_headers_are_allowlisted(self):
        s=self.session()
        headers={'date':'Sat, 17 Oct 2026 00:00:30 GMT','age':'0','cache-control':'max-age=900',
                 'x-ratelimit-limit':'12','set-cookie':'constructed-secret','authorization':'constructed-secret'}
        self.discover(s,self.client(headers=headers))
        e,r=self.receipt(s)
        self.assertFalse(e['retry_after_present']);self.assertIn('date',r['response_headers'])
        self.assertIn('x-ratelimit-limit',r['response_headers'])
        self.assertNotIn('set-cookie',r['response_headers']);self.assertNotIn('authorization',r['response_headers'])
        self.assertNotIn('constructed-secret',(s.directory/e['headers_file']).read_text())

    def test_headers_survive_body_timeout(self):
        s=self.session()
        class Broken(httpx.SyncByteStream):
            def __iter__(self):
                yield b'partial received'
                raise httpx.ReadTimeout('constructed body timeout')
        with self.assertRaises(BoundaryError):
            self.discover(s,self.client(handler=lambda r:httpx.Response(200,stream=Broken(),headers={'content-type':'application/json','retry-after':'40'})))
        e,r=self.receipt(s)
        self.assertEqual(r['status_code'],200);self.assertTrue(e['incomplete'])
        self.assertEqual((s.directory/e['file']).read_bytes(),b'partial received')
        self.assertEqual(e['retry_after_values'],['40'])

    def test_long_retry_after_defers_next_session_without_reservation(self):
        s=self.session();self.discover(s,self.client(headers={'retry-after':'120'}))
        other=Session.create(self.base/'other',[]);self.addCleanup(other.close)
        with self.assertRaises(DeferredRequest) as caught:self.discover(other)
        self.assertIn('00:02:30',caught.exception.earliest_utc)
        self.assertEqual(len(other.events),1);self.assertEqual(other.status()['reserved_url_slots'],0)

    def test_valid_provider_deadline_longer_than_local_cooldown(self):
        s=self.session();self.discover(s,self.client(headers={'retry-after':'45'}));self.discover(s)
        self.assertEqual(self.clock.waits,[30,45])

    def test_http_date_retry_after(self):
        s=self.session()
        self.discover(s,self.client(headers={'retry-after':'Sat, 17 Oct 2026 00:01:15 GMT'}));self.discover(s)
        self.assertEqual(self.clock.waits,[30,45])

    def test_duplicate_identical_retry_after_allowed(self):
        s=self.session();self.discover(s,self.client(headers=[('retry-after','0'),('retry-after','0')]))
        self.assertEqual(self.receipt(s)[0]['retry_after_values'],['0','0'])

    def test_contradictory_retry_after_blocks_shared_gate(self):
        s=self.session()
        with self.assertRaises(BoundaryError):
            self.discover(s,self.client(headers=[('retry-after','30'),('retry-after','60')]))
        self.assertTrue(self.receipt(s)[0]['retry_after_parse_error'])
        other=Session.create(self.base/'other',[]);self.addCleanup(other.close)
        with self.assertRaises(BoundaryError):self.discover(other)

    def test_bad_retry_after_does_not_hide_header_urls(self):
        s=self.session()
        with self.assertRaises(BoundaryError):
            self.discover(s,self.client(headers={'retry-after':'broken','ratelimit-policy':'https://example.invalid/terms'}))
        self.assertIn('https://example.invalid/terms',s.seen)

    def test_final_import_retains_all_four_slots(self):
        s,source,digest=self.diagnostic()
        self.assertEqual((s.status()['exposed_urls'],s.status()['reserved_url_slots'],s.attempts),(204,4,66))
        self.assertEqual(s.status()['remaining_url_slots'],92)
        self.assertEqual(hashlib.sha256((source/'journal.jsonl').read_bytes()).hexdigest(),digest)

    def test_final_success_still_cannot_dispatch_twice(self):
        s,_,_=self.diagnostic();self.discover(s)
        self.assertEqual(s.status()['reserved_url_slots'],4)
        before=len(s.events)
        with self.assertRaises(BoundaryError):self.discover(s)
        self.assertEqual(len(s.events),before)
        s.close()
        with Session(self.base/'final') as reopened:
            with self.assertRaises(BoundaryError):self.discover(reopened)

    def test_final_failure_stops_without_retry(self):
        s,_,_=self.diagnostic();calls=[]
        def send(r):calls.append(r);self.assertEqual(s.status()['reserved_url_slots'],7);return httpx.Response(429,text='busy')
        with self.assertRaises(BoundaryError):self.discover(s,self.client(handler=send))
        self.assertEqual(len(calls),1);self.assertEqual(s.status()['reserved_url_slots'],7)
        self.assertEqual(s.status()['remaining_url_slots'],89)

    def test_final_never_allows_publisher_client(self):
        s,_,_=self.diagnostic()
        with self.assertRaises(BoundaryError):s.article_client()

    def test_final_repeated_launch_rejected(self):
        s,source,digest=self.diagnostic();s.close()
        with self.assertRaises(BoundaryError):
            Session.final_diagnostic(self.base/'another',source,expected_journal_sha256=digest,reconciliation_sha256='c'*64)

    def test_reopening_unspent_diagnostic_cannot_restore_launch_permission(self):
        s,_,_=self.diagnostic();s.close()
        with Session(self.base/'final') as reopened:
            with self.assertRaises(BoundaryError):self.discover(reopened)
            self.assertEqual(reopened.status()['discovery_requests'],0)

    def test_preflight_failure_consumes_operation_without_network(self):
        s,_,_=self.diagnostic()
        with _PacingGate(self.base,self.clock.now,self.clock.sleep):
            with self.assertRaises(BoundaryError):self.discover(s)
        with self.assertRaises(BoundaryError):self.discover(s)
        self.assertEqual(s.status()['discovery_requests'],0)
        self.assertEqual(s.status()['reserved_url_slots'],4)

    def test_final_stale_checkpoint_rejected(self):
        s,source,digest=self.diagnostic();s.close()
        with self.assertRaisesRegex(BoundaryError,'Stale'):
            Session.final_diagnostic(self.base/'another',source,expected_journal_sha256='0'*64,reconciliation_sha256='c'*64)

    def test_final_authorization_requires_exact_checkpoint(self):
        digest=self.predecessor()
        with self.assertRaises(BoundaryError):
            Session.final_diagnostic(self.base/'final',self.out,expected_journal_sha256=digest,reconciliation_sha256='c'*64)


if __name__=='__main__':unittest.main()
