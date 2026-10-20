"""Thirty fictional scope regressions. Not corpus members or measured language data."""
from __future__ import annotations

from .context_acceptance_cases import make_case, entity, depth, time, status

FAMILIES = ('affected_vs_causal', 'repeated_updates', 'bounded_continuation',
            'observation_cues', 'plural_predicates')


def core_cases() -> list[dict]:
    result = []
    for i, language in enumerate(('english', 'tagalog', 'taglish')):
        def phrase(*values): return values[i]
        def add(family, contrast, texts, entities, facts, links, reason):
            case = make_case('v38_' + family, language, contrast, texts[i], entities,
                             facts, links, ['No unsupported target, status, role or measurement.'], reason)
            case['family'] = family
            result.append(case)
        road = 'Daan Piña'; village = 'Barangay Luntian'; dam = 'Prinsang Áraw'; school = 'Paaralang Ilaw'
        gauge = phrase('waist-deep', 'abot-baywang', 'waist-deep')
        add('affected_vs_causal', 'supported',
            (f'In {village}, houses were flooded after the spilling of {dam}. Floodwaters reached {gauge}.',
             f'Sa {village}, binaha ang mga bahay matapos ang pag-apaw ng {dam}. Umabot sa {gauge} ang baha.',
             f'Sa {village}, flooded ang houses after the spilling of {dam}. Umabot sa {gauge} ang floodwaters.'),
            [entity('v', village, 'BARANGAY'), entity('d', dam, 'LANDMARK'), entity('g', gauge, 'DEPTH')],
            [status('s', 'active'), depth('f', 'g')], [('s', ['v'], 'local'), ('f', ['v'], 'local')],
            'A causal facility is not the affected area; the next bounded water measurement retains the affected area.')
        add('affected_vs_causal', 'counterexample',
            (f'{dam} was flooded with {gauge} water. Families evacuated to {school}.',
             f'Binaha ang {dam} ng tubig na {gauge}. Lumikas sa {school} ang mga pamilya.',
             f'Flooded ang {dam} with {gauge} water. Evacuated sa {school} ang families.'),
            [entity('d', dam, 'LANDMARK'), entity('l', school, 'LANDMARK'), entity('g', gauge, 'DEPTH')],
            [status('s', 'active'), depth('f', 'g')], [('s', ['d'], 'local'), ('f', ['d'], 'local')],
            'An explicitly flooded facility remains eligible; an evacuation destination does not inherit its depth.')
        add('repeated_updates', 'supported',
            (f'{road} was flooded. Floodwater on {road} rose. After the floodwaters receded, traffic resumed.',
             f'Binaha ang {road}. Tumaas ang baha sa {road}. Matapos humupa ang baha, umusad ang trapiko.',
             f'Flooded ang {road}. Tumaas ang floodwater sa {road}. After the floodwaters receded, umusad ang traffic.'),
            [entity('a', road), entity('b', road, occurrence=1)],
            [status('s', 'active'), status('r', 'rising'), status('u', 'subsided')],
            [('s', ['a'], 'local'), ('r', ['b'], 'local'), ('u', ['a'], 'local')],
            'An unqualified narrative recession updates the initial supported event anchor; explicit repeated observations keep their occurrence.')
        add('repeated_updates', 'counterexample',
            (f'{road} was flooded yesterday. Today, {road} was flooded at 3 PM. It subsided at 4 PM.',
             f'Binaha ang {road} kahapon. Ngayon, binaha ang {road} noong 3 PM. Humupa ang baha noong 4 PM.',
             f'Flooded ang {road} yesterday. Today, flooded ang {road} at 3 PM. Nag-subside ang baha at 4 PM.'),
            [entity('a', road), entity('b', road, occurrence=1),
             entity('t0', phrase('yesterday', 'kahapon', 'yesterday'), 'TIME'),
             entity('t1', phrase('Today', 'Ngayon', 'Today'), 'TIME'), entity('t2', '3 PM', 'TIME'), entity('t3', '4 PM', 'TIME')],
            [status('s', 'historical'), status('n', 'active'), status('u', 'subsided'),
             time('f0', 't0', 'observation'), time('f1', 't1', 'observation'),
             time('f2', 't2', 'observation'), time('f3', 't3', 'recession')],
            [('s', ['a'], 'local'), ('n', ['b'], 'local'), ('u', ['b'], 'local'),
             ('f0', ['a'], 'local'), ('f1', ['b'], 'local'), ('f2', ['b'], 'local'), ('f3', ['b'], 'local')],
            'An explicit new-day observation resets the event anchor; first-occurrence relocation is forbidden.')
        add('bounded_continuation', 'supported',
            (f'Flooding on {road} was {gauge} near {school}. Riders pushed vehicles through the water, while others crossed the deep flood.',
             f'{gauge.capitalize()} ang baha sa {road} malapit sa {school}. Itinulak ang mga sasakyan sa tubig, habang tumawid ang iba sa malalim na baha.',
             f'{gauge} ang flooding sa {road} near {school}. Tinulak ang vehicles sa water, while others crossed the deep flood.'),
            [entity('p', road), entity('l', school, 'LANDMARK'), entity('g', phrase(gauge, gauge.capitalize(), gauge), 'DEPTH'),
             entity('d', phrase('deep', 'malalim', 'deep'), 'DEPTH', occurrence=phrase(1, 0, 1))],
            [depth('f', 'g'), depth('d2', 'd', 'unspecified'), status('s', 'active')],
            [('f', ['p'], 'local'), ('d2', ['p'], 'local'), ('s', ['p'], 'local')],
            'A nearby facility does not replace the affected road in a bounded vehicle/water continuation; no duplicate generic status.')
        add('bounded_continuation', 'counterexample',
            (f'{road} was flooded. Families evacuated to {school}. Water was {gauge} at an unidentified site.',
             f'Binaha ang {road}. Lumikas sa {school} ang mga pamilya. {gauge.capitalize()} ang tubig sa hindi tinukoy na lugar.',
             f'Flooded ang {road}. Evacuated sa {school} ang families. May {gauge} water sa site unknown.'),
            [entity('p', road), entity('l', school, 'LANDMARK'), entity('g', phrase(gauge, gauge.capitalize(), gauge), 'DEPTH')],
            [depth('f', 'g'), status('s', 'active')], [('s', ['p'], 'local')],
            'Unknown sites and evacuation destinations stop scope; surplus water words cannot supply a target.')
        morning = phrase('this morning', 'ngayong umaga', 'this morning')
        add('observation_cues', 'supported',
            (f'#FloodWatch: Situation in {village} {morning}.',
             f'#BantayBaha: Kalagayan sa {village} {morning}.',
             f'#BantayBaha: Situation sa {village} {morning}.'),
            [entity('v', village, 'BARANGAY'), entity('t', morning, 'TIME')],
            [time('ft', 't', 'observation')], [('ft', ['v'], 'local')],
            'A scoped flood-observation bulletin supports its clock, not an invented active status.')
        add('observation_cues', 'counterexample',
            (f'A rainfall report in {village} {morning}; no flood observation was supplied.',
             f'Ulat ng pag-ulan sa {village} {morning}; walang ulat ng baha.',
             f'Rainfall report sa {village} {morning}; walang flood report.'),
            [entity('v', village, 'BARANGAY'), entity('t', morning, 'TIME')],
            [time('ft', 't', 'report')], [],
            'Rain timing or missing flood reports do not establish an observed flood time or absence.')
        add('plural_predicates', 'supported',
            (f'{village} experienced {gauge} floods.', f'Nakaranas ng mga bahang {gauge} ang {village}.',
             f'Nakaranas ng {gauge} floods ang {village}.'),
            [entity('v', village, 'BARANGAY'), entity('g', gauge, 'DEPTH')],
            [depth('f', 'g'), status('s', 'active')], [('f', ['v'], 'local'), ('s', ['v'], 'local')],
            'Plural observed floods retain local status and measurement without expanding locations.')
        add('plural_predicates', 'counterexample',
            (f'{village} is prone to floods; forecasts warn of flooding tomorrow.',
             f'Bahain ang {village}; maaaring bumaha bukas.',
             f'Flood-prone ang {village}; forecast warns of flooding tomorrow.'),
            [entity('v', village, 'BARANGAY'), entity('t', phrase('tomorrow', 'bukas', 'tomorrow'), 'TIME')],
            [status('h', 'habitual'), status('f', 'forecast'), time('ft', 't', 'unspecified')], [],
            'Susceptibility and forecasts do not assert current observed flooding or an observation clock.')
    return result
