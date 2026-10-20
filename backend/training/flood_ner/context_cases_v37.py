"""Forty-eight fictional grouping/repair cases; never corpus additions."""
from __future__ import annotations
from .context_acceptance_cases import make_case,entity,depth,time,status

FAMILIES=('canonical_groups','multirow_summaries','measurement_boundary','trend_status',
    'duration_links','bounded_antecedents','temporal_context','row_junction_scope')


def core_cases() -> list[dict]:
    result=[]
    for n,language in enumerate(('english','tagalog','taglish')):
        def phr(*xs):return xs[n]
        def add(family,contrast,texts,entities,facts,links,reason):
            c=make_case('v37_'+family,language,contrast,texts[n],entities,facts,links,
                ['No invented scalar, timestamp, target, status or cross-scope association.'],reason)
            c['family']=family
            if family=='multirow_summaries'and contrast=='supported':
                # The schema permits a null grouped fact over original row expressions.
                next(f for f in c['record']['facts']if f['id']=='summary')['value']=None
            result.append(c)
        p='Daan Sampaguita';q='Daan Luntian';school='Paaralang Álamat'
        locs=[entity('p',p),entity('q',q)]
        gauge=phr('knee-deep','abot-tuhod','knee-deep')
        duration=phr('two hours','dalawang oras','two hours')
        clock=phr('3 PM','alas-tres ng hapon','3 PM')
        def es(id,text,label='DEPTH'):return entity(id,text,label)
        add('canonical_groups','supported',
            (f'{p} was flooded. {q} was flooded.',f'Binaha ang {p}. Binaha ang {q}.',f'Flooded ang {p}. Flooded din ang {q}.'),
            locs,[status('s1','active'),status('s2','active')],[('s1',['p'],'local'),('s2',['q'],'local')],
            'Separate evidence predicates are not merged merely because both values are active.')
        add('canonical_groups','counterexample',
            (f'{p} and {q} were both flooded.',f'Parehong binaha ang {p} at {q}.',f'Parehong flooded ang {p} at {q}.'),
            locs,[status('s','active')],[('s',['p','q'],'shared')],
            'One explicit shared predicate remains shared rather than inventing separate observations.')
        a=phr('10 cm','10 sentimetro','10 cm');b=phr('20 cm','20 sentimetro','20 cm')
        add('multirow_summaries','supported',
            (f'Collective depth summary of the following measured rows:\n{p}: {a}.\n{q}: {b}.',
             f'Pinagsamang tala ng lalim ng mga sumusunod na hanay:\n{p}: {a}.\n{q}: {b}.',
             f'Collective depth summary ng mga measured row:\n{p}: {a}.\n{q}: {b}.'),
            locs+[es('d1',a),es('d2',b)],
            [depth('f1','d1'),depth('f2','d2'),{'id':'summary','kind':'depth','entity_ids':['d1','d2'],'depth_scope':'collective'}],
            [('f1',['p'],'local'),('f2',['q'],'local'),('summary',['p','q'],'collective')],
            'An explicit collective record preserves both row gauges and a null grouped summary, not a shared scalar.')
        add('multirow_summaries','counterexample',
            (f'{p}: {a} of water yesterday.\n{q}: {b} of water today.',
             f'{p}: {a} ang tubig kahapon.\n{q}: {b} ang tubig ngayon.',
             f'{p}: {a} ang water yesterday.\n{q}: {b} ang water today.'),
            locs+[es('d1',a),es('d2',b),es('t1',phr('yesterday','kahapon','yesterday'),'TIME'),es('t2',phr('today','ngayon','today'),'TIME')],
            [depth('f1','d1'),depth('f2','d2'),time('ft1','t1','unspecified'),time('ft2','t2','unspecified')],
            [('f1',['p'],'local'),('f2',['q'],'local')],
            'Different row dates and no flood predicate supply no common event-clock or collective summary.')
        numeric=phr('5 feet','5 talampakan','5 feet')
        add('measurement_boundary','supported',
            (f'Floodwater on {p} reached {numeric} deep.',f'Umabot sa {numeric} ang lalim ng baha sa {p}.',f'Umabot sa {numeric} deep ang baha sa {p}.'),
            [entity('p',p),es('d',numeric)],[depth('f','d'),status('s','active')],[('f',['p'],'local'),('s',['p'],'local')],
            'One numerical measurement excludes a second independent trailing deep descriptor.')
        add('measurement_boundary','counterexample',
            (f'Water on {p} was deep; no numerical depth was given.',f'Malalim ang tubig sa {p}; walang ibinigay na bilang.',f'Deep ang water sa {p}; walang exact number.'),
            [entity('p',p),es('d',phr('deep','Malalim','Deep'))],[depth('f','d','unspecified')],[('f',['p'],'local')],
            'A standalone physical depth descriptor remains recognized without asserting active flood status.')
        add('trend_status','supported',
            (f'Floodwater on {p} rose at {clock}.',f'Tumaas ang baha sa {p} noong {clock}.',f'Tumaas ang floodwater sa {p} at {clock}.'),
            [entity('p',p),es('t',clock,'TIME')],[status('s','rising'),time('ft','t','observation')],
            [('s',['p'],'local'),('ft',['p'],'local')],'Explicit rising water is distinct from generic active and does not establish onset.')
        add('trend_status','counterexample',
            (f'Water on {p} receded at {clock}; the road was not yet dry.',f'Humupa ang baha sa {p} noong {clock}; hindi pa tuyo ang kalsada.',f'Nag-subside ang baha sa {p} at {clock}; hindi pa dry ang kalsada.'),
            [entity('p',p),es('t',clock,'TIME')],[status('s','subsided'),time('ft','t','recession')],
            [('s',['p'],'local'),('ft',['p'],'local')],'Completed recession does not become clearance when dryness is explicitly denied.')
        add('duration_links','supported',
            (f'Floodwater on {p} rose for {duration}.',f'Tumaas ang baha sa {p} sa loob ng {duration}.',f'Tumaas ang floodwater sa {p} for {duration}.'),
            [entity('p',p),es('t',duration,'TIME')],[status('s','rising'),time('ft','t','unspecified')],
            [('s',['p'],'local'),('ft',['p'],'local')],'An explicit change duration can attach to its flood target while remaining unspecified, not onset or observation time.')
        add('duration_links','counterexample',
            (f'A meeting at {school} lasted {duration}. {p} was mentioned.',f'Tumagal ng {duration} ang pulong sa {school}. Nabanggit ang {p}.',f'Naglast ng {duration} ang meeting sa {school}. Nabanggit ang {p}.'),
            [entity('l',school,'LANDMARK'),entity('p',p),es('t',duration,'TIME')],[time('ft','t','unspecified')],[],
            'A meeting duration supplies no flood-event association to school or mentioned road.')
        add('bounded_antecedents','supported',
            (f'{p} was flooded. The floodwater there remained {gauge}.',f'Binaha ang {p}. Nanatiling {gauge} ang baha roon.',f'Flooded ang {p}. Nanatiling {gauge} ang floodwater doon.'),
            [entity('p',p),es('d',gauge)],[depth('f','d'),status('s','active')],[('f',['p'],'local'),('s',['p'],'local')],
            'One explicit bounded there/roon antecedent supports the preceding flood target; no first-name relocation.')
        add('bounded_antecedents','counterexample',
            (f'{p} was flooded. Families evacuated to {school}. Water was {gauge} at an unidentified site.',
             f'Binaha ang {p}. Lumikas sa {school} ang mga pamilya. {gauge.capitalize()} ang tubig sa hindi tinukoy na lugar.',
             f'Flooded ang {p}. Evacuated sa {school} ang families. May {gauge} water sa unknown site.'),
            [entity('p',p),entity('l',school,'LANDMARK'),es('d',phr(gauge,gauge.capitalize(),gauge))],
            [depth('f','d'),status('s','active')],[('s',['p'],'local')],
            'Evacuation destination and unknown site terminate rather than inherit the previous road depth.')
        add('temporal_context','supported',
            (f'Flooding on {p} was observed at {clock}.',f'Naobserbahan ang baha sa {p} noong {clock}.',f'Na-observe ang flooding sa {p} at {clock}.'),
            [entity('p',p),es('t',clock,'TIME')],[time('ft','t','observation'),status('s','active')],
            [('ft',['p'],'local'),('s',['p'],'local')],'An actual flood-observation clock remains recognized and linked.')
        add('temporal_context','counterexample',
            (f'A report on “12 Oras Balita” mentioned {p}.',f'Nabanggit ang {p} sa ulat ng palabas na “12 Oras Balita”.',f'Nabanggit ang {p} sa report on “12 Oras Balita”.'),
            [entity('p',p)],[],[],
            'A numeric expression inside an explicitly introduced programme title is not a duration or clock; names alone do not make English text Taglish.')
        heading=phr('Observed flooding','Naobserbahang pagbaha','Observed na pagbaha')
        add('row_junction_scope','supported',
            (f'{heading}\n{p} / {q}: {a}; not passable to all vehicles.',
             f'{heading}\n{p} / {q}: {a}; hindi madaanan ng lahat ng sasakyan.',
             f'{heading}\n{p} / {q}: {a}; not passable sa all vehicles.'),
            locs+[es('d',a)],[depth('f','d'),status('s','active'),{'id':'fa','kind':'access','value':'impassable_all'}],
            [('f',['p','q'],'collective'),('s',['p','q'],'collective'),('fa',['p','q'],'collective')],
            'Explicit observed junction row preserves grouped depth/status, with its own complete vehicle restriction.')
        add('row_junction_scope','counterexample',
            (f'{p}: {a}; passable to all vehicles.\n{q}: {b}; not passable to light vehicles.',
             f'{p}: {a}; madaanan ng lahat ng sasakyan.\n{q}: {b}; hindi madaanan ng maliliit na sasakyan.',
             f'{p}: {a}; passable sa all vehicles.\n{q}: {b}; not passable sa light vehicles.'),
            locs+[es('d1',a),es('d2',b)],[depth('f1','d1'),depth('f2','d2'),{'id':'fa1','kind':'access','value':'passable_all'},{'id':'fa2','kind':'access','value':'light_vehicle_closed'}],
            [('f1',['p'],'local'),('f2',['q'],'local'),('fa1',['p'],'local'),('fa2',['q'],'local')],
            'Different rows and vehicle classes cannot collapse into a shared access claim.')
    return result
