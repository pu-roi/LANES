"""Research bundle safety, deterministic examples and source-use hold boundaries."""
from copy import deepcopy
import hashlib
import csv
import json
from pathlib import Path
import zipfile

import pytest

from training.flood_ner import use_bundle as u
from training.flood_ner.annotation.schema import AnnotationRecord, text_hash
from training.flood_ner.sources import json_bytes, write_jsonl


def sample(i, language='english', full=False, split='train'):
    publisher,domain=[('ABS-CBN News','abs-cbn.com'),('GMA News','gmanetwork.com'),('Philstar','philstar.com')][i%3]
    names=[('Main Road','ROAD'),('City Hall','LANDMARK'),('Purok 03-A','LOCAL_AREA'),('Barangay Catmon','BARANGAY'),('Malabon City','CITY'),('Bulacan','PROVINCE')]
    name,label=names[i%6];text=f'Report {i}: sa Biñan—{name} was mentioned.';body=text if full else 'Header\n'+text+'\nFooter'
    start=0 if full else len('Header\n');a=text.index(name)
    return AnnotationRecord.model_validate_json(json.dumps({'record_id':f'r{i:03d}','source':{'source_id':f's{i}',
        'url':f'https://{domain}/article/{i}','publisher':publisher,'title':f'Article {i}','text':body,
        'text_sha256':text_hash(body),'capture_version':f'v{i}','article_group':f'a{i}','event_group':f'e{i}',
        'syndication_group':f'copy{i}','reuse_terms':'unresolved','extraction_method':'constructed regression capture'},
        'text':text,'text_sha256':text_hash(text),'passage_start':start,'passage_end':start+len(text),
        'passage_language':language,'split':split,'annotation_profile':'location-only-v1','annotation_revision':'fixture',
        'review_status':'accepted','complete':True,'quality':'silver','teacher':'fixture AI','reviewer':'fixture AI',
        'entities':[{'id':'place','label':label,'text':name,'start':a,'end':a+len(name)}]}))


def source_entry(r,path):
    return {'source_id':r.source.source_id,'capture_version':r.source.capture_version,'url':r.source.url,
            'publisher':r.source.publisher,'title':r.source.title,'text_path':str(path),'text_sha256':r.source.text_sha256,
            'publication_date':'2024-01-01','status':'accepted','admission_status':'research_only'}


def assessment_fixture(tmp_path):
    p=tmp_path/'evidence.html';p.write_text('Public policy evidence',encoding='utf-8')
    evidence={'evidence_id':'evidence','url':'https://example.org/policy','checked_at':'2026-10-15T00:00:00+00:00',
              'outcome':'captured','reference':{'path':'evidence.html','sha256':u.digest(p)}}
    sources=[{'source_id':f's{i}','publisher':pub} for i,pub in enumerate(['ABS-CBN News','GMA News','Philstar'])]
    rows=[]
    for source in sources:
        for scope in u.SCOPES:
            current=scope in u.CURRENT_SCOPES
            rows.append({'publisher':source['publisher'],'scope':scope,'source_ids':[source['source_id']],
                'proposed_outcome':'unresolved','review_state':'reviewed' if current else 'deferred',
                'assessor':{'name':'Codex','kind':'ai','reviewed_at':'2026-10-15'} if current else None,
                'fair_use_factors':{k:'Evidence and uncertainty reviewed' for k in ['purpose','nature','amount','market_effect']} if current else {},
                'uncertainties':['No permission inferred'],'evidence_ids':['evidence'] if current else []})
    packet={'schema_version':'lanes-study-use-review-v2','automatic_admission':False,'training_admitted':0,
            'distribution_ready':False,'evidence':[evidence],'assessments':rows}
    return packet,sources


def test_appendix_is_deterministic_balanced_training_only_and_avoids_complete_articles():
    records=[sample(i,'english' if i<12 else 'taglish') for i in range(24)]
    records += [sample(25,'english',True),sample(26,'taglish',split='test')]
    a,report=u.select_appendix(records);b,_=u.select_appendix(list(reversed(records)))
    assert [r.record_id for r in a]==[r.record_id for r in b]
    assert len(a)==10 and report['languages']=={'english':5,'taglish':5}
    assert report['all_six_classes_covered'] and len(report['publishers'])==3
    assert all(r.split=='train' and r.text!=r.source.text for r in a)
    with pytest.raises(ValueError):u.select_appendix([sample(1)])


@pytest.mark.parametrize('mutation',['scope_count','scope_duplicate','source','allowed','automatic','admitted','distribution',
                                   'human_claim','factor_missing','factor_null','review_state','deferred','evidence_hash',
                                   'path_escape','evidence_id_escape','unbound','failure_without_error'])
def test_scoped_assessments_cannot_clear_sources_or_forge_evidence(tmp_path,mutation):
    packet,sources=assessment_fixture(tmp_path);r=packet['assessments'][0];e=packet['evidence'][0]
    if mutation=='scope_count':packet['assessments'].pop()
    elif mutation=='scope_duplicate':packet['assessments'][-1]=deepcopy(r)
    elif mutation=='source':r['source_ids']=['other']
    elif mutation=='allowed':r['proposed_outcome']='allowed'
    elif mutation=='automatic':packet['automatic_admission']=True
    elif mutation=='admitted':packet['training_admitted']=400
    elif mutation=='distribution':packet['distribution_ready']=True
    elif mutation=='human_claim':r['assessor']['kind']='human'
    elif mutation=='factor_missing':r['fair_use_factors'].pop('amount')
    elif mutation=='factor_null':r['fair_use_factors']['amount']=None
    elif mutation=='review_state':r['review_state']='deferred'
    elif mutation=='deferred':packet['assessments'][3]['review_state']='reviewed'
    elif mutation=='evidence_hash':e['reference']['sha256']='0'*64
    elif mutation=='path_escape':e['reference']['path']='../outside.html'
    elif mutation=='evidence_id_escape':e['evidence_id']='../outside'
    elif mutation=='unbound':e.pop('reference')
    else:e['outcome']='failed'
    with pytest.raises(ValueError):u.validate_assessments(packet,{s['publisher'] for s in sources},sources,tmp_path)


def test_preserved_failed_checks_are_not_successful_policy_captures(tmp_path):
    packet,sources=assessment_fixture(tmp_path);packet['evidence'][0].update(outcome='failed',error='HTTP 403')
    u.validate_assessments(packet,{s['publisher'] for s in sources},sources,tmp_path)
    assert all(r['proposed_outcome']=='unresolved' for r in packet['assessments'])


def test_passage_payload_omits_full_sources_private_identity_paths_and_capture_files():
    r=sample(1);data=r.model_dump(mode='json');data['entities'][0]['identity']={'state':'unresolved','reference_url':'D:/private/evidence.json'}
    r=AnnotationRecord.model_validate_json(json.dumps(data));entry=source_entry(r,'private/body.txt')
    entry.update(raw_path='private/raw.html',capture_path='private/source.json')
    payload=u.passage_payload(r,entry)
    assert payload['text']==r.text and payload['text_sha256']==r.text_sha256
    assert 'text' not in payload['source'] and 'text_path' not in payload['source']
    assert 'private/' not in json.dumps(payload) and 'D:/' not in json.dumps(payload)
    assert payload['entities'][0]['identity']['reference_withheld_private_or_nonpublic']
    assert payload['dataset_license'] is None and payload['admission_status']=='research_only'


def test_whole_article_passage_is_metadata_only_without_changing_private_record():
    r=sample(2,full=True);before=r.model_dump();p=u.passage_payload(r,source_entry(r,'private.txt'))
    assert p['text'] is None and p['payload_status']=='withheld_complete_article'
    assert all('text' not in e for e in p['entities']) and not p['facts'] and not p['relations']
    assert r.model_dump()==before


def test_union_amounts_full_copy_counts_and_unknown_rights_are_distinct(tmp_path):
    r=sample(0);entry=source_entry(r,'body.txt');(tmp_path/'body.txt').write_text(r.source.text,encoding='utf-8')
    rows=u.measure_sources([r,r],[],[entry],tmp_path)
    assert rows[0]['selected_unique_passage_characters']==len(r.text)
    assert rows[0]['complete_article_characters']==len(r.source.text)
    assert rows[0]['retained_complete_article_fraction']==1
    assert rows[0]['clean_full_article_representations_in_new_private_bundle']==4
    assert rows[0]['rights_evidence']['author_identity']=='unknown'


def test_rights_inspection_distinguishes_captured_credits_from_ownership(tmp_path):
    r=sample(1);p=tmp_path/'raw.html'
    p.write_text('<meta name="author" content="Reporter Name"><main>Copyright; all rights reserved</main>',encoding='utf-8')
    entry=source_entry(r,'body.txt');entry['raw_path']='raw.html'
    rights=u.inspect_rights(r.source,entry,tmp_path)
    assert rights['structured_authors']==['Reporter Name'] and not rights['rights_holder_verified']
    assert 'copyright' in {s.casefold() for s in rights['raw_site_notice_markers']}


def integration_fixture(tmp_path,monkeypatch):
    artifacts=tmp_path/'backend/training/flood_ner/artifacts';artifacts.mkdir(parents=True)
    cohort=artifacts/'cohort';context=artifacts/'context';cohort.mkdir();context.mkdir()
    records=[sample(i,'english' if i<12 else 'taglish') for i in range(24)]+[sample(30,full=True)]
    contexts=[records[0].model_copy(update={'annotation_profile':'context-rich-v1'})]
    sources=[]
    for r in records:
        p=artifacts/(r.source.source_id+'.txt');p.write_bytes(r.source.text.encode())
        sources.append(source_entry(r,p.relative_to(tmp_path)))
    write_jsonl(cohort/'grouped_annotations.jsonl',records);write_jsonl(context/'context_annotations.jsonl',contexts)
    manifest={'files':{'grouped_annotations.jsonl':u.digest(cohort/'grouped_annotations.jsonl')}}
    (cohort/'partition_manifest.json').write_bytes(json_bytes(manifest))
    (context/'manifest.json').write_bytes(json_bytes({'files':{'context_annotations.jsonl':u.digest(context/'context_annotations.jsonl')}}))
    packet,s_=assessment_fixture(tmp_path)
    old=artifacts/'old.json';old.write_text('{}');reference={'path':old.relative_to(tmp_path).as_posix(),'sha256':u.digest(old)}
    packet.update(original_packet=reference,original_review_forms=reference)
    packet['evidence'][0]['reference']['path']='evidence.html'
    packet_file=artifacts/'review.json';packet_file.write_bytes(json_bytes(packet))
    monkeypatch.setattr(u,'load_inputs',lambda *args:(records,contexts,sources,packet,manifest))
    return artifacts,cohort,context,packet_file,records


def test_packaging_has_stable_unicode_offsets_zip_holds_and_hashes(tmp_path,monkeypatch):
    artifacts,cohort,context,packet,records=integration_fixture(tmp_path,monkeypatch)
    before=[r.model_dump() for r in records]
    a=u.prepare_use_bundle(cohort,context,packet,artifacts/'bundle-a',tmp_path)
    b=u.prepare_use_bundle(cohort,context,packet,artifacts/'bundle-b',tmp_path)
    assert a==b and a['download_metadata_only_records']==1
    assert a['training_admitted']==0 and not a['distribution_ready']
    assert [r.model_dump() for r in records]==before
    for name,digest in a['files'].items():assert u.digest(artifacts/'bundle-a'/name)==digest
    with (artifacts/'bundle-a/01-private-study/article-links.csv').open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            local=artifacts/'bundle-a/01-private-study'/row['local_article_folder']
            assert json.loads((local/'source.json').read_text(encoding='utf-8'))['source_id']==row['source_id']
    for item in json.loads((artifacts/'bundle-a/relocation-index.json').read_text(encoding='utf-8')):
        assert u.digest(artifacts/'bundle-a'/item['bundle_relative_path'])==item['sha256']
    archive=artifacts/'bundle-a/03-download-candidate/research-only-candidate.zip'
    with zipfile.ZipFile(archive) as z:
        assert not any('articles/' in name or 'private' in name for name in z.namelist())
        rows=[json.loads(l) for l in z.read('location-passages.jsonl').decode('utf-8').split('\n') if l.strip()]
        for row in rows:
            if row['text'] is None:continue
            assert text_hash(row['text'])==row['text_sha256']
            for e in row['entities']:assert row['text'][e['start']:e['end']]==e['text']
        assert 'distribution unresolved' in z.read('README.md').decode()
    with pytest.raises(ValueError):u.prepare_use_bundle(cohort,context,packet,artifacts/'bundle-a',tmp_path)
    with pytest.raises(ValueError):u.prepare_use_bundle(cohort,context,packet,tmp_path/'outside',tmp_path)


def test_copy_failure_preserves_partial_outcome_and_cannot_be_retried_in_place(tmp_path,monkeypatch):
    artifacts,cohort,context,packet,_=integration_fixture(tmp_path,monkeypatch)
    def fail(*args):raise OSError('constructed copy failure')
    monkeypatch.setattr(u.shutil,'copyfile',fail)
    with pytest.raises(OSError):u.prepare_use_bundle(cohort,context,packet,artifacts/'failed',tmp_path)
    failure=json.loads((artifacts/'failed/failure.json').read_text())
    assert failure['state']=='failed_incomplete_bundle' and not failure['distribution_ready']
    assert not (artifacts/'failed/manifest.json').exists()


def test_corrected_context_and_review_versions_keep_predecessor_evidence(tmp_path,monkeypatch):
    artifacts,cohort,context,packet_path,_=integration_fixture(tmp_path,monkeypatch)
    data=json.loads((context/'manifest.json').read_text());data['context_revision']='contextual-v3'
    (context/'manifest.json').write_bytes(json_bytes(data))
    records,contexts,sources,packet,manifest=u.load_inputs()
    packet['packet_revision']='v3';packet['previous_review_packet']=packet['original_packet']
    packet_path.write_bytes(json_bytes(packet))
    result=u.prepare_use_bundle(cohort,context,packet_path,artifacts/'corrected',tmp_path)
    assert result['context_revision']=='contextual-v3' and result['packet_revision']=='v3'
    assert '01-private-study/contextual-v3/context_annotations.jsonl' in result['files']
    assert '04-use-review/review-packet-v3.json' in result['files']
    assert '04-use-review/previous_review_packet.json' in result['files']
    assert not (artifacts/'corrected/01-private-study/contextual-v2').exists()


@pytest.mark.parametrize('revision',['../escape','contextual-v3/escape',None])
def test_invalid_context_revision_cannot_create_a_package(tmp_path,monkeypatch,revision):
    artifacts,cohort,context,packet,_=integration_fixture(tmp_path,monkeypatch)
    data=json.loads((context/'manifest.json').read_text());data['context_revision']=revision
    (context/'manifest.json').write_bytes(json_bytes(data))
    with pytest.raises(ValueError,match='revision names'):
        u.prepare_use_bundle(cohort,context,packet,artifacts/'rejected',tmp_path)
    assert not (artifacts/'rejected').exists()


def test_manifest_and_context_path_escape_are_rejected(tmp_path):
    (tmp_path/'manifest.json').write_text(json.dumps({'files':{'../escape':'0'*64}}))
    with pytest.raises(ValueError):u.verify_directory(tmp_path,'manifest.json')


def test_bad_review_packet_cannot_bind_an_existing_frozen_cohort(tmp_path,monkeypatch):
    cohort=tmp_path/'cohort';context=tmp_path/'context';cohort.mkdir();context.mkdir()
    (cohort/'partition_manifest.json').write_text('{}')
    (context/'manifest.json').write_text(json.dumps({'files':{'dummy.txt':text_hash('dummy')}}))
    (context/'dummy.txt').write_text('dummy')
    p=tmp_path/'review.json';p.write_text(json.dumps({'dataset_manifest_sha256':'0'*64}))
    monkeypatch.setattr(u,'load_frozen_cohort',lambda *args: ([],None,{'files':{}}))
    with pytest.raises(ValueError,match='manifest identity'):u.load_inputs(cohort,context,p,tmp_path)


@pytest.mark.parametrize('value',[{'author':'Complete article body'},{'raw_path':'capture.html'},
                                {'nested':[{'author':'D:/private/author.txt'}]}])
def test_nested_attribution_cannot_leak_full_articles_or_private_paths(value):
    with pytest.raises(ValueError):u.check_share_payload(value,{'Complete article body'})


def test_jsonl_roundtrip_preserves_unicode_separators_and_offsets(tmp_path):
    r=sample(2);p=u.passage_payload(r,source_entry(r,'body.txt'))
    p['text']=p['text'].replace('—','\u2028');p['text_sha256']=text_hash(p['text'])
    target=tmp_path/'samples.jsonl';write_jsonl(target,[p])
    assert len(target.read_bytes().splitlines())==1
    row=json.loads(target.read_bytes());assert row['text']==p['text']
    for entity in row['entities']:assert row['text'][entity['start']:entity['end']]==entity['text']


def test_invalid_context_or_capture_binding_never_creates_an_output(tmp_path,monkeypatch):
    artifacts=tmp_path/'backend/training/flood_ner/artifacts';artifacts.mkdir(parents=True)
    def invalid(*args):raise ValueError('context source/hash identity mismatch')
    monkeypatch.setattr(u,'load_inputs',invalid)
    with pytest.raises(ValueError,match='source/hash'):
        u.prepare_use_bundle(tmp_path/'cohort',tmp_path/'context',tmp_path/'review.json',artifacts/'rejected',tmp_path)
    assert not (artifacts/'rejected').exists()


def test_cli_preserves_research_only_status_and_propagates_validation_failures(tmp_path,monkeypatch,capsys):
    from training.flood_ner.cli import main
    args=['prepare-use-bundle','--cohort',str(tmp_path/'cohort'),'--context',str(tmp_path/'context'),
          '--review-packet',str(tmp_path/'review.json'),'--output',str(tmp_path/'out')]
    monkeypatch.setattr(u,'prepare_use_bundle',lambda *a:{'state':'prepared_research_only','training_admitted':0,'files':{}})
    assert main(args)==0 and json.loads(capsys.readouterr().out)['training_admitted']==0
    def fail(*a):raise ValueError('frozen binding failed')
    monkeypatch.setattr(u,'prepare_use_bundle',fail)
    assert main(args)==1 and 'frozen binding failed' in capsys.readouterr().err


@pytest.mark.parametrize('mutation',['draft','incomplete','admitted','reuse_allowed','constructed','count','language','split'])
def test_research_cohort_requires_complete_review_and_unchanged_holds(mutation):
    records=[]
    for i in range(400):
        split='train' if i<280 else 'dev' if i<340 else 'test'
        lang='english' if (i<140 or 280<=i<310 or 340<=i<370) else 'taglish'
        records.append(sample(i,lang,split=split))
    u.validate_research_cohort(records)
    r=records[0]
    if mutation=='draft':records[0]=r.model_copy(update={'review_status':'draft'})
    elif mutation=='incomplete':records[0]=r.model_copy(update={'complete':False})
    elif mutation=='admitted':records[0]=r.model_copy(update={'source':r.source.model_copy(update={'admission_status':'training_admitted'})})
    elif mutation=='reuse_allowed':records[0]=r.model_copy(update={'source':r.source.model_copy(update={'reuse_status':'allowed'})})
    elif mutation=='constructed':records[0]=r.model_copy(update={'quality':'constructed'})
    elif mutation=='count':records.pop()
    elif mutation=='language':records[0]=r.model_copy(update={'passage_language':'taglish'})
    else:records[0]=r.model_copy(update={'split':'test'})
    with pytest.raises(ValueError,match='complete accepted'):u.validate_research_cohort(records)
