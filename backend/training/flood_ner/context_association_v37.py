"""Source-bounded grouping successor; no model, geographic lookup or external I/O."""
from __future__ import annotations

from copy import deepcopy
import re

from . import context_association as base
from .context_acceptance import validate_raw_input

IMPLEMENTATION = 'lanes-context-association-v37'
FLAGS = re.I
NUMBER=rf'(?:{base.NUMBER}|eleven|twelve|twenty|dalawampung|dalawampu|isa|dalawa|tatlo|apat|lima|anim|pito|walo|siyam)'
UNIT=rf'(?:{base.UNIT}|sentimetro|metro|talampakan)'
QUALIFIER=rf'(?:(?:almost|about|around|approximately|roughly|nearly|up\s+to|as\s+high\s+as|halos|hanggang|above|below|humigit-kumulang|hindi\s+hihigit\s+sa|nasa)\s+)*'
MEASURE = rf'{NUMBER}(?:\s*(?:to|[-–]|hanggang)\s*{NUMBER})?\s*(?:na\s+)?{UNIT}'
GAUGE=rf'(?:abot[- ](?:tuhod|baywang|dibdib|leeg|sakong)|{base.BODY_GAUGE})'
DEPTH = re.compile(rf'\b{QUALIFIER}(?:{MEASURE}(?:\s*\({MEASURE}\))?|{GAUGE}|gutter|(?:reached\s+)?(?:the\s+)?first\s+floor\s+of\s+(?:the\s+)?houses|(?:up\s+to\s+)?the\s+roof\s+of\s+a\s+vehicle|(?:around\s+)?average\s+human\s+height|(?:nearly\s+)?reached\s+bridge\s+height|deep|malalim)(?!\w)', FLAGS)
DURATION = re.compile(rf'^(?:less\s+than\s+an\s+hour|(?:{NUMBER}|dalawang)\s+(?:minutes?|hours?|oras|minuto))$', FLAGS)
TIME=re.compile(rf'(?<!\w)(?:(?:{NUMBER}|dalawang)\s+(?:hours?|minutes?|oras|minuto)|ngayon|bukas|{base.TIME.pattern})(?!\w)',FLAGS)
TIME=re.compile(TIME.pattern.replace(r'\s+nitong\s+',r'\s+(?:nitong|ng|noong)\s+'),FLAGS)
FLOOD=re.compile(r'\b(?:flood(?:ing|ed|water|waters)?|pagbaha|baha|binaha|binabaha|water\s+level|turned\s+into\s+rivers|overflow(?:ed|ing)?)\b',FLAGS)
ACCESS=re.compile(rf'\b(?:(?:not\s+)?passable\s+sa\s+(?:light|all)\s+vehicles|(?:hindi\s+)?madaanan\s+ng\s+(?:maliliit\s+na|lahat\s+ng)\s+sasakyan|(?:temporarily\s+)?closed\s+(?:to|due)|sarado\s+sa\s+maliliit\s+na\s+sasakyan)\b|{base.ACCESS.pattern}',FLAGS)
TRANSITION = re.compile(r'^\s*(?:meanwhile|samantala|today|yesterday|now|last\s+(?:year|night|week)|kahapon|ngayon)\b', FLAGS)
FACILITY_CONTEXT = re.compile(r'\b(?:near|nearby|malapit|shelter|evacuation\s+(?:center|centre|destination)|matatagpuan|located|where\s+.+?\s+(?:stand|stands))\b', FLAGS)
FACILITY_CONTEXT=re.compile(FACILITY_CONTEXT.pattern+r'|\b(?:evacuat\w*\s+to|lumikas\s+sa)\b',FLAGS)


def temporal_title(text: str, expression: dict, start: int, stop: int) -> bool:
    """A title's duration-shaped words are not a calendar expression."""
    before=text[max(start,expression['start']-100):expression['start']]
    after=text[expression['end']:min(stop,expression['end']+70)]
    introduction=re.search(r'(?:report\s+on|ulat\s+(?:ng|sa)\s+palabas\s+na|palabas\s+na)\s*["“‘\']\s*[^"”’\']*$',before,FLAGS)
    title_follow=re.match(r'\s+(?:[A-ZÀ-Ý][\w-]*\s+){0,3}report\b',after)
    duration_shaped=bool(re.fullmatch(rf'{NUMBER}\s+(?:Oras|Hours?|Minutes?)',expression['text']))
    return bool(duration_shaped and(introduction or title_follow))


def segments(text: str, mentions: list[dict]) -> list[tuple[int,int]]:
    """Do not split within supplied names or general abbreviated designators."""
    result=[];start=0
    for match in re.finditer(r'\n+|[!?](?=\s|$)|\.(?=\s+[A-ZÀ-Ý]|$)',text):
        if match.group()=='.':
            inside=any(m['start']<=match.start()<m['end'] for m in mentions)
            abbreviation=re.search(r'\b(?:St|Ave|Blvd|Gov|Brgy|Dr|Mr|Mrs|Cor|[A-Za-z]|[ap]\.m)$',text[max(0,match.start()-12):match.start()],FLAGS)
            if inside or abbreviation:continue
        stop=match.start() if '\n' in match.group() else match.end()
        a=start
        while a<stop and text[a].isspace():a+=1
        if a<stop:result.append((a,stop))
        start=match.end()
    while start<len(text) and text[start].isspace():start+=1
    if start<len(text):result.append((start,len(text)))
    return result


def complete_named_set(text: str, start: int, stop: int, local: list[dict], targets: list[dict]) -> bool:
    """Abstain on visibly missing list items or unsupported numeric road targets."""
    if len(targets)<2:return True
    if re.search(r'\b(?:unnamed|unidentified|hindi\s+pinangalanang)\b',text[start:stop],FLAGS):return False
    if any(m['label']=='ROAD' and m['text'].strip().isdigit() for m in targets):return False
    a=min(m['start']for m in targets);b=stop
    after=max(m['end']for m in targets)
    end=re.search(r'\b(?:were|was|are|had|has|have|ay|kaya|dahil|due|according|ayon)\b',text[after:stop],FLAGS)
    if end:b=after+end.start()
    for part in re.finditer(r'[^,]+',text[a:b]):
        x=a+part.start();y=a+part.end()
        if not any(x<=m['start']<y for m in local) and re.search(r'[A-ZÀ-Ý][A-Za-zÀ-ÿ]+',part.group()):
            return False
    return True


def supported_targets(text: str, start: int, stop: int, local: list[dict]) -> list[dict]:
    fragment=text[start:stop];filtered=[]
    facility_context=FACILITY_CONTEXT.search(fragment)
    for mention in local:
        if mention['label']=='LANDMARK' and facility_context:
            following=text[mention['end']:stop]
            own_flood=re.match(r'\s+(?:is|was|were|had|has|ay|ang)?\s*(?:flooded|submerged|binaha|binabaha)',following,FLAGS)
            before=text[max(start,mention['start']-22):mention['start']]
            if not own_flood or re.search(r'\b(?:near|malapit|located|matatagpuan)\b',before,FLAGS):continue
        filtered.append(mention)
    return base.eligible_targets(filtered)


def state_for(fragment: str) -> tuple[str|None,list[str]]:
    if re.search(r'\b(?:no\s+(?:flooding\s+)?report|no\s+flooding\s+report\s+was\s+supplied|walang\s+(?:ulat|flood\s+report)|hindi\s+alam\s+ang\s+lalim)\b',fragment,FLAGS):
        return None,['missing_observation_not_verified_absence']
    if re.search(r'\b(?:bahain|flood[- ]prone)\b',fragment,FLAGS):return 'habitual',['susceptibility_not_current_observation']
    if re.search(r'\b(?:wala\s+nang\s+baha|cleared\s+of\s+floodwater|tuyo\s+na)\b',fragment,FLAGS):return 'cleared',[]
    if re.search(r'\b(?:hindi\s+flooded|hindi\s+binabaha|not\s+flooded)\b',fragment,FLAGS):return 'negated',[]
    if re.search(r'\b(?:subsided|receded|humupa|nag-subside)\b',fragment,FLAGS):return 'subsided',[]
    if re.search(r'\b(?:receding|humuhupa|humupa|bumababa)\b',fragment,FLAGS)and(re.search(r'\b(?:water|baha|flood\w*)\b',fragment,FLAGS)):return 'receding',[]
    if re.search(r'\b(?:rose|rising|tumaas|tumataas)\b',fragment,FLAGS)and FLOOD.search(fragment):return 'rising',[]
    state,issues=base.semantic_state(fragment)
    if state is None and FLOOD.search(fragment)and not re.search(r'\b(?:flood[- ]control|flood-prone)\b',fragment,FLAGS):
        state='forecast'if base.FORECAST.search(fragment)else'active'
    if re.search(r'\bwater\s+level\b',fragment,FLAGS) and not re.search(r'\b(?:flood\w*|baha|binaha|binabaha)\b',fragment,FLAGS):
        return None,issues+['measurement_row_not_explicit_active_status']
    prone=bool(re.search(r'\b(?:prone|susceptib\w*)\b',fragment,FLAGS))
    actual=bool(re.search(r'\b(?:were\s+flooded|was\s+flooded|experienced\s+flood|binaha|binabaha)\b',fragment,FLAGS))
    if prone and not actual:return 'habitual',issues+['susceptibility_not_current_observation']
    return state,issues


def time_role(text: str, expression: dict, start: int, stop: int,
              state: str|None, elliptical_observation: bool) -> str:
    if DURATION.fullmatch(expression['text']):return 'unspecified'
    before=text[max(start,expression['start']-75):expression['start']]
    cues=list(re.finditer(r'\b(?:reced\w*|subsid\w*|humuhupa|humupa|cleared|dry|tuyo|nagsimula|began|started|observed|na-observe|naobserbahan|report\w*|ulat)\b',before,FLAGS))
    if cues:
        cue=cues[-1].group().casefold()
        if re.match(r'reced|subsid|humup|humuh',cue):return 'recession'
        if cue in {'cleared','dry','tuyo'}:return 'clearance'
        if cue in {'nagsimula','began','started'}and FLOOD.search(text[start:stop]):return 'onset'
        if cue in {'observed','na-observe','naobserbahan'}:return 'observation'
        if re.match(r'report|ulat',cue):return 'report'
    if state in {'receding','subsided'}:return 'recession'
    if state=='cleared':return 'clearance'
    if re.search(r'\bas\s+of\s*$',before,FLAGS) and state not in {'forecast','cleared'}:
        return 'observation'
    role=base.time_role(text,expression,start,stop,state)
    if role=='unspecified' and(elliptical_observation or FLOOD.search(text[start:stop]))and state!='forecast':return 'observation'
    return role


def derive_depth_scope(raw: str) -> tuple[str,list[str]]:
    tags=[]
    if re.search(r'\b(?:about|around|almost|halos|nearly|approximately|roughly|humigit-kumulang)\b',raw,FLAGS):tags.append('approximate')
    if re.search(r'\b(?:above|below)\b',raw,FLAGS):tags.append('relative_gauge')
    if re.search(rf'{NUMBER}\s*(?:to|[-–]|hanggang)\s*{NUMBER}',raw,FLAGS):return 'range',tags+['not_a_point_measurement']
    if re.match(r'(?:up\s+to|as\s+high\s+as|hindi\s+hihigit\s+sa)\b',raw,FLAGS)or re.match(rf'hanggang\s+{NUMBER}\b',raw,FLAGS):return 'maximum',tags+['upper_bound']
    if raw.casefold()in{'deep','malalim'}:return 'unspecified',tags
    return 'point',tags


def target_groups(fragment: str, targets: list[dict], expressions: list[dict], kind: str) -> list[tuple]:
    if base.AMBIGUOUS.search(fragment):
        return [([], 'unresolved', 'Explicitly unidentified target; range does not resolve it.')for _ in expressions]
    if kind=='depth' and len(targets)>1 and len(expressions)==1:
        if base.depth_scope(expressions[0]['text'])[0]=='range' and base.COORDINATOR.search(fragment):
            return [(targets,'collective','Explicit bounded named-set range; no per-target scalar.')]
        if re.search(r'\b(?:collective|sumusunod|following|nabanggit)\b',fragment,FLAGS):
            return [(targets,'collective','Explicit list retains one grouped measurement.')]
        if re.search(r'\b(?:hanggang|abot[- ])',expressions[0]['text'],FLAGS)and base.COORDINATOR.search(fragment)and not re.search(r'\b(?:both|pareho\w*)\b',fragment,FLAGS):
            return [(targets,'collective','Coordinated reached-level list; no invented independent scalars.')]
    return base.target_groups(fragment,targets,expressions,kind)


def extract(value: dict) -> dict:
    validate_raw_input(value)
    text=value['text'];mentions=deepcopy(value['mentions'])
    expressions=[];facts=[];relations=[];unassigned=[];diagnostics=[]
    prior_single=[];row_targets=[];prior_observation=False;prior_list=[]
    row_joint=False;observed_header=False;inventory_header=False;inventory_rows=[];last_stop=0

    def add(kind: str, span: dict|None, evidence: dict, targets: list[dict], scope: str,
            reason: str, *, state: str|None=None, role: str|None=None,
            collective_depth: bool=False, qualifiers: list[str]|None=None) -> None:
        ids=[];raw=None;depth_scope=None;tags=list(qualifiers or [])
        if span is not None:
            raw=span['text'];entity=next((e for e in expressions if (e['start'],e['end'],e['label'])==(span['start'],span['end'],span['label'])),None)
            if entity is None:
                entity={**span,'id':f'x{len(expressions)}'};expressions.append(entity)
            ids=[entity['id']]
            if kind=='depth':
                depth_scope_value,new_tags=derive_depth_scope(raw);tags+=new_tags
                if collective_depth:depth_scope_value='collective';tags.append('not_a_uniform_point_measurement')
                depth_scope=depth_scope_value
        fact={'id':f'f{len(facts)}','kind':kind,'entity_ids':ids,
            'value':raw if span is not None else state,'temporal_role':role if kind=='time'else None,
            'depth_scope':depth_scope,'qualifiers':tags,'uncertainty':[],'evidence':[deepcopy(evidence)]}
        facts.append(fact)
        if targets:
            relations.append({'id':f'r{len(relations)}','fact_id':fact['id'],
                'target_entity_ids':[m['id']for m in targets],'scope':scope,
                'evidence':[deepcopy(evidence)],'uncertainty':[],
                'overrides_relation_id':None,'reason':reason})
        else:
            fact['uncertainty']=[reason];unassigned.append({'fact_id':fact['id'],'reason':reason})

    for sentence_start,sentence_end in segments(text,mentions):
        sentence=text[sentence_start:sentence_end];splits=[sentence_start]
        for match in re.finditer(r';|\b(?:meanwhile|whereas|while|samantala|habang|but|pero)\b',sentence,FLAGS):
            splits.append(sentence_start+match.start())
        splits=sorted(set(splits+[sentence_end]))
        for start,stop in zip(splits,splits[1:]):
            while start<stop and(text[start].isspace()or text[start]==';'):start+=1
            if start==stop:continue
            fragment=text[start:stop];local=[m for m in mentions if start<=m['start'] and m['end']<=stop]
            if '\n\n'in text[last_stop:start]:prior_single=[];row_targets=[];prior_list=[];row_joint=False
            last_stop=stop
            if not local and re.search(r'^(?:observed\s+(?:na\s+)?(?:flooding|pagbaha)|naobserbahang\s+pagbaha)\s*$',fragment,FLAGS):observed_header=True
            if not local and re.search(r'collective\s+depth\s+summary|pinagsamang\s+tala\s+ng\s+lalim',fragment,FLAGS):inventory_header=True
            targets=supported_targets(text,start,stop,local)
            complete=complete_named_set(text,start,stop,local,targets)
            if not complete:targets=[];diagnostics.append('incomplete_or_unsupported_named_set')
            ds=base.lexical_spans(DEPTH,text,start,stop,'DEPTH')
            ts=base.lexical_spans(TIME,text,start,stop,'TIME')
            ds=[d for i,d in enumerate(ds)if not(d['text'].casefold()=='deep'and i and re.fullmatch(r'\s*',text[ds[i-1]['end']:d['start']])and re.search(rf'{NUMBER}.*{UNIT}$',ds[i-1]['text'],FLAGS))]
            ds=[e for e in ds if not any(max(e['start'],m['start'])<min(e['end'],m['end'])for m in local)]
            ds=[e for e in ds if not re.search(r'\b(?:rainfall|rain\s+total|road\s+width|wide|widened|construction\s+height)\b[^.!?;\n]{0,30}$',text[max(start,e['start']-45):e['start']],FLAGS)]
            ts=[e for e in ts if not any(max(e['start'],m['start'])<min(e['end'],m['end'])for m in local)]
            # A spelled month homograph in Taglish possession ("May 11 ... cm")
            # cannot overlap a source-explicit measured depth.
            ts=[e for e in ts if not any(max(e['start'],d['start'])<min(e['end'],d['end'])for d in ds)]
            ts=[e for e in ts if not temporal_title(text,e,start,stop)]
            state,issues=state_for(fragment)
            line_start=text.rfind('\n',0,start)+1;line_end=text.find('\n',stop)
            if line_end<0:line_end=len(text)
            line=text[line_start:line_end]
            explicit_colon=bool(targets and re.search(':',text[max(m['end']for m in targets):stop]))
            measured_table=bool(ds and targets and(explicit_colon or re.match(r'water\s+level',fragment,FLAGS)))
            wet_row=bool(measured_table and(observed_header or re.search(r'water\s+level',line,FLAGS)and ACCESS.search(line)
                or re.search(r'gutter|knee|waist|tuhod|baywang',fragment,FLAGS)and ACCESS.search(line)))
            if state is None and wet_row:state='active'
            elliptical=bool(ds and targets and prior_observation and (TRANSITION.search(fragment)or re.search(r'\bnaman\b',fragment,FLAGS)) and state is None)
            if elliptical:
                state='historical'if base.HISTORY.search(fragment)else'active'
            evidence={'start':start,'end':stop,'text':fragment}
            row_continuation=bool(not local and(re.match(r'^\s*water\s+level',fragment,FLAGS)or ACCESS.match(fragment)))
            if row_continuation and row_targets:
                targets=row_targets;first=min(m['start']for m in targets)
                evidence={'start':first,'end':stop,'text':text[first:stop]}
            elif not local and base.PRONOUN.search(fragment) and len(prior_single)==1 and not base.AMBIGUOUS.search(fragment):
                targets=prior_single;first=targets[0]['start']
                evidence={'start':first,'end':stop,'text':text[first:stop]}
            elif not local and len(prior_single)==1 and sentence_start<=prior_single[0]['start'] and re.match(r'^(?:but|pero)\s+(?:remained|still|gutter|knee|waist|may)\b',fragment,FLAGS):
                targets=prior_single;first=targets[0]['start'];evidence={'start':first,'end':stop,'text':text[first:stop]}
            elif not local and re.search(r'\b(?:nabanggit|aforementioned|these\s+roads|the\s+following\s+roads)\b',fragment,FLAGS)and prior_list and not base.AMBIGUOUS.search(fragment):
                targets=prior_list;first=min(m['start']for m in targets);evidence={'start':first,'end':stop,'text':text[first:stop]}
            elif not local and prior_single and not base.AMBIGUOUS.search(fragment)and re.search(r'\b(?:floodwaters?|floodwater|baha)\b',fragment,FLAGS):
                targets=prior_single;first=targets[0]['start'];evidence={'start':first,'end':stop,'text':text[first:stop]}
            if state is None and ds and targets and re.match(r'water\s+level',fragment,FLAGS):
                next_end=text.find('\n',line_end+1)
                if next_end<0:next_end=len(text)
                if ACCESS.search(text[line_end:next_end]):state='active'
            if targets and not local and state is None and ds and re.match(r'^\s*(?:but|pero|ngunit)',fragment,FLAGS):
                state=None  # A residual gauge does not assert a second flood status.
            if local:
                residual=fragment
                for mention in sorted(local,key=lambda m:m['start'],reverse=True):
                    a,b=mention['start']-start,mention['end']-start;residual=residual[:a]+' '+residual[b:]
                row_targets=targets if explicit_colon or not re.search(r'\b(?:had|have|flood|baha|said|was|were|is|are|report)\b',residual,FLAGS) and not ds and not ts else []
                row_joint=bool(len(targets)>1 and(explicit_colon or re.search(r'\b(?:sa\s+bahagi\s+ng|junction|intersection)\b',fragment,FLAGS))
                    and not re.search(r'\b(?:both|pareho\w*|collective|depths?|lalim)\b',text[start:min(m['start']for m in targets)],FLAGS))
                prior_single=targets if len(targets)==1 and targets[0]['label']in{'ROAD','LANDMARK','LOCAL_AREA','BARANGAY'}else[]
                prior_list=targets if len(targets)>1 else[]
            elif not row_continuation:row_targets=[];row_joint=False
            for d,(assigned,scope,reason) in zip(ds,target_groups(fragment,targets,ds,'depth')):
                collective=bool(re.search(r'\b\d+\s+(?:barangays|villages|areas|communities)\b',fragment,FLAGS))
                if scope=='collective'and derive_depth_scope(d['text'])[0]!='range'and re.search(r'\bmga\s+sumusunod\b',fragment,FLAGS):collective=True
                add('depth',d,evidence,assigned,scope,reason,collective_depth=collective,
                    qualifiers=['predicted_only']if state=='forecast'else[])
                if assigned and (measured_table or re.match(r'water\s+level',fragment,FLAGS)):
                    expression_id=next(e['id']for e in expressions if (e['start'],e['end'],e['label'])==(d['start'],d['end'],d['label']))
                    inventory_rows.append({'line':line_start,'expression_id':expression_id,'targets':deepcopy(assigned),
                        'evidence':deepcopy(evidence),'table_context':wet_row or bool(re.search(r'SUBSIDED|water\s+level',line,FLAGS))})
            for t,(assigned,scope,reason) in zip(ts,target_groups(fragment,targets,ts,'time')):
                role=time_role(text,t,start,stop,state,elliptical)
                event_duration=bool(DURATION.fullmatch(t['text'])and targets and FLOOD.search(fragment)and re.search(r'\b(?:rose|rising|tumaas|tumataas)\b',fragment,FLAGS))
                if role=='report' or DURATION.fullmatch(t['text'])and not event_duration:
                    assigned=[];scope='unresolved';reason='Report/duration evidence does not establish a per-location event clock.'
                elif role=='unspecified' and not base.FLOOD.search(fragment):
                    assigned=[];scope='unresolved';reason='Unsupported temporal subject or role.'
                add('time',t,evidence,assigned,scope,reason,role=role)
            if re.search(r'\b(?:visited|visit|flew|arrived|evacuated\s+to|evacuation\s+center)\b',fragment,FLAGS)and not re.search(r'\b(?:was\s+flooded|were\s+flooded|binaha|binabaha)\b',fragment,FLAGS):
                status_targets=[]
            else:status_targets=targets
            if state is not None:
                assigned=[]if base.AMBIGUOUS.search(fragment) or 'susceptibility_not_current_observation' in issues else status_targets
                add('status',None,evidence,assigned,'collective'if row_joint and len(assigned)>1 else'shared'if len(assigned)>1 else'local',
                    'Explicit bounded status; missing context remains unassigned.',state=state)
            for access in ACCESS.finditer(fragment):
                raw=access.group();negative=bool(re.search(r'\bnot\b|\bhindi\b',raw,FLAGS))
                negative=negative or bool(re.search(r'closed|sarado',raw,FLAGS))
                all_vehicles=bool(re.search(r'\ball\b|\blahat\b',raw,FLAGS));light=bool(re.search(r'\blight\b|\bmaliliit\b',raw,FLAGS))
                state_access=('impassable_all'if all_vehicles else'light_vehicle_closed'if light else'unknown')if negative else'passable_all'if all_vehicles else'passable_unspecified'
                assigned=[]if base.AMBIGUOUS.search(fragment)else targets
                add('access',None,evidence,assigned,'collective'if row_joint and len(assigned)>1 else'shared'if len(assigned)>1 else'local',
                    'Explicit vehicle and complete target-set scope.',state=state_access,qualifiers=[raw])
            diagnostics.extend(issues)
            if ds and targets and state in {'active','historical','receding','subsided'}:prior_observation=True
            elif local or state in {'forecast','negated','habitual','prevention'}:prior_observation=False
    # A null source-list inventory records its original constituents, not a new
    # measurement or one event shared across distinct row clocks and updates.
    rows={r['line']for r in inventory_rows}
    if len(rows)>1 and(inventory_header or all(r['table_context']for r in inventory_rows)):
        ids=list(dict.fromkeys(r['expression_id']for r in inventory_rows))
        assigned={m['id']:m for r in inventory_rows for m in r['targets']}
        a=min(r['evidence']['start']for r in inventory_rows);b=max(r['evidence']['end']for r in inventory_rows)
        e={'start':a,'end':b,'text':text[a:b]};fact_id=f'f{len(facts)}'
        facts.append({'id':fact_id,'kind':'depth','entity_ids':ids,'value':None,'temporal_role':None,
            'depth_scope':'collective','qualifiers':['source_list_inventory_not_uniform_scalar_or_event'],
            'uncertainty':[],'evidence':[e]})
        relations.append({'id':f'r{len(relations)}','fact_id':fact_id,'target_entity_ids':list(assigned),
            'scope':'collective','evidence':[e],'uncertainty':[],'overrides_relation_id':None,
            'reason':'Explicit measured source-list constituents; original row facts and clocks remain separate.'})
    output={'schema':base.VERSION,'record_id':value['record_id'],'text_sha256':value['text_sha256'],
        'mentions':mentions,'expressions':sorted(expressions,key=lambda e:(e['start'],e['end'],e['label'])),
        'facts':facts,'relations':relations,'unassigned':unassigned,'diagnostics':sorted(set(diagnostics)),
        'absolute_instants':[],'numeric_depths':[]}
    validate_output(value,output)
    return output


def validate_output(value: dict, output: dict) -> None:
    validate_raw_input(value)
    if set(output)!={'schema','record_id','text_sha256','mentions','expressions','facts','relations','unassigned','diagnostics','absolute_instants','numeric_depths'}:
        raise ValueError('exact context output required')
    if output['schema']!=base.VERSION or output['record_id']!=value['record_id']or output['text_sha256']!=value['text_sha256']or output['mentions']!=value['mentions']:
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
            null_inventory=(f['kind']=='depth'and f['value']is None and f['depth_scope']=='collective'and len(set(f['entity_ids']))==len(f['entity_ids'])>=2)
            if f['value']not in{entities[i]['text']for i in f['entity_ids']}and not null_inventory:raise ValueError('invented fact value')
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
