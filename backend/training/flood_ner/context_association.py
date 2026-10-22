"""Deterministic, offline mention-anchored context prototype. No model or I/O."""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from .context_acceptance import validate_raw_input

VERSION = 'lanes-context-association-v34'
FLAGS = re.I
BODY_GAUGE = r'(?:gutter|ankle|calf|half[- ]knee|half[- ]tire|knee|tire|waist|chest|neck)[- ](?:deep|high)|(?:tuhod|baywang|dibdib|leeg|sakong)'
NUMBER = r'(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|sampu|labing\s+siyam)'
UNIT = r'(?:centimet(?:er|re)s?|cm|met(?:er|re)s?|feet|foot|ft|inches|inch|pulgada)'
MEASURE = rf'{NUMBER}(?:\s*(?:to|[-–]|hanggang)\s*{NUMBER})?\s*{UNIT}'
QUALIFIER = r'(?:(?:almost|about|around|approximately|roughly|nearly|up\s+to|as\s+high\s+as|halos|hanggang|above|below)\s+)*'
DEPTH = re.compile(rf'\b{QUALIFIER}(?:{MEASURE}(?:\s*\({MEASURE}\))?|{BODY_GAUGE}|gutter|(?:reached\s+)?(?:the\s+)?first\s+floor\s+of\s+(?:the\s+)?houses|(?:up\s+to\s+)?the\s+roof\s+of\s+a\s+vehicle|(?:around\s+)?average\s+human\s+height|(?:nearly\s+)?reached\s+bridge\s+height)(?!\w)', FLAGS)
CLOCK = r'\d{1,2}(?::\d{2})?\s*(?:[ap]\.m\.|[ap]m)'
DAY = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Lunes|Martes|Miyerkules|Huwebes|Biyernes|Sabado|Linggo)'
MONTH = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
TIME = re.compile(rf'(?<!\w)(?:'
    rf'(?:(?:pasado|bandang|kaninang)\s+)?alas[- ](?:\d+|[a-z]+)(?:\s+ng\s+(?:umaga|hapon|gabi|madaling-araw))?(?:\s+nitong\s+{DAY})?(?:,\s*{MONTH}\s+\d{{1,2}})?|'
    rf'{MONTH}\s+\d{{1,2}}(?:,\s*\d{{4}})?|{DAY}(?:\s+(?:morning|afternoon|evening|night))?(?:,\s*{MONTH}\s+\d{{1,2}})?|'
    rf'{CLOCK}|last\s+(?:year|night|week)|yesterday|today|tomorrow|now|kahapon|ngayong\s+umaga|'
    rf'this\s+(?:morning|afternoon|evening)|less\s+than\s+an\s+hour|\d+\s+(?:minutes?|hours?)'
    rf')(?!\w)', FLAGS)
FLOOD = re.compile(r'\b(?:flood(?:ing|ed|water|waters)?|baha|binaha|binabaha|water\s+level)\b', FLAGS)
FORECAST = re.compile(r'\b(?:forecast\w*|predict\w*|warn\w*|maaaring|posibleng|inaasahan)\b', FLAGS)
HISTORY = re.compile(r'\b(?:yesterday|kahapon|last\s+(?:year|week|night)|previous(?:ly)?|earlier)\b', FLAGS)
ABSENCE = re.compile(r'\b(?:not\s+flooded|hindi\s+(?:na\s+)?(?:binabaha|binaha)|wala(?:ng|\s+nang)\s+baha|no\s+(?:current\s+)?flood(?:ing)?)\b', FLAGS)
RECESSION = re.compile(r'\b(?:receding|receded|subsided|subside|humupa|humuhupa|bumababa)\b', FLAGS)
CLEAR = re.compile(r'\b(?:dry|cleared\s+of\s+floodwater|wala\s+nang\s+baha)\b', FLAGS)
AMBIGUOUS = re.compile(r'\b(?:one\s+had|sa\s+isa|which|kung\s+alin|not\s+identified|hindi\s+tinukoy|site\s+unknown|nearby|malapit\s+dito)\b', FLAGS)
SHARED = re.compile(r'\b(?:both|pareho\w*|following|sumusunod|nabanggit|across|ranged|range)\b', FLAGS)
COORDINATOR = re.compile(r'\b(?:and|at)\b|,', FLAGS)
PRONOUN = re.compile(r'\b(?:the\s+road|ang\s+kalsada|ang\s+kalsadang\s+ito)\b', FLAGS)
ACCESS = re.compile(r'\b(?:not\s+passable(?:\s+to\s+(?:all(?:\s+types?\s+of)?\s+vehicles|light\s+vehicles))?|passable(?:\s+to\s+(?:all(?:\s+types?\s+of)?\s+vehicles|motorcycles\s+and\s+cars(?:\s*\(sedan\))?))?|hindi\s+(?:ito\s+)?passable\s+sa\s+(?:mga\s+)?maliliit\s*(?:na\s*)?sasakyan)\b', FLAGS)


def segments(text: str) -> list[tuple[int, int]]:
    """Source-preserving sentence/row boundaries; no Unicode normalization."""
    result = []; start = 0
    for m in re.finditer(r'\n+|[!?](?=\s|$)|\.(?=\s+[A-ZÀ-Ý]|$)', text):
        if m.group() == '.' and re.search(r'\b(?:St|Ave|Blvd|Gov|Brgy|Dr|Mr|Mrs|[ap]|[ap]\.m)$', text[max(0,m.start()-12):m.start()], FLAGS):
            continue
        stop = m.start() if '\n' in m.group() else m.end()
        a = start
        while a < stop and text[a].isspace(): a += 1
        if a < stop: result.append((a, stop))
        start = m.end()
    while start < len(text) and text[start].isspace(): start += 1
    if start < len(text): result.append((start, len(text)))
    return result


def eligible_targets(mentions: list[dict]) -> list[dict]:
    for labels in ({'ROAD','LANDMARK','LOCAL_AREA'}, {'BARANGAY'}, {'CITY'}, {'PROVINCE'}):
        selected = [m for m in mentions if m['label'] in labels]
        if selected: return selected
    return []


def lexical_spans(pattern: re.Pattern, text: str, start: int, stop: int, label: str) -> list[dict]:
    result = []
    for match in pattern.finditer(text, start, stop):
        a,b=match.span()
        if label == 'TIME' and re.fullmatch(DAY,match.group(),FLAGS):
            # A weekday immediately used as a quoted reporter's given name is
            # not a supported temporal expression. No name list is consulted.
            if re.search(r"(?:['’]s|\bby)\s*$",text[max(start,a-8):a],FLAGS) and re.match(r'\s+[A-ZÀ-Ý][a-zà-ÿ]+',text[b:stop]):
                continue
        result.append({'start':a,'end':b,'text':text[a:b],'label':label})
    return result


def depth_scope(raw: str) -> tuple[str, list[str]]:
    tags=[]
    if re.search(r'\b(?:about|around|almost|halos|nearly|approximately|roughly)\b',raw,FLAGS):tags.append('approximate')
    if re.search(r'\b(?:above|below)\b',raw,FLAGS):tags.append('relative_gauge')
    if re.search(rf'{NUMBER}\s*(?:to|[-–]|hanggang)\s*{NUMBER}',raw,FLAGS):return 'range',tags+['not_a_point_measurement']
    if re.match(r'(?:up\s+to|as\s+high\s+as|hanggang)\b',raw,FLAGS):return 'maximum',tags+['upper_bound']
    return 'point',tags


def semantic_state(fragment: str) -> tuple[str | None, list[str]]:
    if not FLOOD.search(fragment) and not(re.search(r'\bwater\b',fragment,FLAGS)and(RECESSION.search(fragment)or CLEAR.search(fragment))): return None,[]
    # A missing report is not a positive observation of flood absence.
    if re.search(r'\b(?:no\s+\w*\s*flood\s+was\s+reported|walang\s+report)\b',fragment,FLAGS):
        return None,['no_observation_report']
    if re.search(r'\b(?:flood[- ]prone|prone\s+to\s+flood|tuwing|taon-taon)\b',fragment,FLAGS):return 'habitual',[]
    if re.search(r'\b(?:flood[- ]control|prevention\s+project)\b',fragment,FLAGS)and not re.search(r'\b(?:flooded|submerged|floodwaters?|baha|binaha)\b',fragment,FLAGS):return 'prevention',[]
    if CLEAR.search(fragment): return 'cleared',[]
    if ABSENCE.search(fragment): return 'negated',[]
    if FORECAST.search(fragment): return 'forecast',[]
    if HISTORY.search(fragment): return 'historical',[]
    if RECESSION.search(fragment):
        return ('subsided'if re.search(r'\bsubsided\b',fragment,FLAGS)else'receding'),[]
    if re.search(r'\b(?:rising|tumataas)\b',fragment,FLAGS):return 'rising',[]
    return 'active',[]


def time_role(text: str, expression: dict, start: int, stop: int, state: str | None) -> str:
    before=text[max(start,expression['start']-75):expression['start']]
    fragment=text[start:stop]
    if state=='forecast':return 'unspecified'
    # Rainfall and institutional schedules are distinct event subjects.
    if re.search(r'\b(?:rain(?:fall)?|pag-ulan|classes|class\s+suspension|suspend\w*)\b',fragment,FLAGS) and not FLOOD.search(fragment):
        return 'unspecified'
    cues=list(re.finditer(r'\b(?:began|started|nagsimula|observed|observe|na-observe|reported|report|ulat|said)\b',before,FLAGS))
    if cues:
        cue=cues[-1].group().casefold()
        if cue in {'began','started','nagsimula'} and FLOOD.search(fragment):return 'onset'
        if cue in {'reported','report','ulat','said'}:return 'report'
        if cue in {'observed','observe','na-observe'}:return 'observation'
    if re.search(r'\breport|\bulat',before,FLAGS):return 'report'
    if state=='cleared':return 'clearance'
    if state in {'receding','subsided'}:return 'recession'
    if FLOOD.search(fragment):return 'observation'
    return 'unspecified'


def target_groups(fragment: str, targets: list[dict], expressions: list[dict], kind: str) -> list[tuple[list[dict], str, str]]:
    """One output per expression; assignment requires explicit structural scope."""
    if not targets:return [([], 'unresolved', 'No supported location in this scope.')for _ in expressions]
    if AMBIGUOUS.search(fragment) and not(kind=='depth'and re.search(r'\b(?:range|ranged|individual)\b',fragment,FLAGS)):
        return [([], 'unresolved', 'Ambiguous or unidentified antecedent; no nearest-place guess.')for _ in expressions]
    if len(targets)==1:return [(targets,'local','One supported target in the bounded clause/row.')for _ in expressions]
    if len(expressions)==len(targets)>1 and COORDINATOR.search(fragment):
        # Both English target-before-value and Taglish value-before-target orders
        # are supported only when the matching order is monotonic and bounded.
        out=[]
        for target, expression in zip(targets,expressions):
            out.append(([target],'local','Parallel ordered mentions and values in one explicit coordination.'))
        return out
    if len(expressions)==1:
        if kind=='time'and COORDINATOR.search(fragment):return [(targets,'shared','Explicit single clock scoped to coordinated named observations.')]
        if SHARED.search(fragment):
            scope='collective'if depth_scope(expressions[0]['text'])[0]=='range'or re.search(r'\b(?:following|sumusunod|nabanggit|across)\b',fragment,FLAGS)else'shared'
            return [(targets,scope,'Explicit shared or collective named set; no derived scalar.')]
        if ':'in fragment and all(t['label']in{'ROAD','LANDMARK','LOCAL_AREA'}for t in targets):
            return [(targets,'collective','Bounded source row/junction; not independent whole-road values.')]
    return [([], 'unresolved', 'Multiple target/value scope is not explicitly resolved.')for _ in expressions]


def extract(value: dict) -> dict:
    validate_raw_input(value)
    text=value['text'];mentions=deepcopy(value['mentions']);expressions=[];facts=[];relations=[];unassigned=[];diagnostics=[]
    prior_single=[];row_targets=[];scope_count=0
    def add_fact(kind: str, span: dict | None, evidence: dict, targets: list[dict], scope: str, reason: str,
                 *, state: str | None=None, role: str | None=None, qualifiers: list[str] | None=None) -> None:
        entity_ids=[];raw=None;ds=None;tags=qualifiers or []
        if span is not None:
            raw=span['text'];e=next((e for e in expressions if(e['start'],e['end'],e['label'])==(span['start'],span['end'],span['label'])),None)
            if e is None:
                e={**span,'id':f'x{len(expressions)}'};expressions.append(e)
            entity_ids=[e['id']]
            if kind=='depth':ds,new_tags=depth_scope(raw);tags=tags+new_tags
        fact={'id':f'f{len(facts)}','kind':kind,'entity_ids':entity_ids,'value':raw if span is not None else state,
              'temporal_role':role if kind=='time'else None,'depth_scope':ds,'qualifiers':tags,
              'uncertainty':[],'evidence':[deepcopy(evidence)]}
        facts.append(fact)
        if targets:
            relations.append({'id':f'r{len(relations)}','fact_id':fact['id'],'target_entity_ids':[t['id']for t in targets],
                'scope':scope,'evidence':[deepcopy(evidence)],'uncertainty':[]if scope!='unresolved'else[reason],
                'overrides_relation_id':None,'reason':reason})
        else:
            fact['uncertainty']=[reason];unassigned.append({'fact_id':fact['id'],'reason':reason})
    for sentence_start,sentence_end in segments(text):
        sentence=text[sentence_start:sentence_end]
        # A sentence-level leading clock can scope its coordinated clauses, but
        # no clock is carried across another sentence or unrelated row.
        splits=[sentence_start]
        for m in re.finditer(r';|\b(?:meanwhile|whereas|while|samantala|habang|but|pero)\b',sentence,FLAGS):
            splits.append(sentence_start+m.start())
        splits.append(sentence_end);splits=sorted(set(splits))
        for start,stop in zip(splits,splits[1:]):
            while start<stop and text[start].isspace():start+=1
            if start==stop:continue
            fragment=text[start:stop];scope_count+=1
            local=[m for m in mentions if start<=m['start']and m['end']<=stop]
            target_mentions=[m for m in local if not(m['label']=='LANDMARK'and re.search(r'\b(?:near|malapit\s+sa)\s*$',text[max(start,m['start']-25):m['start']],FLAGS))]
            targets=eligible_targets(target_mentions)
            ds=lexical_spans(DEPTH,text,start,stop,'DEPTH');ts=lexical_spans(TIME,text,start,stop,'TIME')
            ds=[e for e in ds if not any(max(e['start'],m['start'])<min(e['end'],m['end'])for m in local)]
            ds=[e for e in ds if not re.search(r'\b(?:rainfall|rain\s+total|road\s+width|wide|widened|construction\s+height)\b[^.!?;\n]{0,30}$',text[max(start,e['start']-45):e['start']],FLAGS)]
            ts=[e for e in ts if not any(max(e['start'],m['start'])<min(e['end'],m['end'])for m in local)]
            state,state_issues=semantic_state(fragment)
            evidence={'start':start,'end':stop,'text':fragment}
            if not local and re.match(r'^\s*(?:water\s+level|passable|not\s+passable)',fragment,FLAGS)and row_targets:
                targets=row_targets
                # Explicit row continuation: evidence includes its preceding
                # source row without altering any coordinate.
                base=min(m['start']for m in targets)
                evidence={'start':base,'end':stop,'text':text[base:stop]}
            elif not local and PRONOUN.search(fragment)and len(prior_single)==1 and not AMBIGUOUS.search(fragment):
                targets=prior_single
                base=targets[0]['start'];evidence={'start':base,'end':stop,'text':text[base:stop]}
            elif not local and len(prior_single)==1 and sentence_start<=prior_single[0]['start'] and re.match(r'^(?:but|pero)\s+(?:remained|still|gutter|knee|waist|may)\b',fragment,FLAGS):
                targets=prior_single
                base=targets[0]['start'];evidence={'start':base,'end':stop,'text':text[base:stop]}
            if local:
                residual=fragment
                for m in sorted(local,key=lambda m:m['start'],reverse=True):
                    a,b=m['start']-start,m['end']-start;residual=residual[:a]+' '+residual[b:]
                row_targets=targets if not re.search(r'\b(?:had|have|flood|baha|said|was|were|is|are|report)\b',residual,FLAGS)and not ds and not ts else []
                prior_single=targets if len(targets)==1 and targets[0]['label']in{'ROAD','LANDMARK','LOCAL_AREA'}else[]
            elif not re.match(r'^\s*(?:water\s+level|passable|not\s+passable)',fragment,FLAGS):
                row_targets=[]
            for d,(assigned,scope,reason)in zip(ds,target_groups(fragment,targets,ds,'depth')):
                qualifiers=['predicted_only']if state=='forecast'else[]
                add_fact('depth',d,evidence,assigned,scope,reason,qualifiers=qualifiers)
            for t,(assigned,scope,reason)in zip(ts,target_groups(fragment,targets,ts,'time')):
                role=time_role(text,t,start,stop,state)
                if role=='unspecified'and not FLOOD.search(fragment):assigned=[];scope='unresolved';reason='Non-flood or unsupported temporal subject.'
                add_fact('time',t,evidence,assigned,scope,reason,role=role)
            if state is not None:
                # A clause-level state may describe an explicit coordinated set;
                # it never manufactures a location omitted by the supplied NER.
                assigned=[]if AMBIGUOUS.search(fragment)else targets
                scope='shared'if len(assigned)>1 else'local'
                add_fact('status',None,evidence,assigned,scope,'Explicit clause-local flood state.',state=state)
            for access in ACCESS.finditer(fragment):
                raw=access.group();negative=bool(re.search(r'\bnot\b|\bhindi\b',raw,FLAGS))
                all_vehicles=bool(re.search(r'\ball\b',raw,FLAGS));light=bool(re.search(r'\blight\b|\bmaliliit\b',raw,FLAGS))
                result=('impassable_all'if all_vehicles else'light_vehicle_closed'if light else'unknown')if negative else'passable_all'if all_vehicles else'passable_unspecified'
                assigned=[]if AMBIGUOUS.search(fragment)else targets
                add_fact('access',None,evidence,assigned,'shared'if len(assigned)>1 else'local','Explicit vehicle scope only.',
                         state=result,qualifiers=[raw])
            if state_issues:diagnostics.extend(state_issues)
            if (ds or ts or state)and not targets:diagnostics.append('recognized_fact_without_supported_location')
    output={'schema':VERSION,'record_id':value['record_id'],'text_sha256':value['text_sha256'],
            'mentions':mentions,'expressions':sorted(expressions,key=lambda e:(e['start'],e['end'],e['label'])),
            'facts':facts,'relations':relations,'unassigned':unassigned,'diagnostics':sorted(set(diagnostics)),
            'absolute_instants':[],'numeric_depths':[]}
    validate_output(value,output)
    return output


def validate_output(value: dict, output: dict) -> None:
    validate_raw_input(value)
    if set(output)!={'schema','record_id','text_sha256','mentions','expressions','facts','relations','unassigned','diagnostics','absolute_instants','numeric_depths'}:
        raise ValueError('exact context output required')
    if output['schema']!=VERSION or output['record_id']!=value['record_id']or output['text_sha256']!=value['text_sha256']or output['mentions']!=value['mentions']:
        raise ValueError('original mention/text identity changed')
    if output['absolute_instants']or output['numeric_depths']:raise ValueError('prototype emits raw evidence only, no inferred instant/scalar')
    text=value['text'];entities={e['id']:e for e in output['expressions']};facts={f['id']:f for f in output['facts']};mentions={m['id']:m for m in value['mentions']}
    if len(entities)!=len(output['expressions'])or len(facts)!=len(output['facts']):raise ValueError('duplicate output identity')
    end=-1
    for e in output['expressions']:
        if e['label']not in{'DEPTH','TIME'}or type(e['start'])is not int or type(e['end'])is not int or not(0<=e['start']<e['end']<=len(text))or text[e['start']:e['end']]!=e['text']or e['start']<end:
            raise ValueError('invalid or overlapping contextual expression')
        end=e['end']
    for f in output['facts']:
        if f['kind']not in{'depth','time','status','access'}:raise ValueError('unknown fact kind')
        if not f['evidence']:raise ValueError('fact evidence required')
        for e in f['evidence']:
            if not(0<=e['start']<e['end']<=len(text))or text[e['start']:e['end']]!=e['text']:raise ValueError('invalid fact evidence')
        if f['kind']in{'depth','time'}:
            if not f['entity_ids']or any(i not in entities for i in f['entity_ids']):raise ValueError('missing expression evidence')
            if f['value']not in{entities[i]['text']for i in f['entity_ids']}:raise ValueError('invented fact value')
            expected='DEPTH'if f['kind']=='depth'else'TIME'
            if any(entities[i]['label']!=expected for i in f['entity_ids']):raise ValueError('wrong expression type')
            if any(not any(s['start']<=entities[i]['start']<entities[i]['end']<=s['end']for s in f['evidence'])for i in f['entity_ids']):raise ValueError('expression escapes fact evidence')
        if f['kind']=='time'and f['temporal_role']not in{'onset','observation','report','publication','recession','clearance','unspecified'}:raise ValueError('invalid temporal role')
        if f['kind']=='depth'and f['depth_scope']not in{'point','range','collective','maximum','unspecified'}:raise ValueError('invalid depth scope')
        if f['kind']=='status'and f['value']not in{'active','rising','receding','subsided','cleared','forecast','negated','historical','habitual','prevention','unknown'}:raise ValueError('invalid status value')
        if f['kind']=='access'and f['value']not in{'passable_all','passable_with_caution','passable_unspecified','light_vehicle_closed','impassable_all','unknown'}:raise ValueError('invalid access value')
    linked=set();relation_ids=set()
    for r in output['relations']:
        if r['id']in relation_ids or r['fact_id']not in facts or not r['target_entity_ids']or len(set(r['target_entity_ids']))!=len(r['target_entity_ids'])or any(i not in mentions for i in r['target_entity_ids']):raise ValueError('invalid relation targets')
        if r['scope']not in{'local','shared','collective','unresolved'}or(r['scope']=='local'and len(r['target_entity_ids'])!=1)or(r['scope']=='shared'and len(r['target_entity_ids'])<2):raise ValueError('invalid relation scope')
        if r['scope']=='unresolved'and not r['uncertainty']:raise ValueError('unresolved reason required')
        if not r['evidence']or r['overrides_relation_id']is not None:raise ValueError('evidence required; prototype preserves updates without guessed overrides')
        for e in r['evidence']:
            if not(0<=e['start']<e['end']<=len(text))or text[e['start']:e['end']]!=e['text']:raise ValueError('invalid relation evidence')
            if any(not(e['start']<=mentions[i]['start']<mentions[i]['end']<=e['end'])for i in r['target_entity_ids']):raise ValueError('target escapes evidence')
        linked.add(r['fact_id']);relation_ids.add(r['id'])
    if {x['fact_id']for x in output['unassigned']}!=set(facts)-linked or any(not x['reason']for x in output['unassigned']):raise ValueError('unassigned facts unaccounted')
