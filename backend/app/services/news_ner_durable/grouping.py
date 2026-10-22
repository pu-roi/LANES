"""Observation partitions from exact graph occurrences, never normalized names."""
from __future__ import annotations

from copy import deepcopy

from .contracts import sha


def _overlap(left: list[dict], right: list[dict]) -> bool:
    return any(a['start'] < b['end'] and b['start'] < a['end'] for a in left for b in right)


def _unique(evidence: list[dict]) -> list[dict]:
    return [dict(start=a,end=b,text=t) for a,b,t in sorted({(e['start'],e['end'],e['text']) for e in evidence})]


def observations(graph: dict) -> list[dict]:
    mentions={m['id']:m for m in graph['mentions']};facts={f['id']:f for f in graph['facts']}
    units:dict[tuple,dict]={}
    relations=[r for r in graph['relations'] if r['target_entity_ids']]

    def targets(r: dict) -> tuple:
        return tuple(sorted(r['target_entity_ids'],key=lambda i:(mentions[i]['start'],mentions[i]['end'],i)))

    def add(r: dict, key: tuple, *, ambiguous: bool=False) -> None:
        unit=units.setdefault(key,{'target_entity_ids':list(targets(r)),'scope':r['scope'],'relations':[],
                                   'fact_ids':[],'partition_ambiguous':ambiguous})
        unit['relations'].append(deepcopy(r))
        if r['fact_id'] not in unit['fact_ids']:unit['fact_ids'].append(r['fact_id'])

    for r in relations:
        f=facts[r['fact_id']]
        if f['kind']=='status':
            core=tuple((e['start'],e['end']) for e in f['evidence'])
            add(r,(targets(r),r['scope'],'status',core))
    for r in relations:
        f=facts[r['fact_id']]
        if f['kind']=='status':continue
        matches=[key for key,u in units.items() if key[2]=='status' and tuple(u['target_entity_ids'])==targets(r)
                 and u['scope']==r['scope'] and any(_overlap(f['evidence'],facts[i]['evidence']) for i in u['fact_ids'] if facts[i]['kind']=='status')]
        if len(matches)==1:add(r,matches[0])
        else:
            core=tuple((e['start'],e['end']) for e in f['evidence'])
            add(r,(targets(r),r['scope'],'unanchored',core),ambiguous=len(matches)>1)
    output=[]
    for u in units.values():
        u['fact_ids']=sorted(u['fact_ids']);u['relation_ids']=sorted(r['id'] for r in u['relations'])
        u['evidence']=_unique([e for r in u['relations'] for e in r['evidence']] + [e for i in u['fact_ids'] for e in facts[i]['evidence']])
        identity={k:u[k] for k in ('target_entity_ids','relation_ids','fact_ids','scope','evidence')}
        u['group_id']='g-'+sha(identity)
        output.append(u)
    ordered=sorted(output,key=lambda u:(min(e['start'] for e in u['evidence']),
                   tuple(mentions[i]['start'] for i in u['target_entity_ids']),u['group_id']))
    # IDs are local to the source-bound result, like native mention/fact IDs.
    # The full identity digest above still provides a deterministic tie-break;
    # repeating it in every group/accounting link needlessly expands results.
    for index,unit in enumerate(ordered):unit['group_id']=f'g{index}'
    return ordered
