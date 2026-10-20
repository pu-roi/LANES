"""Thirty-six fictional location expectations, separate from corpus references."""
from .location_repair_cases_v40 import mention
from .location_repair_v44 import FAMILIES, object_text_sha


def location_cases() -> list[dict]:
    cases = []
    for language in ('english', 'tagalog', 'taglish'):
        for family in FAMILIES:
            for supported in (True, False):
                for variant in (0, 1):
                    a, b = ('Piña Áster', 'Luntian Street') if variant == 0 else ('Dalisay', 'Mabini Road')
                    separator = {'english': ' cor. ', 'tagalog': ' kanto ng ', 'taglish': ' corner '}[language]
                    tail = {'english': ' - 8 inches, gutter deep at 6 PM',
                            'tagalog': ' - 8 pulgada, abot-sakong nang 6 PM',
                            'taglish': ' - 8 inches, gutter deep at 6 PM'}[language]
                    text = '🌧 '+a+separator+b+tail
                    changes = []
                    if family == 'missing_junction':
                        originals = [mention(text, b, 'ROAD')]
                        changes = [(text.index(a), text.index(a)+len(a), 'ROAD')]
                        if not supported:
                            if variant == 0:
                                text = '🌧 '+a+' company'+separator+b+tail
                                originals = [mention(text, b, 'ROAD')]
                            else:
                                text = 'QX'+separator+'17 Dalisay'+tail
                                originals = []
                            changes = []
                    elif family == 'boundary_replacement':
                        phrase = 'Áster' if variant == 0 else a+separator.rstrip()
                        originals = [mention(text, phrase, 'ROAD'), mention(text, b, 'ROAD', identity='n1')]
                        changes = [(text.index(a), text.index(a)+len(a), 'ROAD')]
                        if not supported:
                            if variant == 0:
                                originals = [mention(text, 'Piña', 'ROAD'), mention(text, 'Áster', 'ROAD', identity='n1'),
                                             mention(text, b, 'ROAD', identity='n2')]
                            else:
                                text = 'Dalisay'+separator+' - 8 inches at 6 PM'
                                originals = [mention(text, 'Dalisay', 'ROAD')]
                            changes = []
                    else:
                        originals = [mention(text, a, 'CITY'), mention(text, b, 'ROAD', identity='n1')]
                        changes = [(text.index(a), text.index(a)+len(a), 'ROAD')]
                        if not supported:
                            if variant == 0:
                                text = 'Barangay '+a+separator+b+tail
                                originals = [mention(text, a, 'CITY'), mention(text, b, 'ROAD', identity='n1')]
                            else:
                                originals[0]['label'] = 'LANDMARK'
                            changes = []
                    # A repeated complete occurrence provides no permission to
                    # fill an incomplete later row. Keep the earlier identity.
                    if language == 'taglish' and family == 'missing_junction' and not supported and variant == 1:
                        text = 'Dalisay Road - 3 inches at 5 PM\n'+text
                        originals = [mention(text, 'Dalisay Road', 'ROAD')]
                    control = [(m['start'], m['end'], m['label']) for m in originals]
                    expected = list(control)
                    if supported:
                        if family != 'missing_junction': expected.remove(control[0])
                        expected.extend(changes)
                    expected.sort()
                    rid = f'fictional-v44-{len(cases)}'
                    raw = {'record_id': rid, 'text': text, 'text_sha256': object_text_sha(text),
                           'publication': None, 'mentions': originals}
                    cases.append({'case_id': f'v44-{family}-{language}-{supported}-{variant}', 'family': family,
                                  'language': language, 'supported': supported, 'variant': variant,
                                  'raw': raw, 'expected_mentions': expected})
    return cases


def result(case: dict, repair: dict) -> dict:
    expected = case['expected_mentions'] if repair['method'] in (case['family'], 'combined') else [
        (m['start'], m['end'], m['label']) for m in case['raw']['mentions']]
    actual = [(m['start'], m['end'], m['label']) for m in repair['effective_mentions']]
    return {'case_id': case['case_id'], 'family': case['family'], 'method': repair['method'],
            'passed': sorted(expected) == sorted(actual) and repair['neural_mentions'] == case['raw']['mentions']}
