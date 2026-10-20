"""Twenty-four fictional repair checks; never corpus members or neural inputs."""
from __future__ import annotations

from .context_acceptance_cases import make_case, entity, depth, time, status

FAMILIES=('parallel_updates','collective_ranges','abbreviated_lists',
          'temporal_evidence','flood_evidence','facility_scope')


def core_cases() -> list[dict]:
    cases=[]
    for language in ('english','taglish'):
        en=language=='english'
        def add(family: str, contrast: str, english: str, taglish: str, entities: list,
                facts: list, links: list, reason: str) -> None:
            cases.append(make_case(family,language,contrast,english if en else taglish,
                entities,facts,links,['No invented target, point depth, onset or absolute timestamp.'],reason))
        add('parallel_updates','supported',
            'Yesterday Violet Road had knee-deep flooding. Today, water was waist-deep on Piña Road.',
            'Yesterday ay knee-deep ang baha sa Violet Road. Today ay waist-deep sa Piña Road.',
            [entity('p1','Violet Road'),entity('p2','Piña Road'),entity('d1','knee-deep','DEPTH'),entity('d2','waist-deep','DEPTH'),entity('t1','Yesterday','TIME'),entity('t2','Today','TIME')],
            [depth('f1','d1'),depth('f2','d2'),time('ft1','t1','observation'),time('ft2','t2','observation'),status('s1','historical'),status('s2','active')],
            [('f1',['p1'],'local'),('f2',['p2'],'local'),('ft1',['p1'],'local'),('ft2',['p2'],'local'),('s1',['p1'],'local'),('s2',['p2'],'local')],
            'An explicit current qualitative observation can omit the repeated predicate; its target and time remain separate.')
        add('parallel_updates','counterexample',
            'At 2 PM Violet Road had knee-deep flooding. Piña Road was merely mentioned today; its depth is unknown.',
            'At 2 PM, knee-deep ang baha sa Violet Road. Nabanggit lang ang Piña Road today; unknown ang depth nito.',
            [entity('p1','Violet Road'),entity('p2','Piña Road'),entity('d','knee-deep','DEPTH'),entity('t1','2 PM','TIME'),entity('t2','today','TIME')],
            [depth('f','d'),time('ft1','t1','observation'),time('ft2','t2','unspecified')],
            [('f',['p1'],'local'),('ft1',['p1'],'local')],
            'A mentioned location alone cannot inherit the preceding observation or clock.')
        add('collective_ranges','supported',
            'Flood depths across Violet Road and Piña Road ranged from 11 to 23 cm; individual values are unknown.',
            'Ang flood depths sa Violet Road at Piña Road ay 11 to 23 cm; walang individual measurement.',
            [entity('p1','Violet Road'),entity('p2','Piña Road'),entity('d','11 to 23 cm','DEPTH')],
            [depth('f','d','range',['not an individual scalar'])],[('f',['p1','p2'],'collective')],
            'An explicitly named range stays one collective relation.')
        add('collective_ranges','counterexample',
            'Violet Road and Piña Road were mentioned. One had 11 to 23 cm of floodwater; the report did not say which.',
            'Nabanggit ang Violet Road at Piña Road. May 11 to 23 cm na baha sa isa; hindi tinukoy kung alin.',
            [entity('p1','Violet Road'),entity('p2','Piña Road'),entity('d','11 to 23 cm','DEPTH')],
            [depth('f','d','range')],[], 'A range does not resolve an explicitly unknown target.')
        access={'id':'fa','kind':'access','value':'light_vehicle_closed'}
        add('abbreviated_lists','supported',
            'Violet St., P. Rivera Ave., and Piña Court were not passable to light vehicles.',
            'Hindi passable sa maliliit na sasakyan ang Violet St., P. Rivera Ave., at Piña Court.',
            [entity('p1','Violet St.'),entity('p2','P. Rivera Ave.'),entity('p3','Piña Court','LOCAL_AREA')],
            [access],[('fa',['p1','p2','p3'],'shared')],
            'Abbreviation punctuation must not fragment a complete explicit list.')
        add('abbreviated_lists','counterexample',
            'Violet St., Pine Road, and Amber Road were not passable to light vehicles.',
            'Hindi passable sa maliliit na sasakyan ang Violet St., Pine Road, at Amber Road.',
            [entity('p1','Violet St.'),entity('p2','Pine Road')],[access],[],
            'Fixture inputs deliberately omit a named list member; partial shared groups must remain unresolved.')
        add('temporal_evidence','supported',
            'Flooding on Violet Road was observed at 4 PM.',
            'Na-observe ang baha sa Violet Road at 4 PM.',
            [entity('p','Violet Road'),entity('t','4 PM','TIME')],
            [time('ft','t','observation')],[('ft',['p'],'local')],
            'An explicit observation clock is distinct from publication and onset.')
        add('temporal_evidence','counterexample',
            'A report on Tuesday said Violet Road had knee-deep flooding in less than an hour.',
            'Sa report nitong Martes, knee-deep ang baha sa Violet Road sa less than an hour.',
            [entity('p','Violet Road'),entity('d','knee-deep','DEPTH'),entity('t1','Tuesday'if en else'Martes','TIME'),entity('t2','less than an hour','TIME')],
            [depth('f','d'),time('ft1','t1','report'),time('ft2','t2','unspecified')],
            [('f',['p'],'local')], 'Report date and rise duration remain recognized but unassigned to an observation clock.')
        add('flood_evidence','supported',
            'Violet Road was flooded with knee-deep water; no residents were injured.',
            'Knee-deep ang baha sa Violet Road; walang residents na nasaktan.',
            [entity('p','Violet Road'),entity('d','Knee-deep'if not en else'knee-deep','DEPTH')],
            [depth('f','d'),status('s','active')],[('f',['p'],'local'),('s',['p'],'local')],
            'Negated injuries do not negate an explicit flood observation.')
        add('flood_evidence','counterexample',
            'Residents from Violet Road were evacuated because the area is flood-prone.',
            'Residents mula Violet Road ay evacuated dahil flood-prone ang area.',
            [entity('p','Violet Road')],[status('s','habitual')],[],
            'Evacuation and susceptibility do not establish current active flooding at a road.')
        add('facility_scope','supported',
            'Piña School was flooded with knee-deep water.',
            'Piña School ay binaha ng knee-deep na tubig.',
            [entity('p','Piña School','LANDMARK'),entity('d','knee-deep','DEPTH')],
            [depth('f','d'),status('s','active')],[('f',['p'],'local'),('s',['p'],'local')],
            'A facility with its own explicit flooding predicate remains an eligible location.')
        add('facility_scope','counterexample',
            'Violet Road had knee-deep flooding. People walked through floodwater on the road where Piña School is located.',
            'Knee-deep ang baha sa Violet Road. Naglakad sa baha ang mga tao sa kalsada kung saan matatagpuan ang Piña School.',
            [entity('p1','Violet Road'),entity('p2','Piña School','LANDMARK'),entity('d','Knee-deep'if not en else'knee-deep','DEPTH')],
            [depth('f','d'),status('s','active')],[('f',['p1'],'local'),('s',['p1'],'local')],
            'A facility used to describe the flooded road does not inherit its flood status.')
    return cases
