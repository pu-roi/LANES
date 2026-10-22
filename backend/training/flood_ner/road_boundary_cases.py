"""Twenty-four fictional contrasts; never corpus members or neural outputs."""
import hashlib
import re

MARK = re.compile(r'\[\[([^\]]+)\]\]')


def fixture(theme, language, contrast, marked, action, pieces=None, abstained=False):
    text = ''; cursor = 0; predictions = []; references = []
    for match in MARK.finditer(marked):
        text += marked[cursor:match.start()]; start = len(text); raw = match[1]; text += raw
        predictions.append([start, len(text), 'ROAD'])
        if pieces is None: references.append([start, len(text), 'ROAD'])
        else:
            for lo, hi in pieces: references.append([start + lo, start + hi, 'ROAD'])
        cursor = match.end()
    text += marked[cursor:]
    ambiguous = contrast == 'ambiguity'
    return {'case_id': f'constructed-{theme}-{language}-{contrast}', 'theme': theme, 'language': language,
        'contrast': contrast, 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'prediction': predictions, 'expected_shadow': references,
        'expected_action': action, 'expected_abstention': abstained,
        'expected_entities': None if ambiguous else references, 'allow_definitive_scoring': not ambiguous,
        'quality': 'constructed', 'role': 'design_only_not_dataset_membership'}


def core_cases():
    result = []
    for lang in ('english', 'taglish'):
        pre = 'Floodwater reached ' if lang == 'english' else 'May flood alert sa '
        tail = ' today.' if lang == 'english' else ' dahil sa heavy rain.'
        for theme, positive, counter, ambiguous, repeated, action, pieces in [
            ('terminal_descriptor', 'Aster Road Intersection', 'Junction Road', 'Aster Hilaga Intersection',
             'Peña Road Junction', 'trim', [(0, len('Aster Road'))]),
            ('traffic_direction', 'Aster Road (northbound)', 'Northbound Road', 'Aster Hilaga WB',
             'Peña Road NB/SB', 'trim', [(0, len('Aster Road'))]),
            ('explicit_crossing', 'Aster Road corner Hilaga Street', 'Aster-Hilaga Road', 'Aster Road corner Hilaga',
             'Peña Road cor. Piña Street', 'split', [(0, len('Aster Road')), (len('Aster Road corner '), len('Aster Road corner Hilaga Street'))])]:
            result.append(fixture(theme, lang, 'supported', pre + '[[' + positive + ']]' + tail, action, pieces))
            result.append(fixture(theme, lang, 'counterexample', pre + '[[' + counter + ']]' + tail, 'keep'))
            result.append(fixture(theme, lang, 'ambiguity', pre + '[[' + ambiguous + ']]' + tail, 'keep', abstained=True))
            children = [(0, len('Peña Road'))] if action == 'trim' else [
                (0, len('Peña Road')), (len('Peña Road cor. '), len(repeated))]
            result.append(fixture(theme, lang, 'unicode_repeated', '🌧 ' + pre + '[[' + repeated + ']]; [[' + repeated + ']]' + tail,
                                  action, children))
    return result
