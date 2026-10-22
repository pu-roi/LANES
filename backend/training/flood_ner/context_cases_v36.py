"""Ninety-six fictional three-language behavior cases; never corpus additions."""
from __future__ import annotations

from .context_acceptance_cases import make_case, entity, depth, time, status

FAMILIES=('row_measurements','separate_depth_shared_time','shared_depth','ranges_qualifiers',
    'scope_boundaries','forecast','negation','historical_update','observation_onset','recession_clearance',
    'parallel_updates','collective_ranges','abbreviated_lists','temporal_evidence','flood_evidence','facility_scope')


def core_cases() -> list[dict]:
    cases=[]
    for language in ('english','tagalog','taglish'):
        n=('english','tagalog','taglish').index(language)
        def phrase(*values):return values[n]
        def add(family,contrast,texts,entities,facts,links,reason):
            case=make_case('v36_'+family,language,contrast,texts[n],entities,facts,links,
                ['No unsupported active status, depth, target, onset, clearance or absolute timestamp.'],reason)
            case['family']=family
            cases.append(case)
        p='Daan Rosal';q='Daan Lila';facility='Paaralang Piña'
        def locs(two=False,label='ROAD'):
            return [entity('p',p,label)]+([entity('q',q)]if two else[])
        def ds(identifier,word):return entity(identifier,word,'DEPTH')
        def ts(identifier,word,occurrence=0):return entity(identifier,word,'TIME',occurrence)
        active=status('s','active')
        gauge=phrase('knee-deep','abot-tuhod','knee-deep')
        waist=phrase('waist-deep','abot-baywang','waist-deep')
        clock=phrase('3 PM','alas-tres ng hapon','3 PM')
        later=phrase('4 PM','alas-kuwatro ng hapon','4 PM')
        add('row_measurements','supported',
            (f'🌧 Water level\n{p}: 12 cm.\n{q}: 24 cm.',f'🌧 Antas ng tubig\n{p}: 12 sentimetro.\n{q}: 24 sentimetro.',f'🌧 Water level ng baha\n{p}: 12 cm.\n{q}: 24 cm.'),
            locs(True)+[ds('d1',phrase('12 cm','12 sentimetro','12 cm')),ds('d2',phrase('24 cm','24 sentimetro','24 cm'))],
            [depth('f1','d1'),depth('f2','d2')],[('f1',['p'],'local'),('f2',['q'],'local')],
            'Source rows supply separate measurements; measurement heading does not independently assert status.')
        add('row_measurements','counterexample',
            (f'{p}: depth not measured.\n{p}: depth not measured.',f'{p}: hindi nasukat ang lalim.\n{p}: hindi nasukat ang lalim.',f'{p}: walang measured depth.\n{p}: walang measured depth.'),
            [entity('p',p),entity('q',p,occurrence=1)],[],[],
            'No measurement may be fabricated or copied across repeated occurrences.')
        add('separate_depth_shared_time','supported',
            (f'As of {clock}, {p} had {gauge} flooding and {q} had {waist} flooding.',
             f'Noong {clock}, {gauge} ang baha sa {p} at {waist} sa {q}.',
             f'As of {clock}, {gauge} ang baha sa {p} at {waist} sa {q}.'),
            locs(True)+[ds('d1',gauge),ds('d2',waist),ts('t',clock)],
            [depth('f1','d1'),depth('f2','d2'),time('ft','t','observation'),active],
            [('f1',['p'],'local'),('f2',['q'],'local'),('ft',['p','q'],'shared'),('s',['p','q'],'shared')],
            'One explicit observation clock with two different named measurements.')
        add('separate_depth_shared_time','counterexample',
            (f'At {clock}, {p} had {gauge} flooding. At {later}, {q} had {waist} flooding.',
             f'Noong {clock}, {gauge} ang baha sa {p}. Noong {later}, {waist} ang baha sa {q}.',
             f'At {clock}, {gauge} ang baha sa {p}. At {later}, {waist} ang baha sa {q}.'),
            locs(True)+[ds('d1',gauge),ds('d2',waist),ts('t1',clock),ts('t2',later)],
            [depth('f1','d1'),depth('f2','d2'),time('ft1','t1','observation'),time('ft2','t2','observation'),status('s1','active'),status('s2','active')],
            [('f1',['p'],'local'),('f2',['q'],'local'),('ft1',['p'],'local'),('ft2',['q'],'local'),('s1',['p'],'local'),('s2',['q'],'local')],
            'Separate clocks cannot be copied across observation scopes.')
        add('shared_depth','supported',
            (f'{p} and {q} both had {gauge} flooding.',f'Parehong {gauge} ang baha sa {p} at {q}.',f'Parehong may {gauge} flooding sa {p} at {q}.'),
            locs(True)+[ds('d',gauge)],[depth('f','d'),active],[('f',['p','q'],'shared'),('s',['p','q'],'shared')],
            'Both names explicitly share one gauge; do not invent a scalar.')
        add('shared_depth','counterexample',
            (f'{p} and {q} were mentioned. Water was {gauge} nearby; the site was not identified.',
             f'Nabanggit ang {p} at {q}. {gauge.capitalize()} ang tubig sa malapit; hindi tinukoy ang lugar.',
             f'Nabanggit ang {p} at {q}. May {gauge} water nearby; hindi tinukoy ang site.'),
            locs(True)+[ds('d',phrase(gauge,gauge.capitalize(),gauge))],[depth('f','d')],[],
            'Nearby/unknown site cannot be assigned to either named place.')
        upper=phrase('up to 25 cm','hindi hihigit sa 25 sentimetro','up to 25 cm')
        approximate=phrase('about knee-deep','humigit-kumulang abot-tuhod','about knee-deep')
        add('ranges_qualifiers','supported',
            (f'{p} had {upper} of floodwater. {q} had {approximate} flooding.',
             f'{upper.capitalize()} ang baha sa {p}. {approximate.capitalize()} ang baha sa {q}.',
             f'May {upper} na baha sa {p}. {approximate.capitalize()} ang baha sa {q}.'),
            locs(True)+[ds('d1',phrase(upper,upper.capitalize(),upper)),ds('d2',phrase(approximate,approximate.capitalize(),approximate.capitalize()))],
            [depth('f1','d1','maximum',['upper bound']),depth('f2','d2','point',['approximation']),status('s1','active'),status('s2','active')],
            [('f1',['p'],'local'),('f2',['q'],'local'),('s1',['p'],'local'),('s2',['q'],'local')],
            'An explicit numerical upper bound differs from approximate body gauge.')
        add('ranges_qualifiers','counterexample',
            (f'{p} had knee-deep flooding; no exact numerical depth was given.',
             f'Hanggang tuhod ang baha sa {p}; walang ibinigay na eksaktong bilang.',
             f'Hanggang tuhod ang baha sa {p}; walang exact numeric depth.'),
            locs()+[ds('d',phrase('knee-deep','Hanggang tuhod','Hanggang tuhod'))],
            [depth('f','d','point',['conventional body-level gauge']),active],[('f',['p'],'local'),('s',['p'],'local')],
            'Conventional body-level wording does not automatically impose a numerical maximum.')
        add('scope_boundaries','supported',
            (f'{p} in Bayan Verde had {gauge} flooding. {facility} was used as a shelter.',
             f'{gauge.capitalize()} ang baha sa {p} sa Bayan Verde. Ginawang silungan ang {facility}.',
             f'{gauge.capitalize()} ang baha sa {p} sa Bayan Verde. Evacuation shelter ang {facility}.'),
            locs()+[entity('c','Bayan Verde','CITY'),entity('l',facility,'LANDMARK'),ds('d',phrase(gauge,gauge.capitalize(),gauge.capitalize()))],
            [depth('f','d'),active],[('f',['p'],'local'),('s',['p'],'local')],
            'Parent place and shelter do not inherit the road depth or active status.')
        add('scope_boundaries','counterexample',
            (f'A meeting was held at {facility} near {p}. No flooding report was supplied.',
             f'Nagpulong sa {facility} malapit sa {p}. Walang ulat tungkol sa baha.',
             f'May meeting sa {facility} near {p}. Walang flood report.'),
            [entity('l',facility,'LANDMARK'),entity('p',p)],[],[],
            'A missing report is neither active flooding nor a verified dry observation.')
        tomorrow=phrase('tomorrow','bukas','tomorrow')
        add('forecast','supported',
            (f'A forecast warns {p} may have {gauge} flooding {tomorrow}.',
             f'Maaaring maging {gauge} ang baha sa {p} {tomorrow}, ayon sa babala.',
             f'May forecast na maaaring {gauge} ang baha sa {p} {tomorrow}.'),
            locs()+[ds('d',gauge),ts('t',tomorrow)],
            [depth('f','d','point',['predicted only']),time('ft','t','unspecified'),status('s','forecast')],
            [('f',['p'],'local'),('ft',['p'],'local'),('s',['p'],'local')],
            'Future forecast is not a current observation or absolute date.')
        add('forecast','counterexample',
            (f'A forecast concerns heavy rainfall {tomorrow}. {p} was only mentioned.',
             f'Maaaring lumakas ang ulan {tomorrow}. Nabanggit lamang ang {p}.',
             f'May rain forecast {tomorrow}. Nabanggit lang ang {p}.'),
            locs()+[ts('t',tomorrow)],[time('ft','t','unspecified')],[],
            'Weather forecast alone does not establish a flood target or depth.')
        add('negation','supported',
            (f'{p} is not flooded at {clock}.',f'Hindi binabaha ang {p} noong {clock}.',f'Hindi flooded ang {p} at {clock}.'),
            locs()+[ts('t',clock)],[time('ft','t','observation'),status('s','negated')],
            [('ft',['p'],'local'),('s',['p'],'local')],
            'Explicit flood negation applies to this target and clock only.')
        add('negation','counterexample',
            (f'No residents were injured, but {p} had {gauge} flooding.',
             f'Walang nasugatan, ngunit {gauge} ang baha sa {p}.',
             f'Walang injured residents, pero {gauge} ang baha sa {p}.'),
            locs()+[ds('d',gauge)],[depth('f','d'),active],[('f',['p'],'local'),('s',['p'],'local')],
            'Negated casualty is not negated flooding.')
        yesterday=phrase('Yesterday','Kahapon','Yesterday');today=phrase('Today','Ngayon','Today')
        add('historical_update','supported',
            (f'{yesterday} {p} had {gauge} flooding. {today} {p} had {waist} flooding.',
             f'{gauge.capitalize()} ang baha sa {p} {yesterday.lower()}. {waist.capitalize()} naman sa {p} {today.lower()}.',
             f'{yesterday}, {gauge} ang baha sa {p}. {today}, {waist} naman sa {p}.'),
            [entity('p',p),entity('q',p,occurrence=1),ds('d1',phrase(gauge,gauge.capitalize(),gauge)),ds('d2',phrase(waist,waist.capitalize(),waist)),ts('t1',phrase(yesterday,yesterday.lower(),yesterday)),ts('t2',phrase(today,today.lower(),today))],
            [depth('f1','d1'),depth('f2','d2'),time('ft1','t1','observation'),time('ft2','t2','observation'),status('s1','historical'),status('s2','active')],
            [('f1',['p'],'local'),('f2',['q'],'local'),('ft1',['p'],'local'),('ft2',['q'],'local'),('s1',['p'],'local'),('s2',['q'],'local')],
            'Different source occurrences retain earlier and current observations without inferred override.')
        add('historical_update','counterexample',
            (f'{yesterday} {p} had {gauge} flooding. {q} was mentioned; its current depth is unknown.',
             f'{gauge.capitalize()} ang baha sa {p} {yesterday.lower()}. Nabanggit ang {q}; hindi alam ang lalim doon ngayon.',
             f'{yesterday}, {gauge} ang baha sa {p}. Nabanggit ang {q}; unknown ang current depth doon.'),
            locs(True)+[ds('d',phrase(gauge,gauge.capitalize(),gauge)),ts('t1',phrase(yesterday,yesterday.lower(),yesterday))]+([ts('t2','ngayon')]if n==1 else[]),
            [depth('f','d'),time('ft1','t1','observation'),status('s','historical')]+([time('ft2','t2','unspecified')]if n==1 else[]),
            [('f',['p'],'local'),('ft1',['p'],'local'),('s',['p'],'local')],
            'A different merely mentioned place cannot inherit the historical gauge or current status.')
        add('observation_onset','supported',
            (f'Flooding on {p} began at {clock} and was observed at {later}.',
             f'Nagsimula ang baha sa {p} noong {clock} at naobserbahan noong {later}.',
             f'Nagsimula ang flooding sa {p} at {clock} at na-observe at {later}.'),
            locs()+[ts('t1',clock),ts('t2',later)],
            [time('ft1','t1','onset'),time('ft2','t2','observation'),active],
            [('ft1',['p'],'local'),('ft2',['p'],'local'),('s',['p'],'local')],
            'Explicit flood onset and later observation remain distinct roles.')
        add('observation_onset','counterexample',
            (f'Rain began at {clock}. {p} had {gauge} flooding at {later}.',
             f'Nagsimula ang ulan noong {clock}. {gauge.capitalize()} ang baha sa {p} noong {later}.',
             f'Nagsimula ang rain at {clock}. {gauge.capitalize()} ang baha sa {p} at {later}.'),
            locs()+[ts('t1',clock),ts('t2',later),ds('d',phrase(gauge,gauge.capitalize(),gauge.capitalize()))],
            [time('ft1','t1','unspecified'),time('ft2','t2','observation'),depth('f','d'),active],
            [('ft2',['p'],'local'),('f',['p'],'local'),('s',['p'],'local')],
            'Rain onset cannot become flood onset.')
        add('recession_clearance','supported',
            (f'As of {clock}, water on {p} was receding. At {later}, the road was explicitly dry and cleared of floodwater.',
             f'Humuhupa ang baha sa {p} noong {clock}. Noong {later}, tuyo na ang kalsada at wala nang baha.',
             f'As of {clock}, receding ang baha sa {p}. At {later}, dry at cleared of floodwater na ang kalsada.'),
            locs()+[ts('t1',clock),ts('t2',later)],
            [time('ft1','t1','recession'),time('ft2','t2','clearance'),status('s1','receding'),status('s2','cleared')],
            [('ft1',['p'],'local'),('ft2',['p'],'local'),('s1',['p'],'local'),('s2',['p'],'local')],
            'Explicit recession beats as-of observation; clearance needs its own dry/no-flood evidence.')
        add('recession_clearance','counterexample',
            (f'As of {clock}, water on {p} was receding but remained {gauge}.',
             f'Humuhupa ang baha sa {p} noong {clock}, ngunit {gauge} pa rin.',
             f'As of {clock}, receding ang baha sa {p} pero {gauge} pa rin.'),
            locs()+[ts('t',clock),ds('d',gauge)],
            [time('ft','t','recession'),depth('f','d'),status('s','receding')],
            [('ft',['p'],'local'),('f',['p'],'local'),('s',['p'],'local')],
            'Recession with residual depth never establishes clearance.')
        add('parallel_updates','supported',
            (f'{p} had {gauge} flooding at {clock}. Meanwhile, {q} had {waist} flooding at {later}.',
             f'{gauge.capitalize()} ang baha sa {p} noong {clock}. Samantala, {waist} sa {q} noong {later}.',
             f'{gauge.capitalize()} ang baha sa {p} at {clock}. Samantala, {waist} sa {q} at {later}.'),
            locs(True)+[ds('d1',phrase(gauge,gauge.capitalize(),gauge.capitalize())),ds('d2',waist),ts('t1',clock),ts('t2',later)],
            [depth('f1','d1'),depth('f2','d2'),time('ft1','t1','observation'),time('ft2','t2','observation'),status('s1','active'),status('s2','active')],
            [('f1',['p'],'local'),('f2',['q'],'local'),('ft1',['p'],'local'),('ft2',['q'],'local'),('s1',['p'],'local'),('s2',['q'],'local')],
            'Parallel omitted predicate must retain each road clock and gauge.')
        add('parallel_updates','counterexample',
            (f'{p} had {gauge} flooding. Meanwhile, water was waist-deep nearby; the site was not identified.',
             f'{gauge.capitalize()} ang baha sa {p}. Samantala, abot-baywang ang tubig sa malapit; hindi tinukoy ang lugar.',
             f'{gauge.capitalize()} ang baha sa {p}. Samantala, waist-deep water nearby; hindi tinukoy ang site.'),
            locs()+[ds('d1',phrase(gauge,gauge.capitalize(),gauge.capitalize())),ds('d2',phrase('waist-deep','abot-baywang','waist-deep'))],
            [depth('f1','d1'),depth('f2','d2'),active],[('f1',['p'],'local'),('s',['p'],'local')],
            'Parallel form does not resolve an explicitly unknown nearby target.')
        ranged=phrase('10 to 20 cm','sampu hanggang dalawampung sentimetro','10 to 20 cm')
        add('collective_ranges','supported',
            (f'Flood depths across {p} and {q} ranged from {ranged}.',
             f'{ranged.capitalize()} ang lalim ng baha sa mga sumusunod: {p} at {q}.',
             f'Collective flood depth sa {p} at {q}: {ranged}.'),
            locs(True)+[ds('d',phrase(ranged,ranged.capitalize(),ranged))],
            [depth('f','d','range',['not an individual scalar']),active],
            [('f',['p','q'],'collective'),('s',['p','q'],'shared')],
            'One explicit source-listed range stays grouped and preserves its endpoints.')
        add('collective_ranges','counterexample',
            (f'{p} and {q} were mentioned. One had {ranged} of water; the report did not identify which.',
             f'Nabanggit ang {p} at {q}. May {ranged} na tubig sa isa; hindi tinukoy kung alin.',
             f'Nabanggit ang {p} at {q}. May {ranged} water sa isa; unknown kung alin.'),
            locs(True)+[ds('d',ranged)],[depth('f','d','range')],[],
            'Unknown target prevents collective or per-road assignment.')
        access={'id':'fa','kind':'access','value':'light_vehicle_closed'}
        names=['Rosal St.','P. Lila Ave.','Purok Piña']
        add('abbreviated_lists','supported',
            (f'{names[0]}, {names[1]}, and {names[2]} were not passable to light vehicles.',
             f'Hindi madaanan ng maliliit na sasakyan ang {names[0]}, {names[1]}, at {names[2]}.',
             f'Not passable sa light vehicles ang {names[0]}, {names[1]}, at {names[2]}.'),
            [entity('p',names[0]),entity('q',names[1]),entity('l',names[2],'LOCAL_AREA')],
            [access],[('fa',['p','q','l'],'shared')],
            'Abbreviations and LOCAL_AREA remain a complete bounded shared-access list.')
        add('abbreviated_lists','counterexample',
            (f'{names[0]}, {names[1]}, and an unnamed road were not passable to light vehicles.',
             f'Hindi madaanan ng maliliit na sasakyan ang {names[0]}, {names[1]}, at isang hindi pinangalanang kalsada.',
             f'Not passable sa light vehicles ang {names[0]}, {names[1]}, at isang unnamed road.'),
            [entity('p',names[0]),entity('q',names[1])],[access],[],
            'An explicitly incomplete target set cannot become a complete shared assertion.')
        duration=phrase('two hours','dalawang oras','two hours');day=phrase('Tuesday','Martes','Tuesday')
        add('temporal_evidence','supported',
            (f'{p} had {gauge} flooding at {clock}.',f'{gauge.capitalize()} ang baha sa {p} noong {clock}.',f'{gauge.capitalize()} ang baha sa {p} at {clock}.'),
            locs()+[ds('d',phrase(gauge,gauge.capitalize(),gauge.capitalize())),ts('t',clock)],
            [depth('f','d'),time('ft','t','observation'),active],[('f',['p'],'local'),('ft',['p'],'local'),('s',['p'],'local')],
            'Only a supported event observation clock receives observation role.')
        add('temporal_evidence','counterexample',
            (f'A report on {day} said {p} had {gauge} flooding for {duration}.',
             f'Ayon sa ulat noong {day}, {gauge} ang baha sa {p} sa loob ng {duration}.',
             f'Ayon sa report nitong {day}, {gauge} ang baha sa {p} for {duration}.'),
            locs()+[ds('d',gauge),ts('t1',day),ts('t2',duration)],
            [depth('f','d'),time('ft1','t1','report'),time('ft2','t2','unspecified'),active],
            [('f',['p'],'local'),('s',['p'],'local')],
            'Report date and duration are recognized separately, not inferred onset or observation clocks.')
        add('flood_evidence','supported',
            (f'{p} was flooded. No residents were injured.',f'Binabaha ang {p}. Walang nasugatan.',f'Flooded ang {p}. Walang injured residents.'),
            locs(),[active],[('s',['p'],'local')],'Explicit flood state survives unrelated injury negation.')
        add('flood_evidence','counterexample',
            (f'Residents from {p} were evacuated because the area is flood-prone.',
             f'Lumikas ang mga residente mula sa {p} dahil bahain ang lugar.',
             f'Evacuated ang residents mula sa {p} dahil flood-prone ang area.'),
            locs(),[status('s','habitual')],[],
            'Susceptibility/evacuation alone does not establish active flooding at the place.')
        add('facility_scope','supported',
            (f'{facility} was flooded with {gauge} water.',f'Binabaha ang {facility} ng {gauge} na tubig.',f'Flooded ang {facility} ng {gauge} na tubig.'),
            [entity('l',facility,'LANDMARK'),ds('d',gauge)],[depth('f','d'),active],
            [('f',['l'],'local'),('s',['l'],'local')],'A facility with its own flooding evidence remains a valid target.')
        add('facility_scope','counterexample',
            (f'{p} had {gauge} flooding. People waded through floodwater on the road where {facility} is located.',
             f'{gauge.capitalize()} ang baha sa {p}. Naglakad sa baha ang mga tao sa kalsada kung saan matatagpuan ang {facility}.',
             f'{gauge.capitalize()} ang baha sa {p}. Dumaan sa floodwater sa kalsada kung saan located ang {facility}.'),
            locs()+[entity('l',facility,'LANDMARK'),ds('d',phrase(gauge,gauge.capitalize(),gauge.capitalize()))],
            [depth('f','d'),active],[('f',['p'],'local'),('s',['p'],'local')],
            'Nearby building location is road context, not proof the building itself flooded.')
    return cases
