"""Source-exact candidate passages for review; never labels or training admission."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from .annotation.schema import SourceCapture, StrictRecord, Language, text_hash
from .collection import article_key, validate_reviewed, verify_capture_files
from .sources import json_bytes, write_jsonl


REQUIRED_HOLDS = {'passage_language_review_pending','event_syndication_review_pending',
                  'editorial_bounds_and_caption_review_pending','annotation_not_started'}


def candidate_identity(source: SourceCapture, start: int, end: int) -> str:
    return 'candidate-' + text_hash(f'{source.source_id}|{source.capture_version}|{start}|{end}')[:20]


def editorial_flags(text: str, *, truncated: bool = False, missing_number_cue: bool = False) -> list[str]:
    """Review diagnostics only; truncation/caption/chrome are not flood labels."""
    flags = []
    if re.search(r'(?im)^\s*(?:ADVERTISEMENT|Facebook|Twitter|\+ Add GMA|Make this your preferred source|Subscribe|Publication metadata:)',text):
        flags.append('publisher_chrome_review_pending')
    if re.search(r'(?im)^\s*(?:Image:|Photo:|File photo|Courtesy)',text):
        flags.append('caption_origin_review_pending')
    if truncated:
        flags.append('truncated_article_scope_review_pending')
    if missing_number_cue:
        flags.append('numbered_locality_cue_outside_window_review_pending')
    return flags


class CandidatePassage(StrictRecord):
    schema_version: Literal['lanes-flood-ner-candidate-v1'] = 'lanes-flood-ner-candidate-v1'
    candidate_id: str = Field(pattern=r'^candidate-[a-f0-9]{20}$')
    source: SourceCapture
    article_key: str = Field(min_length=1)
    passage_start: int = Field(ge=0)
    passage_end: int = Field(gt=0)
    text: str
    text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    article_language: Language
    passage_language: Literal['unknown'] = 'unknown'
    review_status: Literal['proposed'] = 'proposed'
    admission_status: Literal['research_only'] = 'research_only'
    selection_method: Literal['body-anchor-context-window-v1'] = 'body-anchor-context-window-v1'
    proposed_event_group: str | None = None
    proposed_syndication_group: str | None = None
    case_cues: list[dict[str, Any]] = Field(default_factory=list)
    source_review_notes: list[str] = Field(default_factory=list)
    hold_reasons: list[str] = Field(min_length=1)

    @model_validator(mode='after')
    def exact_candidate(self) -> CandidatePassage:
        SourceCapture.model_validate(self.source.model_dump())
        if (self.passage_end > len(self.source.text) or self.passage_end <= self.passage_start
                or self.source.text[self.passage_start:self.passage_end] != self.text
                or text_hash(self.text) != self.text_sha256):
            raise ValueError('candidate passage must match unchanged source offsets/hash')
        if self.source.admission_status != 'research_only':
            raise ValueError('candidate review queue requires a research-only source')
        if self.article_key != article_key(self.source.url):
            raise ValueError('candidate article identity must match captured source')
        if self.candidate_id != candidate_identity(self.source,self.passage_start,self.passage_end):
            raise ValueError('candidate identity must match source version and passage bounds')
        required = set(REQUIRED_HOLDS)
        if self.source.reuse_status != 'allowed':
            required.add('reuse_assessment_pending')
        if self.source.raw_sha256 is None or self.source.captured_at is None:
            required.add('legacy_original_html_retrieval_gap')
        if (not required <= set(self.hold_reasons) or any(not h.strip() for h in self.hold_reasons)
                or len(set(self.hold_reasons)) != len(self.hold_reasons)):
            raise ValueError('unreviewed candidate must retain required review/provenance holds')
        for cue in self.case_cues:
            if not isinstance(cue.get('role'),str) or not cue['role'].strip():
                raise ValueError('candidate cue requires a nonempty research role')
            a, b = cue.get('start'), cue.get('end')
            if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(self.text)
                    or text_hash(self.text[a:b]) != cue.get('sha256')):
                raise ValueError('candidate cue must match unchanged passage offsets/hash')
        return self


def propose_passage(entry: dict[str, Any], source: SourceCapture, target_characters: int = 1800) -> CandidatePassage:
    """Keep a contiguous anchor/paragraph window. Editorial boundaries need review."""
    if target_characters < 1:
        raise ValueError('target characters must be positive')
    anchor = next((s for s in entry['evidence'] if s.get('role') == 'body_review_anchor'), entry['evidence'][0])
    text = source.text
    start = text.rfind('\n', 0, anchor['start']) + 1
    # Include a short immediate heading when it is not clearly publisher chrome.
    if start:
        previous = text.rfind('\n', 0, start - 1) + 1
        heading = text[previous:start].strip()
        if heading and len(heading) <= 80 and not re.search(r'^(?:By\b|Published\b|Updated\b|Publication metadata:|Image:|Facebook|Twitter)', heading, re.I):
            start = previous
    bound = min(len(text), max(anchor['end'], start + target_characters))
    boundary = text.find('\n', bound)
    end = boundary if boundary >= 0 else len(text)
    cues = [{'role':s.get('role','research_cue'), 'start':s['start']-start, 'end':s['end']-start, 'sha256':s['sha256']}
            for s in entry['evidence'] if s.get('role') != 'body_review_anchor' and start <= s['start'] < s['end'] <= end]
    holds = ['reuse_assessment_pending','passage_language_review_pending','event_syndication_review_pending',
             'editorial_bounds_and_caption_review_pending','annotation_not_started']
    if source.raw_sha256 is None or source.captured_at is None:
        holds.append('legacy_original_html_retrieval_gap')
    missing_number = ('numbered_locality_cue' in entry.get('case_types',[])
                      and not any(c['role']=='numbered_locality_cue' for c in cues))
    holds.extend(editorial_flags(text[start:end],truncated=end < len(text),missing_number_cue=missing_number))
    if 'measurement_role_ambiguity' in entry.get('case_types',[]):
        holds.append('measurement_role_review_pending')
    if end-start > target_characters*2:
        holds.append('long_paragraph_bounds_review')
    return CandidatePassage(candidate_id=candidate_identity(source,start,end), source=source, article_key=entry['article_key'],
        passage_start=start, passage_end=end, text=text[start:end], text_sha256=text_hash(text[start:end]),
        article_language=entry['language'], proposed_event_group=entry.get('event_group'),
        proposed_syndication_group=entry.get('syndication_group'), case_cues=cues,
        source_review_notes=entry.get('review_notes',[]), hold_reasons=holds)


def prepare_candidates(entries: list[dict[str, Any]], sources: list[SourceCapture], root: Path, output: Path) -> dict[str, Any]:
    errors = validate_reviewed(entries, {s.capture_version:s for s in sources}) + verify_capture_files(entries, root)
    if errors:
        raise ValueError('\n'.join(errors))
    accepted = [e for e in entries if e.get('status') == 'accepted']
    if not accepted:
        raise ValueError('no reviewed articles supplied')
    artifacts = (root/'backend/training/flood_ner/artifacts').resolve()
    if not output.resolve().is_relative_to(artifacts):
        raise ValueError('candidate bodies must stay under ignored training artifacts')
    if output.exists() and any(output.iterdir()):
        raise ValueError('candidate destination must be empty; preserve earlier review queues')
    by_version = {s.capture_version:s for s in sources}
    by_article = {e['article_key']:e for e in accepted}
    candidates = [propose_passage(e, by_version[e['capture_version']]) for e in sorted(accepted, key=lambda e:e['article_key'])]
    groups: dict[str, list[str]] = defaultdict(list)
    for candidate in candidates:
        groups[candidate.proposed_event_group or 'unresolved:'+candidate.article_key].append(candidate.source.source_id)
    metadata = [{**c.model_dump(mode='json', exclude={'source','text'}), 'source_id':c.source.source_id,
        'source_version':c.source.capture_version,'source_text_sha256':c.source.text_sha256,'source_url':c.source.url,
        'publisher':by_article[c.article_key]['publisher'],
        'publication_date':by_article[c.article_key]['publication_date'],'characters':len(c.text)} for c in candidates]
    group_queue = [{'proposed_group':key,'source_ids':sorted(ids),'review_status':'pending',
                    'note':'Conservative research bucket; review event boundaries and syndication before any split.'}
                   for key,ids in sorted(groups.items())]
    report = {'schema_version':'lanes-flood-ner-readiness-v1','candidate_passages':len(candidates),
        'source_articles':len(accepted),'training_admitted':0,'annotated_passages':0,'assigned_splits':0,
        'article_languages':dict(Counter(c.article_language for c in candidates)),
        'publishers':dict(Counter(e['publisher'] for e in accepted)),
        'passage_languages':{'unknown':len(candidates)},'proposed_event_buckets':len(group_queue),
        'reviewed_split_groups':0,'hold_reasons':dict(Counter(h for c in candidates for h in c.hold_reasons)),
        'case_cues':dict(Counter(s['role'] for c in candidates for s in c.case_cues)),
        'note':'One draft context window per reviewed article; not a balanced or labeled pilot corpus. Cues are review aids.'}
    output.mkdir(parents=True,exist_ok=True)
    write_jsonl(output/'candidate_passages.jsonl',candidates)
    (output/'candidate_register.json').write_bytes(json_bytes(metadata))
    (output/'group_review_queue.json').write_bytes(json_bytes(group_queue))
    (output/'readiness.json').write_bytes(json_bytes(report))
    return report
