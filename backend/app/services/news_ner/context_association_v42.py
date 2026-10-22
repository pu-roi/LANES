"""Versioned junction, list context and clock successor; frozen v41 preserved."""
from __future__ import annotations

from copy import deepcopy
import re

from . import context_association as base
from . import context_association_v38 as previous
from .contract import validate_raw_input

IMPLEMENTATION = 'lanes-context-association-v42'
FLAGS = re.I
NUMBER=rf'(?:{base.NUMBER}|eleven|twelve|twenty|dalawampung|dalawampu|isa|dalawa|tatlo|apat|lima|anim|pito|walo|siyam)'
UNIT=rf'(?:{base.UNIT}|sentimetro|metro|talampakan)'
QUALIFIER=rf'(?:(?:almost|about|around|approximately|roughly|nearly|up\s+to|as\s+high\s+as|halos|hanggang|above|below|humigit-kumulang|hindi\s+hihigit\s+sa|nasa)\s+)*'
MEASURE = rf'{NUMBER}(?:\s*(?:to|[-–]|hanggang)\s*{NUMBER})?\s*(?:na\s+)?{UNIT}'
GAUGE=rf'(?:abot[- ](?:tuhod|baywang|dibdib|leeg|sakong)|{base.BODY_GAUGE})'
DEPTH = re.compile(rf'\b{QUALIFIER}(?:{MEASURE}(?:\s*\({MEASURE}\))?|{GAUGE}|gutter|(?:reached\s+)?(?:the\s+)?first\s+floor\s+of\s+(?:the\s+)?houses|(?:up\s+to\s+)?the\s+roof\s+of\s+a\s+vehicle|(?:around\s+)?average\s+human\s+height|(?:nearly\s+)?reached\s+bridge\s+height|deep|malalim)(?!\w)', FLAGS)
DURATION = re.compile(rf'^(?:less\s+than\s+an\s+hour|(?:{NUMBER}|dalawang)\s+(?:minutes?|hours?|oras|minuto))$', FLAGS)
CLOCK = r'\d{1,2}(?::\d{2})?\s*(?:[ap]\.m\.?|[ap]m)'
TIME=re.compile(rf'(?<!\w)(?:(?:{NUMBER}|dalawang)\s+(?:hours?|minutes?|oras|minuto)|ngayon|bukas|{base.TIME.pattern.replace(base.CLOCK, CLOCK)})(?!\w)',FLAGS)
TIME=re.compile(TIME.pattern.replace(r'\s+nitong\s+',r'\s+(?:nitong|ng|noong)\s+'),FLAGS)
FLOOD=re.compile(r'\b(?:flood(?:s|ing|ed|water|waters)?|pagbaha|bahang|baha|lubog|binaha|binabaha|water\s+level|turned\s+into\s+rivers|overflow(?:ed|ing)?)\b',FLAGS)
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
    # Causal and destination roles are local grammatical cues, not facility types.
    affected = []
    for mention in filtered:
        before = text[max(start, mention['start']-65):mention['start']]
        causal = re.search(r'(?:spilling\s+of|release\s+(?:from|of)|pag-apaw\s+ng|pagpapakawala\s+ng|overflowing\s+of)\s*$', before, FLAGS)
        destination = re.search(r'(?:evacuat\w*\s+to|evacuation\s+(?:center|centre)|lumikas\s+sa)\s*$', before, FLAGS)
        if causal or destination:
            continue
        affected.append(mention)
    return base.eligible_targets(affected)


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
        state='forecast'if base.FORECAST.search(fragment)else'historical'if base.HISTORY.search(fragment)else'active'
    if re.search(r'\bwater\s+level\b',fragment,FLAGS) and not re.search(r'\b(?:flood\w*|baha|binaha|binabaha)\b',fragment,FLAGS):
        return None,issues+['measurement_row_not_explicit_active_status']
    prone=bool(re.search(r'\b(?:prone|susceptib\w*)\b',fragment,FLAGS))
    actual=bool(re.search(r'\b(?:were\s+flooded|was\s+flooded|experienced\s+flood|binaha|binabaha)\b',fragment,FLAGS))
    if prone and not actual:return 'habitual',issues+['susceptibility_not_current_observation']
    return state,issues


def time_role(text: str, expression: dict, start: int, stop: int,
              state: str|None, elliptical_observation: bool) -> str:
    """Attach a clock to its bounded predicate, on either side of the clock."""
    inherited=previous.time_role(text,expression,start,stop,state,elliptical_observation)
    if DURATION.fullmatch(expression['text']):return 'unspecified'
    if state=='forecast':return 'unspecified'
    cues=list(TEMPORAL_PREDICATE.finditer(text,start,stop))
    clocks=list(TIME.finditer(text,start,stop))
    left=max([start]+[m.end()for m in clocks if m.end()<=expression['start']])
    right=min([stop]+[m.start()for m in clocks if m.start()>=expression['end']])
    before=[m for m in cues if left<=m.start() and m.end()<=expression['start']]
    after=[m for m in cues if expression['end']<=m.start()<right]
    # A pre-clock predicate governs its trailing clock. A clause-opening clock
    # otherwise attaches to the first following predicate, not a later event.
    chosen=before[-1]if before else after[0]if after else None
    if chosen is None:return inherited
    if len(before)>1 and re.search(r'\b(?:or|either|o|alinman)\b',text[before[-2].end():chosen.start()],FLAGS):
        return 'unspecified'
    if not before and len(after)>1 and re.search(r'\b(?:or|either|o|alinman)\b',text[chosen.end():after[1].start()],FLAGS):
        return 'unspecified'
    cue=chosen.group().casefold()
    if re.match(r'publish|publication|inilathala|nailathala',cue):return 'publication'
    if re.match(r'report|ulat|iniulat|inulat|naiulat|nag-ulat',cue):
        # A reported-state predicate ("reported dry") differs from issuance of
        # a report. Preserve the existing explicit clearance/recession scope.
        state_complement=re.match(r'reported\s+(?:dry|cleared|subsided|receding)\b',text[chosen.start():right],FLAGS)
        if not before and state_complement and state in {'cleared','subsided','receding'}:
            return 'clearance'if state=='cleared'else'recession'
        return 'report'
    if re.match(r'reced|subsid|humup|humuh',cue):return 'recession'
    if cue in {'cleared','dry','tuyo'}:return 'clearance'
    if re.match(r'observed|na-observe|naobserbahan',cue):return 'observation'
    if cue in {'nagsimula','began','started'}:
        # The subject around this particular predicate, not a flood word in a
        # different subordinate event, establishes whether this is flood onset.
        lo=max(start,chosen.start()-65)
        bounds=list(re.finditer(r'[,;]|\b(?:before|after|that|bago|matapos|na)\b',text[lo:chosen.start()],FLAGS))
        if bounds:lo+=bounds[-1].end()
        hi=min(right,chosen.end()+100)
        bound=re.search(r'[,;]|\b(?:before|after|that|bago|matapos)\b',text[chosen.end():hi],FLAGS)
        if bound:hi=chosen.end()+bound.start()
        subject=text[lo:hi]
        if re.search(r'\b(?:rain(?:fall)?|pag-ulan|classes|suspension|schedule)\b',subject,FLAGS):return 'unspecified'
        if re.search(r'\b(?:not|never|hindi|di|would|might|may|maaaring)\b',subject,FLAGS):return 'unspecified'
        return 'onset'if FLOOD.search(subject)else'unspecified'
    return inherited


TEMPORAL_PREDICATE=re.compile(r'\b(?:publication|published|inilathala|nailathala|report(?:ed|ing)?|ulat|iniulat|inulat|naiulat|nag-ulat|reced\w*|subsid\w*|humuhupa|humupa|cleared|dry|tuyo|nagsimula|began|started|observed|na-observe|naobserbahan)\b',FLAGS)


def joint_locality(text: str, start: int, stop: int, targets: list[dict]) -> bool:
    """A source-complete shared-designator list with one joint indoor level."""
    if len(targets)<2 or any(m['label']!='LOCAL_AREA'for m in targets):return False
    a=min(m['start']for m in targets);b=max(m['end']for m in targets)
    if not start<=a<b<=stop:return False
    fragment=text[start:stop]
    if re.search(r'\b(?:both|each|pareho\w*|bawat|respectively|kanya-kanya)\b',fragment,FLAGS):return False
    if not re.fullmatch(r'(?:Puroks?|Sitios?)\s+\d+[A-Za-z]?(?:\s*(?:,|and|at|&)\s*\d+[A-Za-z]?)+',text[a:b],FLAGS):return False
    if not re.search(r'\b(?:houses|homes|first\s+floor|bahay|palapag)\b',fragment,FLAGS):return False
    return bool(FLOOD.search(fragment))


def derive_depth_scope(raw: str) -> tuple[str,list[str]]:
    tags=[]
    if re.search(r'\b(?:about|around|almost|halos|nearly|approximately|roughly|humigit-kumulang)\b',raw,FLAGS):tags.append('approximate')
    if re.search(r'\b(?:above|below)\b',raw,FLAGS):tags.append('relative_gauge')
    if re.search(rf'{NUMBER}\s*(?:to|[-–]|hanggang)\s*{NUMBER}',raw,FLAGS):return 'range',tags+['not_a_point_measurement']
    if re.match(r'(?:up\s+to|as\s+high\s+as|hindi\s+hihigit\s+sa)\b',raw,FLAGS)or re.match(rf'hanggang\s+{NUMBER}\b',raw,FLAGS):return 'maximum',tags+['upper_bound']
    if raw.casefold()in{'deep','malalim'}:return 'unspecified',tags
    return 'point',tags


def target_groups(fragment: str, targets: list[dict], expressions: list[dict], kind: str,
                  *, source_start: int|None=None, full_text: str|None=None) -> list[tuple]:
    if base.AMBIGUOUS.search(fragment):
        return [([], 'unresolved', 'Explicitly unidentified target; range does not resolve it.')for _ in expressions]
    if kind=='depth' and len(targets)>1 and len(expressions)==1:
        if source_start is not None and full_text is not None and joint_locality(full_text,source_start,source_start+len(fragment),targets):
            return [(targets,'collective','One source-supported joint indoor observation; not independent per-place measurements.')]
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
    event_anchor={};affected_before_destination=[];destination_stop=-1;continuation_gap=0
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
            if '\n\n' in text[last_stop:start]:event_anchor={};affected_before_destination=[]
            last_stop=stop
            continuation_gap = 0 if local else continuation_gap + 1
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
            elif not local and prior_single and not base.AMBIGUOUS.search(fragment)and (re.search(r'\b(?:floodwaters?|floodwater|baha)\b',fragment,FLAGS) or continuation_gap<=2 and re.search(r'\b(?:deep\s+flood|malalim\s+na\s+baha)\b',fragment,FLAGS)):
                targets=prior_single;first=targets[0]['start'];evidence={'start':first,'end':stop,'text':text[first:stop]}
            if not local and not targets and len(prior_single)==1 and state in {'subsided','receding','cleared'} and not base.AMBIGUOUS.search(fragment) and re.match(r'\s*(?:it|ito)\b',fragment,FLAGS):
                targets=prior_single
                first=targets[0]['start'];evidence={'start':first,'end':stop,'text':text[first:stop]}
            if not local and not targets and affected_before_destination and stop-destination_stop<=400 and not base.AMBIGUOUS.search(fragment) and re.search(r'\b(?:residents?.{0,35}rescu|rescued|nasagip|iniligtas|sinagip)\w*\b',fragment,FLAGS):
                targets=affected_before_destination
                first=min(m['start']for m in targets)
                evidence={'start':first,'end':stop,'text':text[first:stop]}
            if not local and state in {'subsided','receding','cleared'} and len(targets)==1:
                identity=(targets[0]['label'],targets[0]['text'].casefold())
                anchor=event_anchor.get(identity)
                if anchor is not None:
                    targets=[anchor]
                    evidence={'start':anchor['start'],'end':stop,'text':text[anchor['start']:stop]}
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
                row_joint=row_joint or joint_locality(text,start,stop,targets)
                if not targets and prior_single and re.search(r'\b(?:evacuat\w*\s+to|lumikas\s+sa)\b',fragment,FLAGS):
                    affected_before_destination=deepcopy(prior_single);destination_stop=stop
                elif targets:
                    affected_before_destination=[]
                if len(targets)==1 and state in {'active','historical','rising'}:
                    identity=(targets[0]['label'],targets[0]['text'].casefold())
                    new_clock=bool(ts and state!='rising')
                    if identity not in event_anchor or new_clock:event_anchor[identity]=deepcopy(targets[0])
                    event_anchor={identity:event_anchor[identity]}
                elif targets:event_anchor={}
                prior_single=targets if len(targets)==1 and targets[0]['label']in{'ROAD','LANDMARK','LOCAL_AREA','BARANGAY'}else[]
                prior_list=targets if len(targets)>1 else[]
            elif not row_continuation:row_targets=[];row_joint=False
            for d,(assigned,scope,reason) in zip(ds,target_groups(fragment,targets,ds,'depth',source_start=start,full_text=text)):
                collective=bool(re.search(r'\b\d+\s+(?:barangays|villages|areas|communities)\b',fragment,FLAGS))
                if scope=='collective'and derive_depth_scope(d['text'])[0]!='range'and re.search(r'\bmga\s+sumusunod\b',fragment,FLAGS):collective=True
                if scope=='collective'and derive_depth_scope(d['text'])[0]!='range'and joint_locality(text,start,stop,targets):collective=True
                add('depth',d,evidence,assigned,scope,reason,collective_depth=collective,
                    qualifiers=['predicted_only']if state=='forecast'else[])
                if assigned and (measured_table or re.match(r'water\s+level',fragment,FLAGS)):
                    expression_id=next(e['id']for e in expressions if (e['start'],e['end'],e['label'])==(d['start'],d['end'],d['label']))
                    inventory_rows.append({'line':line_start,'expression_id':expression_id,'targets':deepcopy(assigned),
                        'evidence':deepcopy(evidence),'table_context':wet_row or bool(re.search(r'SUBSIDED|water\s+level',line,FLAGS))})
            for t,(assigned,scope,reason) in zip(ts,target_groups(fragment,targets,ts,'time')):
                role=time_role(text,t,start,stop,state,elliptical)
                event_duration=bool(DURATION.fullmatch(t['text'])and targets and FLOOD.search(fragment)and re.search(r'\b(?:rose|rising|tumaas|tumataas)\b',fragment,FLAGS))
                if role in {'report','publication'} or DURATION.fullmatch(t['text'])and not event_duration:
                    assigned=[];scope='unresolved';reason='Report/duration evidence does not establish a per-location event clock.'
                elif role=='unspecified' and (not base.FLOOD.search(fragment) or re.search(r'\b(?:rain(?:fall)?|pag-ulan|classes|schedule)\b',fragment,FLAGS)):
                    assigned=[];scope='unresolved';reason='Unsupported temporal subject or role.'
                add('time',t,evidence,assigned,scope,reason,role=role)
            if re.search(r'\b(?:visited|visit|flew|arrived|evacuated\s+to|evacuation\s+center)\b',fragment,FLAGS)and not re.search(r'\b(?:was\s+flooded|were\s+flooded|binaha|binabaha)\b',fragment,FLAGS):
                status_targets=[]
            else:status_targets=targets
            if not local and state=='active' and not ds and not base.PRONOUN.search(fragment) and not re.search(r'\b(?:there|roon|doon)\b',fragment,FLAGS):
                status_targets=[]
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
    repair_article_context(value, output)
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


def words(text: str) -> list[str]:
    return re.findall(r'\w+', text.casefold())


def exact_target(text: str, start: int, stop: int, mentions: list[dict], labels: set[str]) -> list[dict]:
    """Compare complete source words; never repair/resize a neural span."""
    expected = words(text[start:stop])
    hits = [m for m in mentions if m['label'] in labels and start <= m['start'] < m['end'] <= stop
            and words(m['text']) == expected and not m['text'].strip().isdigit()]
    return hits if len(hits) == 1 else []


def measured_row(text: str, start: int, stop: int, expressions: list[dict], mentions: list[dict], allow_named_row: bool = False) -> dict | None:
    ds = [e for e in expressions if e['label'] == 'DEPTH' and start <= e['start'] < e['end'] <= stop]
    if not ds and not allow_named_row:
        return None
    first = min((e['start'] for e in ds), default=stop)
    prefix = text[start:first]
    delimiter = re.search(r'\s*(?:[-–—:]|\s=)\s*$', prefix)
    if (delimiter is None and ds) or ';' in text[start:stop]:
        return None
    end = start + delimiter.start() if delimiter is not None else stop
    subject = text[start:end]
    junctions = list(re.finditer(r'\b(?:cor\.?|corner|intersection\s+(?:with|of)|kanto\s+ng)\s+', subject, FLAGS))
    if not ds and (not junctions or TIME.search(subject) or re.search(r'\b(?:was|were|had|has|is|are|ay|flood\w*|baha|binaha|reported|report|update|forecast|rain)\b', subject, FLAGS)):
        return None
    targets = []
    reason = 'Incomplete source-delimited location; no broad-locality substitution.'
    if junctions:
        if len(junctions) != 1:
            return None
        junction = junctions[0]
        left = start
        # A comma-delimited administrative prefix is context, not a road.
        if ',' in subject[:junction.start()]:
            left += subject.rfind(',', 0, junction.start()) + 1
        preposition = re.match(r'\s*(?:(?:at|along|sa|on)\s+)', text[left:end], FLAGS)
        if preposition:
            left += preposition.end()
        middle_a, middle_b = start + junction.start(), start + junction.end()
        right_end = end
        direction = re.search(r'\s*(?:\((?:northbound|southbound|eastbound|westbound)\)|NB/SB|NB|SB)\s*$', text[middle_b:end], FLAGS)
        if direction:
            right_end = middle_b + direction.start()
        left_targets = exact_target(text, left, middle_a, mentions, {'ROAD', 'LANDMARK', 'LOCAL_AREA'})
        right_targets = exact_target(text, middle_b, right_end, mentions, {'ROAD', 'LANDMARK', 'LOCAL_AREA'})
        if left_targets and right_targets:
            targets = left_targets + right_targets
        numeric = [e for e in ds if re.search(rf'\b{NUMBER}\s*{UNIT}', e['text'], FLAGS)]
        gauges = [e for e in ds if re.fullmatch(rf'{QUALIFIER}{GAUGE}', e['text'], FLAGS)]
        paired = len(ds) == 2 and len(numeric) == len(gauges) == 1
        if paired:
            ordered = sorted(ds, key=lambda e:e['start'])
            paired = bool(re.fullmatch(r'\s*[,(/]?\s*', text[ordered[0]['end']:ordered[1]['start']]))
        if len(ds) > 1 and not paired:
            targets = []
            reason = 'Multiple or conflicting junction measurements; no ordered-value guess.'
        elif targets:
            reason = 'Complete source junction with one measurement or co-described numeric/verbal depths.'
    else:
        a = start
        if re.match(r'\s*(?:Brgy\.?|Barangay)\b', subject, FLAGS) and ',' in subject:
            a = start + subject.rfind(',') + 1
        preposition = re.match(r'\s*(?:(?:at|along|sa|on)\s+)', text[a:end], FLAGS)
        if preposition:
            a += preposition.end()
        targets = exact_target(text, a, end, mentions, {'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY'})
        # Preserve other established table conventions (e.g. adjacent names at
        # a colon). This branch only rejects visibly missing specific subjects.
        specific = a != start or bool(re.match(r'\s*\d+\s+\w+', subject))
        if not targets and not specific:
            return None
        if targets:
            reason = 'One complete source-delimited measured-row location.'
    return {'targets': targets, 'reason': reason, 'junction': bool(junctions), 'expressions': ds}


def access_heading(line: str) -> tuple[str, list[str]] | None:
    clean = line.strip().rstrip(':')
    patterns = (
        (r'(?:impassable\s+to|not\s+passable\s+to|not\s+passable\s+sa)\s+all(?:\s+types?\s+of)?\s+vehicles|hindi\s+madaanan\s+ng\s+lahat\s+ng\s+sasakyan', 'impassable_all'),
        (r'(?:impassable\s+to|not\s+passable\s+to|not\s+passable\s+sa)\s+light\s+vehicles|hindi\s+madaanan\s+ng\s+maliliit\s+na\s+sasakyan', 'light_vehicle_closed'),
        (r'passable\s+(?:with\s+caution|pero\s+mag-ingat)|madaanan\s+nang\s+may\s+pag-iingat', 'passable_unspecified'),
        (r'passable\s+to\s+all(?:\s+types?\s+of)?\s+vehicles|madaanan\s+ng\s+lahat\s+ng\s+sasakyan', 'passable_all'),
    )
    for pattern, value in patterns:
        if re.fullmatch(pattern, clean, FLAGS):
            return value, [clean]
    return None


def repair_article_context(raw: dict, output: dict) -> None:
    """Repair bounded source structures in the successor's own graph only."""
    text = raw['text']
    mentions = raw['mentions']
    facts = output['facts']
    relations = output['relations']
    expressions = output['expressions']
    reasons = {u['fact_id']:u['reason'] for u in output['unassigned']}

    def replace(fact: dict, targets: list[dict], evidence: dict, reason: str, joint: bool = False) -> None:
        relations[:] = [r for r in relations if r['fact_id'] != fact['id']]
        if targets:
            relations.append({'id': '', 'fact_id': fact['id'], 'target_entity_ids':[m['id'] for m in targets],
                'scope':'collective' if joint and len(targets)>1 else 'shared' if len(targets)>1 else 'local',
                'evidence':[deepcopy(evidence)], 'uncertainty':[], 'overrides_relation_id':None, 'reason':reason})
            fact['uncertainty'] = []
        else:
            fact['uncertainty'] = [reason]
            reasons[fact['id']] = reason

    def append(kind: str, value: str, targets: list[dict], evidence: dict, reason: str,
               span: dict | None = None, qualifiers: list[str] | None = None) -> None:
        entity_ids = []
        if span is not None:
            entity = next((e for e in expressions if (e['start'],e['end'],e['label']) == (span['start'],span['end'],'TIME')), None)
            if entity is None:
                entity = {'id':f'x{len(expressions)}', **span, 'label':'TIME'}
                expressions.append(entity)
            entity_ids = [entity['id']]
        fact = {'id':f'f{len(facts)}', 'kind':kind, 'entity_ids':entity_ids, 'value':value,
                'temporal_role':'observation' if kind=='time' else None, 'depth_scope':None,
                'qualifiers':list(qualifiers or []), 'uncertainty':[], 'evidence':[deepcopy(evidence)]}
        facts.append(fact)
        replace(fact, targets, evidence, reason, joint=len(targets)>1)

    # Preserve original mentions and source facts. A dateline is not itself an
    # affected-place assertion. A later explicit occurrence can still be one.
    dateline = re.match(r'^\s*[A-ZÀ-Ý][\w .’\'-]*,\s*(?:Philippines|Pilipinas)\s*[—–-]\s*', text)
    if dateline and not re.match(r'(?:the\s+city|ang\s+lungsod)\s+(?:was\s+flooded|ay\s+binaha)', text[dateline.end():], FLAGS):
        ids = {m['id'] for m in mentions if m['label'] in {'CITY','PROVINCE'} and m['end'] <= dateline.end()}
        for fact in list(facts):
            linked = next((r for r in relations if r['fact_id']==fact['id']), None)
            if linked and ids.intersection(linked['target_entity_ids']):
                targets = [m for m in mentions if m['id'] in linked['target_entity_ids'] and m['id'] not in ids]
                replace(fact, targets, fact['evidence'][0], 'Dateline is not an independent city flood observation.')

    active = False
    clock = None
    heading = None
    header_start = 0
    offset = 0
    for row in text.splitlines(keepends=True):
        start, stop = offset, offset + len(row.rstrip('\r\n'))
        offset += len(row)
        line = text[start:stop]
        stripped = line.strip()
        if not stripped:
            active = False; clock = None; heading = None
            continue
        list_words = re.search(r'\b(?:following|sumusunod|listed|below|listahan|talaan)\b', line, FLAGS)
        state, _ = state_for(line)
        is_list = bool(list_words and FLOOD.search(line) and state not in {'forecast','negated','habitual','cleared','subsided'})
        if is_list:
            active = True; clock = None; heading = None; header_start = start
            times = [m for m in TIME.finditer(text,start,stop) if re.fullmatch(CLOCK,m.group(),FLAGS)]
            issuance = re.search(r'\b(?:issued|published|publication|iniulat|inilathala|inulat)\b', line, FLAGS)
            asof = re.search(r'\b(?:as\s+of|pagsapit\s+ng|noong|bandang)\s*$', line[:times[0].start()-start], FLAGS) if len(times)==1 else None
            if len(times)==1 and asof and not issuance and not base.FORECAST.search(line):
                hit = times[0]
                clock = {'start':hit.start(),'end':hit.end(),'text':hit.group()}
                for fact in facts:
                    if fact['kind']=='time' and any(e['id'] in fact['entity_ids'] and e['start']==hit.start() and e['end']==hit.end() for e in expressions):
                        fact['temporal_role']='observation'
            continue
        access = access_heading(line)
        if access is not None:
            if active:
                heading = (access,start,stop)
            # Preserve the heading's qualifier even when no target is known.
            for fact in facts:
                if fact['kind']=='access' and any(start<=e['start']<e['end']<=stop for e in fact['evidence']):
                    fact['value']=access[0];fact['qualifiers']=list(access[1])
                    if active:
                        replace(fact, [], {'start':start,'end':stop,'text':line},
                                'List access heading governs following rows, not a preceding location.')
            continue
        parsed = measured_row(text,start,stop,expressions,mentions,allow_named_row=active)
        if parsed is not None:
            targets = parsed['targets']
            evidence = {'start':start,'end':stop,'text':line}
            ids = {e['id'] for e in parsed['expressions']}
            for fact in list(facts):
                if fact['kind']=='depth' and fact['entity_ids'] and set(fact['entity_ids']) <= ids:
                    replace(fact, targets, evidence, parsed['reason'], joint=parsed['junction'])
            if active and state not in {'forecast','negated','habitual','cleared','subsided','receding'}:
                inherited = {'start':header_start,'end':stop,'text':text[header_start:stop]}
                if clock is not None and not any(f['kind']=='time' and any(start<=e['start']<e['end']<=stop for e in f['evidence']) for f in facts):
                    append('time',clock['text'],targets,inherited,'Explicit flooding-list as-of clock; no onset inference.',span=clock)
                if not any(f['kind']=='status' and any(start<=e['start']<e['end']<=stop for e in f['evidence']) for f in facts):
                    append('status','active',targets,inherited,'Explicit affected-flooding list and supported measured row.')
                if heading is not None:
                    (value,qualifiers),a,b = heading
                    own_access = any(f['kind']=='access' and any(start<=e['start']<e['end']<=stop for e in f['evidence']) for f in facts)
                    if not own_access:
                        append('access',value,targets,{'start':a,'end':stop,'text':text[a:stop]},
                               'Explicit vehicle heading bounded to its supported list rows.',qualifiers=qualifiers)
            continue
        # Exact standalone administrative headings can continue the same list;
        # free narrative, updates and unsupported headings end inherited scope.
        local = [m for m in mentions if start<=m['start']<m['end']<=stop and m['label'] in {'CITY','PROVINCE','BARANGAY','LOCAL_AREA'}]
        heading_name = re.sub(r'\s+\([\w .’\'-]{1,80}\)\s*$', '', stripped)
        administrative = len(local)==1 and words(heading_name)==words(local[0]['text'])
        if not administrative:
            active = False; clock = None; heading = None

    linked = {r['fact_id'] for r in relations}
    output['unassigned'] = []
    for fact in facts:
        if fact['id'] not in linked:
            reason = reasons.get(fact['id'], 'No complete supported location for this source scope.')
            if not fact['uncertainty']:
                fact['uncertainty']=[reason]
            output['unassigned'].append({'fact_id':fact['id'],'reason':reason})
    for i,relation in enumerate(relations):
        relation['id']=f'r{i}'
    expressions.sort(key=lambda e:(e['start'],e['end']))
