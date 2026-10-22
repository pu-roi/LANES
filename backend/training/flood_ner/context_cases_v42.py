"""Thirty-six fictional source-independent v42 scenarios and explicit oracles."""
import hashlib

from .location_repair_cases_v40 import mention


def core_cases() -> list[dict]:
    cases = []
    families = ('junction_descriptions','clock_forms_roles','list_time_scope','access_headings','datelines','incomplete_targets')
    for language in ('english','tagalog','taglish'):
        a,b = ('Daan Piña','Daan Áster') if language=='tagalog' else ('Piña Street','Áster Road')
        number,gauge = ('8 pulgada','abot-sakong') if language=='tagalog' else ('8 inches','gutter deep')
        pair = number+', '+gauge
        separator = ' kanto ng ' if language=='tagalog' else ' cor. '
        full_list = {'english':'As of 4:30 p.m, the following roads are flooded:',
                     'tagalog':'Pagsapit ng 4:30 p.m, binaha ang mga sumusunod na kalsada:',
                     'taglish':'As of 4:30 p.m, flooded ang sumusunod na roads:'}[language]
        access_all = {'english':'Impassable to all types of vehicles', 'tagalog':'Hindi madaanan ng lahat ng sasakyan',
                      'taglish':'Not passable sa all vehicles'}[language]
        caution = {'english':'Passable with caution','tagalog':'Madaanan nang may pag-iingat','taglish':'Passable pero mag-ingat'}[language]
        for family in families:
            for supported in (True,False):
                depth = None; times = None; roles = None; access = None; forbidden = []
                if family=='junction_descriptions':
                    if supported:
                        text=f'🌧 {a}{separator}{b} - {pair}'
                        depth=[(number,['n0','n1'],'collective'),(gauge,['n0','n1'],'collective')]
                    else:
                        text={'english':f'{a} had 8 inches of flooding. {b} had knee-deep flooding.',
                              'tagalog':f'Sa {a}, 8 pulgada ang baha. Sa {b}, abot-tuhod ang baha.',
                              'taglish':f'Sa {a}, 8 inches ang flood. Sa {b}, knee-deep ang flood.'}[language]
                        second='abot-tuhod' if language=='tagalog' else'knee-deep'
                        depth=[(number,['n0'],'local'),(second,['n1'],'local')]
                    mentions=[mention(text,a,'ROAD'),mention(text,b,'ROAD',identity='n1')]
                elif family=='clock_forms_roles':
                    if supported:
                        text={'english':f'At 4:30 p.m, flooding was observed on {a}.',
                              'tagalog':f'Nang 4:30 p.m., nagsimula ang baha sa {a}.',
                              'taglish':f'At 4:30 PM, iniulat ang flood sa {a}.'}[language]
                        token,role={'english':('4:30 p.m','observation'),'tagalog':('4:30 p.m.','onset'),'taglish':('4:30 PM','report')}[language]
                        roles=[(token,role)]
                        times=[] if role=='report' else [(token,['n0'],'observation' if role=='observation' else'onset')]
                    else:
                        text={'english':f'Rain started at 4:30 p.m. before flooding on {a} was reported at 6 PM.',
                              'tagalog':f'Nagsimula ang pag-ulan nang 4:30 p.m. bago iniulat ang baha sa {a} nang 6 PM.',
                              'taglish':f'Rain started at 4:30 p.m. bago iniulat ang flood sa {a} at 6 PM.'}[language]
                        roles=[('4:30 p.m.','unspecified'),('6 PM','report')];times=[]
                    mentions=[mention(text,a,'ROAD')]
                elif family=='list_time_scope':
                    gap='' if supported else '\n\nUpdate: no observation clock was supplied.'
                    text=f'{full_list}\n{a} - {pair}{gap}\n{b} - {pair}'
                    mentions=[mention(text,a,'ROAD'),mention(text,b,'ROAD',identity='n1')]
                    times=[('4:30 p.m',['n0'],'observation')]
                    if supported:times.append(('4:30 p.m',['n1'],'observation'))
                elif family=='access_headings':
                    second=f'\n{caution}' if supported else '\n\nOther news: a bridge maintenance schedule was published.'
                    text=f'{full_list}\n{access_all}\n{a} - {pair}{second}\n{b} - {pair}'
                    mentions=[mention(text,a,'ROAD'),mention(text,b,'ROAD',identity='n1')]
                    access=[('impassable_all',['n0'],access_all)]
                    if supported:access.append(('passable_unspecified',['n1'],caution))
                elif family=='datelines':
                    country='Pilipinas' if language=='tagalog' else'Philippines'
                    if supported:
                        text=f'ALON, {country} — Flooding affected the metropolitan region on Wednesday.'
                        mentions=[mention(text,'ALON','CITY')];forbidden=['n0']
                    else:
                        sentence={'english':'Alon City was flooded at 6 PM.','tagalog':'Binaha ang Lungsod Alon nang 6 PM.',
                                  'taglish':'Alon City was flooded nang 6 PM.'}[language]
                        city='Lungsod Alon' if language=='tagalog' else'Alon City'
                        text=f'ALON, {country} — {sentence}'
                        mentions=[mention(text,'ALON','CITY'),mention(text,city,'CITY',identity='n1')]
                        forbidden=['n0'];times=[('6 PM',['n1'],'observation')]
                else:
                    if supported:
                        text=f'{a}{separator}{b} - {pair}'
                        mentions=[mention(text,a,'ROAD')]
                        if language=='tagalog':mentions.append(mention(text,b,'CITY',identity='n1'))
                        if language=='taglish':mentions.append(mention(text,'Áster','ROAD',identity='n1'))
                        depth=[(number,[],None),(gauge,[],None)]
                    else:
                        text=f'{a} - {pair}';mentions=[mention(text,a,'ROAD')]
                        depth=[(number,['n0'],'local'),(gauge,['n0'],'local')]
                identity=f'fictional-v42-{len(cases)}'
                raw={'record_id':identity,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                     'publication':None,'mentions':mentions}
                cases.append({'case_id':identity,'language':language,'family':family,'supported':supported,'raw':raw,
                    'depth':depth,'times':times,'roles':roles,'access':access,'forbidden_targets':forbidden})
    return cases


def result(case: dict, graph: dict) -> dict:
    relations={r['fact_id']:r for r in graph['relations']}
    observed={'depth':[],'times':[],'roles':[],'access':[]}
    for fact in graph['facts']:
        relation=relations.get(fact['id'])
        targets=relation['target_entity_ids'] if relation else[]
        if fact['kind']=='depth':observed['depth'].append((fact['value'],targets,relation['scope']if relation else None))
        if fact['kind']=='time':
            observed['roles'].append((fact['value'],fact['temporal_role']))
            if relation:observed['times'].append((fact['value'],targets,fact['temporal_role']))
        if fact['kind']=='access'and relation:
            observed['access'].extend((fact['value'],targets,q)for q in fact['qualifiers'])
    failed=[]
    for key in ('depth','times','roles','access'):
        if case[key] is not None and observed[key]!=[tuple(item)for item in case[key]]:failed.append(key)
    if any(set(r['target_entity_ids'])&set(case['forbidden_targets']) for r in graph['relations']):failed.append('dateline')
    if graph['mentions']!=case['raw']['mentions']or graph['absolute_instants']or graph['numeric_depths']:failed.append('preservation')
    return {'case_id':case['case_id'],'passed':not failed,'failed':failed,'actual':observed}
