"""Offline research packaging and scoped use evidence; never grants admission."""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
from typing import Any
import zipfile
from urllib.parse import urlsplit

from .annotation.schema import AnnotationRecord, PLACE_LABELS
from .collection import article_key, publisher_for, verify_capture_files
from .contextual_pilot import ContextReview, validate_contextual_pilot
from .qualification import _bound_file, load_frozen_cohort
from .sources import CaptureParser, json_bytes, read_jsonl, write_jsonl

SCOPES = ('academic_training_evaluation', 'paper_excerpts', 'dataset_distribution', 'production_use', 'model_distribution')
CURRENT_SCOPES = frozenset(SCOPES[:3])
HOLD = 'Research-only; distribution unresolved. No dataset license or training admission granted.'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_reference(value: dict, root: Path) -> Path:
    if not isinstance(value, dict) or not {'path', 'sha256'} <= value.keys():
        raise ValueError('hash-bound local evidence reference required')
    path = _bound_file(root, value['path'])
    if digest(path) != value['sha256']:
        raise ValueError('review evidence hash mismatch')
    return path


def verify_directory(folder: Path, filename: str) -> dict:
    data = json.loads((folder / filename).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('files'), dict) or not data['files']:
        raise ValueError('hash-bound frozen directory manifest required')
    for name, sha in data['files'].items():
        if not isinstance(name, str) or Path(name).name != name or '/' in name or '\\' in name:
            raise ValueError('frozen manifest file names must be local basenames')
        if digest(_bound_file(folder, name)) != sha:
            raise ValueError('frozen context file hash mismatch')
    return data


def validate_assessments(packet: dict, publishers: set[str], sources: list[dict], root: Path) -> None:
    if (packet.get('schema_version') != 'lanes-study-use-review-v2' or packet.get('automatic_admission') is not False
            or packet.get('training_admitted') != 0 or packet.get('distribution_ready') is not False):
        raise ValueError('review must preserve unresolved admission and distribution holds')
    evidence = packet.get('evidence', [])
    if (not isinstance(evidence, list) or not evidence or any(not isinstance(e, dict) for e in evidence)
            or len({e.get('evidence_id') for e in evidence}) != len(evidence)):
        raise ValueError('unique captured review evidence required')
    evidence_ids = set()
    for item in evidence:
        if not isinstance(item.get('evidence_id'), str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,95}', item['evidence_id']):
            raise ValueError('safe evidence identifier required')
        evidence_ids.add(item['evidence_id'])
        if item.get('outcome') not in {'captured', 'failed'} or not item.get('url') or not item.get('checked_at'):
            raise ValueError('review evidence needs retrieval identity and outcome')
        if item.get('outcome') == 'captured' and not item.get('reference'):
            raise ValueError('captured evidence must bind saved bytes')
        if item.get('reference'): verified_reference(item['reference'], root)
        if item.get('outcome') == 'failed' and not item.get('error'):
            raise ValueError('failed policy check needs explicit error')
    rows = packet.get('assessments', [])
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ValueError('assessment rows must be objects')
    keys = [(r.get('publisher'), r.get('scope')) for r in rows]
    if len(keys) != 15 or set(keys) != {(p, s) for p in publishers for s in SCOPES}:
        raise ValueError('fifteen distinct publisher/use assessments required')
    for row in rows:
        expected_ids = {s['source_id'] for s in sources if s['publisher'] == row['publisher']}
        if set(row.get('source_ids', [])) != expected_ids or row.get('proposed_outcome') != 'unresolved':
            raise ValueError('review source scope or unresolved outcome mismatch')
        if row['scope'] in CURRENT_SCOPES:
            assessor = row.get('assessor')
            if (row.get('review_state') != 'reviewed' or not isinstance(assessor, dict)
                    or assessor.get('kind') != 'ai' or not assessor.get('name') or not assessor.get('reviewed_at')
                    or set(row.get('fair_use_factors', {})) != {'purpose', 'nature', 'amount', 'market_effect'}
                    or any(not isinstance(v, str) or not v.strip() for v in row['fair_use_factors'].values())
                    or not row.get('uncertainties') or not row.get('evidence_ids')
                    or not set(row['evidence_ids']) <= evidence_ids):
                raise ValueError('reviewed scopes require actual AI provenance, four factors and bound evidence')
        elif row.get('review_state') != 'deferred':
            raise ValueError('production and model-distribution assessment remain deferred')


def validate_research_cohort(locations: list[AnnotationRecord]) -> None:
    if (len(locations) != 400 or Counter(r.passage_language for r in locations) != Counter(english=200, taglish=200)
            or Counter(r.split for r in locations) != Counter(train=280, dev=60, test=60)
            or any(r.source.admission_status != 'research_only' or r.source.reuse_status == 'allowed'
                   or r.quality != 'silver' or r.source.origin != 'captured_original'
                   or r.review_status != 'accepted' or not r.complete for r in locations)):
        raise ValueError('requires the complete accepted 400-record research-only silver cohort')


def load_inputs(cohort: Path, context: Path, packet_file: Path, root: Path) -> tuple:
    locations, nlp, manifest = load_frozen_cohort(cohort)
    for name in manifest['files']:
        if Path(name).name != name or '/' in name or '\\' in name:
            raise ValueError('frozen cohort file names must be local basenames')
    context_manifest = verify_directory(context, 'manifest.json')
    packet = json.loads(packet_file.read_text(encoding='utf-8'))
    if not isinstance(packet, dict): raise ValueError('review packet must be an object')
    cohort_sha = digest(cohort / 'partition_manifest.json')
    context_sha = digest(context / 'manifest.json')
    if (packet.get('dataset_manifest_sha256') != cohort_sha or packet.get('context_manifest_sha256') != context_sha
            or context_manifest.get('location_manifest_sha256') != cohort_sha):
        raise ValueError('review/cohort/context manifest identity mismatch')
    originals = json.loads(verified_reference(packet['original_packet'], root).read_text(encoding='utf-8'))
    verified_reference(packet['original_review_forms'], root)
    if (originals.get('dataset_manifest_sha256') != cohort_sha or originals.get('context_manifest_sha256') != context_sha
            or originals.get('articles') != 139 or originals.get('samples') != 400):
        raise ValueError('original study-use packet binding mismatch')
    validate_research_cohort(locations)
    contexts = read_jsonl(context / 'context_annotations.jsonl', AnnotationRecord)
    reviews = [
        ContextReview.model_validate_json(json.dumps(row)) for row in json.loads((context / 'category_reviews.json').read_text(encoding='utf-8'))]
    checked = validate_contextual_pilot(locations, contexts, reviews, nlp)
    if checked['errors'] or len(contexts) != 40 or not context_manifest.get('complete'):
        raise ValueError('contextual-v2 pairing/review requirements failed')
    sources = json.loads(verified_reference(packet['source_register'], root).read_text(encoding='utf-8'))
    actual_sources = {(r.source.source_id, r.source.capture_version): r.source for r in locations}
    if (len(sources) != 139 or len(actual_sources) != 139
            or {(s['source_id'], s['capture_version']) for s in sources} != set(actual_sources)):
        raise ValueError('selected 139-source register mismatch')
    for s in sources:
        original = actual_sources[(s['source_id'], s['capture_version'])]
        if (s['text_sha256'] != original.text_sha256 or article_key(s['url']) != article_key(original.url)
                or s['status'] != 'accepted' or s['admission_status'] != 'research_only'):
            raise ValueError('source identity/hash/review mismatch')
    errors = verify_capture_files(sources, root)
    if errors: raise ValueError('capture/publication evidence failed: ' + '; '.join(errors))
    publishers = {s['publisher'] for s in sources}
    if publishers != {'ABS-CBN News', 'GMA News', 'Philstar'}:
        raise ValueError('three frozen publishers required')
    validate_assessments(packet, publishers, sources, root)
    return locations, contexts, sources, packet, manifest


def select_appendix(records: list[AnnotationRecord]) -> tuple[list[AnnotationRecord], dict]:
    selected = []; labels = set(); publishers = set(); counts = Counter()
    remaining = [r for r in records if r.split == 'train' and r.text != r.source.text]
    while len(selected) < 10:
        candidates = [r for r in remaining if counts[r.passage_language] < 5]
        if not candidates: raise ValueError('ten partial-article training examples, five per language, unavailable')
        winner = min(candidates, key=lambda r: (-len({e.label for e in r.entities} - labels),
                     -int((publisher_for(r.source.url) or r.source.publisher) not in publishers), r.record_id))
        selected.append(winner); remaining.remove(winner); counts[winner.passage_language] += 1
        labels.update(e.label for e in winner.entities); publishers.add(publisher_for(winner.source.url) or winner.source.publisher)
    return selected, {'languages': dict(counts), 'classes': sorted(labels), 'publishers': sorted(publishers),
                      'all_six_classes_covered': PLACE_LABELS <= labels, 'training_only': True,
                      'selection': 'greedy new class coverage, then new publisher coverage, then record ID; five per language'}


def inspect_rights(source: Any, entry: dict, root: Path) -> dict:
    authors = []; parse_error = None; raw = ''
    if entry.get('raw_path'):
        try:
            raw = _bound_file(root, entry['raw_path']).read_bytes().decode('utf-8')
            parser = CaptureParser(); parser.feed(raw)
            meta = parser.article_metadata()
            author = meta.get('author') or parser.meta.get('author')
            for a in author if isinstance(author, list) else [author]:
                if isinstance(a, str) and a.strip(): authors.append(a.strip())
                elif isinstance(a, dict) and isinstance(a.get('name'), str): authors.append(a['name'])
            if not authors and raw.lstrip().startswith('{'):
                snapshot = json.loads(raw)
                for h in snapshot.get('headers', []):
                    if re.match(r'^By\s+', h, re.I): authors.append(h)
        except (ValueError, UnicodeError) as exc: parse_error = str(exc)
    bylines = [{'start': m.start(), 'end': m.end(), 'text': m.group()} for m in
               re.finditer(r'(?m)^By[ \t]+[^\r\n]{1,160}', source.text)]
    markers = [{'start': m.start(), 'end': m.end(), 'text': m.group()} for m in
               re.finditer(r'\b(?:Reuters|Associated Press|Agence France-Presse|AFP|AP)\b', source.text, re.I)]
    notices = sorted(set(re.findall(r'(?i)copyright|all rights reserved', raw)))
    return {'structured_authors': sorted(set(authors)), 'body_byline_evidence': bylines, 'agency_marker_evidence': markers,
            'raw_site_notice_markers': notices, 'parse_error': parse_error,
            'author_identity': 'captured_credit' if authors or bylines else 'unknown',
            'rights_holder_verified': False, 'note': 'Agency mentions/site footers are cues, not proof of ownership or article syndication.'}


def measure_sources(records: list[AnnotationRecord], contexts: list[AnnotationRecord], sources: list[dict], root: Path) -> list[dict]:
    rows = []; context_counts = Counter(r.source.source_id for r in contexts)
    for entry in sorted(sources, key=lambda s: s['source_id']):
        selected = [r for r in records if r.source.source_id == entry['source_id']]; source = selected[0].source
        merged = []
        for a, b in sorted((r.passage_start, r.passage_end) for r in selected):
            if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
            else: merged.append([a, b])
        chars = sum(b-a for a,b in merged)
        rows.append({'source_id': source.source_id, 'capture_version': source.capture_version,
                     'article_key': article_key(source.url), 'publisher': entry['publisher'], 'source_text_sha256': source.text_sha256,
                     'complete_article_characters': len(source.text), 'selected_unique_passage_characters': chars,
                     'selected_fraction_of_article': chars / len(source.text), 'union_intervals': merged,
                     'samples': len(selected), 'whole_article_passage_ids': [r.record_id for r in selected if r.text == source.text],
                     'retained_complete_article_fraction': 1.0,
                     'clean_full_article_representations_in_new_private_bundle': len(selected) + context_counts[source.source_id] + 2,
                     'copy_count_scope': 'source JSON + body file + location source embeddings + context source embeddings; excludes raw markup and prior folders',
                     'rights_evidence': inspect_rights(source, entry, root)})
    return rows


def passage_payload(record: AnnotationRecord, entry: dict) -> dict:
    withheld = record.text == record.source.text
    entities = [e.model_dump(mode='json') for e in record.entities]
    for entity in entities:
        identity = entity.get('identity')
        if identity and identity.get('reference_url'):
            parts = urlsplit(identity['reference_url'])
            if parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password:
                identity['reference_url'] = None
                identity['reference_withheld_private_or_nonpublic'] = True
    facts = [f.model_dump(mode='json') for f in record.facts]
    relations = [r.model_dump(mode='json') for r in record.relations]
    if withheld:
        # Whole-article samples retain only structural metadata in this candidate.
        entities = [{k:v for k,v in e.items() if k != 'text'} for e in entities]
        facts = []; relations = []
    return {'schema_version': 'lanes-passage-share-candidate-v1', 'record_id': record.record_id,
            'payload_status': 'withheld_complete_article' if withheld else 'passage_text_included',
            'text': None if withheld else record.text, 'text_sha256': record.text_sha256,
            'language': record.passage_language, 'split': record.split, 'passage_start': record.passage_start, 'passage_end': record.passage_end,
            'source': {k:entry.get(k) for k in ('source_id','capture_version','url','canonical_url','publisher','title','publication_date','published_at','captured_at','text_sha256')},
            'entities': entities, 'facts': facts, 'relations': relations, 'quality': record.quality,
            'teacher': record.teacher, 'reviewer': record.reviewer, 'annotation_revision': record.annotation_revision,
            'admission_status': 'research_only', 'distribution_status': 'unresolved', 'dataset_license': None}


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    stream = io.StringIO(newline=''); writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader(); writer.writerows({k:r.get(k) for k in columns} for r in rows)
    path.write_bytes(stream.getvalue().encode('utf-8'))


def check_share_payload(value: Any, complete_texts: set[str]) -> None:
    """Check nested metadata too; removing source.text alone is insufficient."""
    if isinstance(value, dict):
        if {'raw_path', 'text_path', 'capture_path', 'model_dir'} & value.keys():
            raise ValueError('private capture/model fields cannot enter the download candidate')
        for v in value.values(): check_share_payload(v, complete_texts)
    elif isinstance(value, list):
        for v in value: check_share_payload(v, complete_texts)
    elif isinstance(value, str):
        if value in complete_texts:
            raise ValueError('complete article body cannot enter the download candidate')
        if re.search(r'(?:(?<![A-Za-z0-9_])[A-Za-z]:[\\/]|(?:^|\s)/(?:Users|home)/)', value):
            raise ValueError('private filesystem path cannot enter the download candidate')


def prepare_use_bundle(cohort: Path, context: Path, review_packet: Path, output: Path, root: Path) -> dict:
    output = output.resolve(); artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    if not output.is_relative_to(artifacts) or output.exists():
        raise ValueError('bundle destination must be new and under ignored artifacts')
    records, contexts, sources, packet, manifest = load_inputs(cohort, context, review_packet, root)
    context_data = json.loads((context / 'manifest.json').read_text(encoding='utf-8'))
    context_revision = context_data.get('context_revision', 'contextual-v2')
    packet_revision = packet.get('packet_revision', 'v2')
    if (not isinstance(context_revision, str) or not re.fullmatch(r'contextual-v[1-9][0-9]*', context_revision)
            or not isinstance(packet_revision, str) or not re.fullmatch(r'v[1-9][0-9]*', packet_revision)):
        raise ValueError('safe context and packet revision names required')
    appendix, coverage = select_appendix(records)
    amounts = measure_sources(records, contexts, sources, root)
    by_source = {s['source_id']:s for s in sources}
    sections = [output/n for n in ('01-private-study','02-paper-appendix-draft','03-download-candidate','04-use-review')]
    output.mkdir(parents=True); private, paper, candidate, review = sections
    for p in sections: p.mkdir()
    relocation = []; article_folders = {}
    try:
        for folder, target, name in [(cohort, private/'cohort', 'partition_manifest.json'), (context, private/context_revision, 'manifest.json')]:
            target.mkdir(); data=json.loads((folder/name).read_text(encoding='utf-8'))
            for item in [name, *data['files']]: shutil.copyfile(_bound_file(folder,item),target/item)
        for i, entry in enumerate(sorted(sources, key=lambda s:s['source_id']),1):
            folder=private/'articles'/f'{i:03d}';folder.mkdir(parents=True)
            article_folders[entry['source_id']] = f'articles/{i:03d}'
            source=next(r.source for r in records if r.source.source_id==entry['source_id'])
            (folder/'source.json').write_bytes(json_bytes(source.model_dump(mode='json')))
            (folder/'capture-entry.json').write_bytes(json_bytes(entry))
            shutil.copyfile(_bound_file(root,entry['text_path']),folder/'complete-article.txt')
            relocation.append({'original_relative_path': entry['text_path'],
                               'bundle_relative_path': (folder/'complete-article.txt').relative_to(output).as_posix(),
                               'sha256': entry['text_sha256']})
            if entry.get('raw_path'):
                raw=_bound_file(root,entry['raw_path']);shutil.copyfile(raw,folder/('capture-raw'+raw.suffix))
                relocation.append({'original_relative_path': entry['raw_path'],
                                   'bundle_relative_path': (folder/('capture-raw'+raw.suffix)).relative_to(output).as_posix(),
                                   'sha256': digest(raw)})
        article_links=[{k:s.get(k) for k in ('source_id','publisher','title','url','publication_date')} for s in sources]
        for row in article_links: row['local_article_folder'] = article_folders[row['source_id']]
        sample_links=[{'record_id':r.record_id,'source_id':r.source.source_id,'url':r.source.url,'language':r.passage_language,
                       'split':r.split,'local_article_folder':article_folders[r.source.source_id]} for r in records]
        write_csv(private/'article-links.csv',article_links,['source_id','publisher','title','url','publication_date','local_article_folder'])
        write_csv(private/'sample-links.csv',sample_links,['record_id','source_id','url','language','split','local_article_folder'])
        appendix_rows=[passage_payload(r,by_source[r.source.source_id]) for r in appendix]
        write_jsonl(paper/'appendix-samples.jsonl',appendix_rows)
        text='# Paper appendix draft\n\n'+HOLD+'\n\nTen training passages; AI silver annotations, not independently verified gold.\n'
        for r in appendix:
            s=by_source[r.source.source_id]
            text+=f'\n## {r.record_id} ({r.passage_language})\n\n{s["publisher"]}: {s["title"]}\n\nSource: {s["url"]}; published: {s["publication_date"]}\n\n```text\n{r.text}\n```\n\n'
            text+='| Start | End | Label | Text |\n|---:|---:|---|---|\n'
            for e in r.entities:
                escaped = e.text.replace('|', '\\|')
                text+=f'| {e.start} | {e.end} | {e.label} | {escaped} |\n'
        (paper/'appendix-draft.md').write_text(text,encoding='utf-8',newline='\n')
        (paper/'coverage.json').write_bytes(json_bytes(coverage))
        payloads=[passage_payload(r,by_source[r.source.source_id]) for r in records]
        context_payloads=[passage_payload(r,by_source[r.source.source_id]) for r in contexts]
        # Attribution evidence includes captured author credits, never private raw-file paths.
        attribution=[{'source_id':r['source_id'],'publisher':r['publisher'], 'rights_evidence':r['rights_evidence']} for r in amounts]
        check_share_payload([payloads, context_payloads, attribution], {r.source.text for r in records})
        write_jsonl(candidate/'location-passages.jsonl',payloads);write_jsonl(candidate/'contextual-pairs.jsonl',context_payloads)
        (candidate/'attribution.json').write_bytes(json_bytes(attribution))
        (candidate/'README.md').write_text('# Download candidate\n\n'+HOLD+'\n\nThis is a private research candidate, not a DocBin training export. Full-article passages have metadata-only placeholders. Context pairs do not add samples. No full capture bodies, HTML, private paths or model weights are included.\n',encoding='utf-8')
        with zipfile.ZipFile(candidate/'research-only-candidate.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
            for p in sorted(candidate.iterdir()):
                if p.suffix=='.zip':continue
                info=zipfile.ZipInfo(p.name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                archive.writestr(info,p.read_bytes())
        shutil.copyfile(review_packet,review/f'review-packet-{packet_revision}.json')
        for key in ('original_packet','original_review_forms'):
            shutil.copyfile(verified_reference(packet[key],root),review/(key+'.json'))
        for key in ('previous_review_packet', 'previous_study_packet'):
            if key in packet:
                previous = verified_reference(packet[key], root)
                shutil.copyfile(previous, review/(key+'.json'))
                relocation.append({'original_relative_path': packet[key]['path'],
                                   'bundle_relative_path': (review/(key+'.json')).relative_to(output).as_posix(),
                                   'sha256': digest(previous)})
        for evidence in packet['evidence']:
            if evidence.get('reference'):
                p=verified_reference(evidence['reference'],root);shutil.copyfile(p,review/(evidence['evidence_id']+p.suffix))
                relocation.append({'original_relative_path': evidence['reference']['path'],
                                   'bundle_relative_path': (review/(evidence['evidence_id']+p.suffix)).relative_to(output).as_posix(),
                                   'sha256': digest(p)})
        (output/'relocation-index.json').write_bytes(json_bytes(relocation))
        (review/'source-amounts-and-rights.json').write_bytes(json_bytes(amounts))
        forms=[dict(r,final_reviewer=None,final_review_date=None,final_outcome='unresolved',retention_period=None,institutional_requirements=None) for r in packet['assessments']]
        (review/'editable-decision-forms.json').write_bytes(json_bytes(forms))
        withheld=[r['record_id'] for r in payloads if r['payload_status']=='withheld_complete_article']
        report={'schema_version':'lanes-study-use-bundle-v1','state':'prepared_research_only','samples':len(records),'articles':len(sources),
                'contextual_pairs':len(contexts),'additional_samples_from_context':0,'appendix_samples':len(appendix),'appendix_coverage':coverage,
                'download_text_records':len(payloads)-len(withheld),'download_metadata_only_records':len(withheld),'withheld_record_ids':withheld,
                'download_context_text_records':sum(r['text'] is not None for r in context_payloads),
                'assessments_reviewed':9,'assessments_deferred':6,'scoped_outcomes_unresolved':15,
                'training_admitted':0,'exported_docbin_records':0,'distribution_ready':False,'dataset_license':None,
                'dataset_manifest_sha256':digest(cohort/'partition_manifest.json'),'context_manifest_sha256':digest(context/'manifest.json'),
                'review_packet_sha256':digest(review_packet),'retention_period':None,'external_backup_performed':False,
                'article_body_characters':sum(r['complete_article_characters'] for r in amounts),
                'selected_unique_passage_characters':sum(r['selected_unique_passage_characters'] for r in amounts),
                'clean_full_article_representations_in_new_private_bundle':sum(r['clean_full_article_representations_in_new_private_bundle'] for r in amounts)}
        if 'context_revision' in context_data:
            report['context_revision'] = context_revision
        if 'packet_revision' in packet:
            report['packet_revision'] = packet_revision
        (output/'START-HERE.md').write_text('# 400-sample study folder\n\n'+HOLD+'\n\n01-private-study: [article links and saved-folder index](01-private-study/article-links.csv), [sample links](01-private-study/sample-links.csv), complete retained evidence and frozen data. Local article folders in both CSVs are relative to 01-private-study/.\n\n02-paper-appendix-draft: [ten training examples](02-paper-appendix-draft/appendix-draft.md) for possible paper use.\n\n03-download-candidate: passage-only data and local ZIP; whole-article samples are withheld as metadata-only records.\n\n04-use-review: evidence, AI assessments and [editable unresolved forms](04-use-review/editable-decision-forms.json).\n\n[Relocation index](relocation-index.json) maps original evidence paths to verified copies inside this bundle; original provenance paths remain unchanged.\n\nThese are local copies, not an external backup or publication. '+f'Download candidate: {report["download_text_records"]} passage texts and {report["download_metadata_only_records"]} metadata-only entries; private study retains all 400.\n',encoding='utf-8')
        for p in sections: (p/'USE-STATUS.txt').write_text(HOLD+'\n',encoding='utf-8')
        report['files']={p.relative_to(output).as_posix():digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
        (output/'manifest.json').write_bytes(json_bytes(report))
        return report
    except (OSError,ValueError,KeyError,TypeError) as exc:
        (output/'failure.json').write_bytes(json_bytes({'state':'failed_incomplete_bundle','error':str(exc),'training_admitted':0,'distribution_ready':False}))
        raise
