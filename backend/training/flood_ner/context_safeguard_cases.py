"""48 new fictional design fixtures. Never corpus members or model predictions."""
from __future__ import annotations

import hashlib
import re

MARKER = re.compile(r'\[\[(\w+)>(\w+):([^\]]+)\]\]')
THEMES = ('organizations', 'professional_roles', 'roads_facilities', 'barangays', 'local_areas', 'shared_identifiers')
CONTRASTS = ('supported', 'counterexample', 'ambiguous', 'unicode_repeated')


def build_case(theme, language, contrast, marked):
    text, predictions, expected, references = '', [], [], []
    cursor = 0
    for match in MARKER.finditer(marked):
        text += marked[cursor:match.start()]
        old, target, literal = match.groups(); start = len(text); text += literal; end = len(text)
        predictions.append([start, end, old])
        label = None if target == 'DROP' else old if target in ('KEEP', 'ABSTAIN') else target
        expected.append({'action': 'drop' if label is None else 'keep' if label == old else 'retag',
                         'label': label, 'abstained': target == 'ABSTAIN'})
        if label is not None:
            references.append([start, end, label])
        cursor = match.end()
    text += marked[cursor:]
    assert predictions and '[[' not in text
    ambiguous = contrast == 'ambiguous'
    return {'case_id': f'constructed-{theme}-{language}-{contrast}', 'quality': 'constructed',
        'role': 'design_fixture_only_not_dataset_membership', 'theme': theme, 'language': language,
        'contrast': contrast, 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'prediction': predictions, 'expected_decisions': expected,
        'expected_entities': None if ambiguous else references,
        'allow_definitive_scoring': not ambiguous}


def core_cases():
    marked = {
    'organizations': {
      'english': [
        '[[LANDMARK>DROP:Office of Aster Safety]] reported flooding.',
        'At the building named [[LANDMARK>KEEP:Office of Aster Safety]], floodwater rose.',
        'The sign named [[CITY>ABSTAIN:Office of Aster Safety]] without specifying its use.',
        '[[CITY>DROP:Department of Peña Safety]] warned residents; [[LANDMARK>DROP:Department of Peña Safety]] reported delays.'],
      'taglish': [
        'Nagpaalala ang [[CITY>DROP:Department of Hilaga Safety]] tungkol sa flood warning.',
        'Sa building na pinangalanang [[LANDMARK>KEEP:Office of Hilaga Safety]], may heavy rainfall.',
        'Nakasulat ang [[CITY>ABSTAIN:Office of Hilaga Safety]] sa sign pero hindi malinaw ang gamit.',
        'Nagpaalala ang [[CITY>DROP:Department of Piña Safety]] tungkol sa flood warning; iniulat ng [[LANDMARK>DROP:Department of Piña Safety]] ang update.']},
    'professional_roles': {
      'english': [
        'Officer Mara Dalisay, [[CITY>DROP:PIO]], reported flooding.',
        'Floodwater covered [[ROAD>KEEP:PIO Road]].',
        'The sign displayed [[CITY>ABSTAIN:PIO]].',
        'Officer Mañó Dalisay, [[CITY>DROP:PIO]], warned residents; Captain Lúmi Dalisay, [[PROVINCE>DROP:PIO]], reported delays.'],
      'taglish': [
        'Ayon kay Officer Mara Dalisay, [[LANDMARK>DROP:PIO]], may flood warning.',
        'Binaha ang [[ROAD>KEEP:PIO Road]] matapos ang heavy rainfall.',
        'Nakalagay ang [[CITY>ABSTAIN:PIO]] sa sign habang may rescue operation.',
        'Ayon kay Officer Mañó Dalisay, [[CITY>DROP:PIO]], may flood warning; ayon kay Captain Lúmi Dalisay, [[PROVINCE>DROP:PIO]], may rescue operation.']},
    'roads_facilities': {
      'english': [
        'Floodwater reached [[ROAD>LANDMARK:Ámihan Bridge]].',
        'Floodwater covered [[ROAD>KEEP:Ámihan Bridge Service Road]].',
        'The [[ROAD>ABSTAIN:Ámihan Center]] board reported delays.',
        'At [[CITY>LANDMARK:Peña Tunnel]] and beside [[ROAD>LANDMARK:Peña Tunnel]], floodwater rose.'],
      'taglish': [
        'Binaha ang [[ROAD>LANDMARK:Amihan Bridge]] matapos ang heavy rainfall.',
        'May flood warning sa [[ROAD>KEEP:Amihan Bridge Service Road]].',
        'May status report ang [[ROAD>ABSTAIN:Amihan Center]] board.',
        'Binaha ang [[CITY>LANDMARK:Piña Tunnel]] at [[ROAD>LANDMARK:Piña Tunnel]] matapos ang heavy rainfall.']},
    'barangays': {
      'english': [
        'Floodwater entered [[CITY>BARANGAY:Barangay Sinta]].',
        'Floodwater covered [[LANDMARK>KEEP:Sinta Barangay Hall]].',
        'The project label was [[CITY>ABSTAIN:Barangay]].',
        '[[CITY>BARANGAY:Brgy. Peña-Ñ]] flooded; [[PROVINCE>BARANGAY:Brgy. Peña-Ñ]] requested help.'],
      'taglish': [
        'May flood warning sa [[CITY>BARANGAY:Barangay Sinta]].',
        'Nilinis ang [[LANDMARK>KEEP:Sinta Barangay Hall]] matapos ang heavy rainfall.',
        'Sa project label ay [[CITY>ABSTAIN:Barangay]] lamang ang nakasulat.',
        'Binaha ang [[CITY>BARANGAY:Brgy. Piña-Ñ]]; may rescue team sa [[PROVINCE>BARANGAY:Brgy. Piña-Ñ]].']},
    'local_areas': {
      'english': [
        'Water rose in [[BARANGAY>LOCAL_AREA:Purok 07-A]].',
        'Phase 2 of drainage work began near [[CITY>KEEP:Luntian City]].',
        '[[CITY>ABSTAIN:Sitio]] was written without an identifier.',
        'Water rose in [[BARANGAY>LOCAL_AREA:Sitio Piña]] and [[CITY>LOCAL_AREA:Sitio Piña]].'],
      'taglish': [
        'May baha sa [[BARANGAY>LOCAL_AREA:Purok 07-A]] ayon sa rescue team.',
        'Nagsimula ang phase 2 ng drainage work malapit sa [[CITY>KEEP:Luntian City]].',
        'Sa rescue report ay [[CITY>ABSTAIN:Sitio]] lang ang nakasulat.',
        'May baha sa [[BARANGAY>LOCAL_AREA:Sitio Piña]] at [[CITY>LOCAL_AREA:Sitio Piña]] ayon sa rescue team.']},
    'shared_identifiers': {
      'english': [
        '[[LOCAL_AREA>KEEP:Purok 04-A]] and [[CITY>LOCAL_AREA:05-B]] were flooded.',
        '[[LOCAL_AREA>KEEP:Purok 04-A]] reported 2 families needing help.',
        '[[LOCAL_AREA>KEEP:Purok 4]] and [[CITY>ABSTAIN:2]] families were affected.',
        '[[LOCAL_AREA>KEEP:Purok 03-A]], [[CITY>LOCAL_AREA:04-B]] and [[BARANGAY>LOCAL_AREA:05-C]] were flooded.'],
      'taglish': [
        'Ang [[LOCAL_AREA>KEEP:Purok 04-A]] at [[CITY>LOCAL_AREA:05-B]] ay binaha habang may rescue operation.',
        'Nag-report ng 2 pamilya ang [[LOCAL_AREA>KEEP:Purok 04-A]] para sa rescue operation.',
        'Ayon sa status report, [[LOCAL_AREA>KEEP:Purok 4]] at [[CITY>ABSTAIN:2]] pamilya ang apektado.',
        'Ang [[LOCAL_AREA>KEEP:Purok 03-A]], [[CITY>LOCAL_AREA:04-B]] at [[BARANGAY>LOCAL_AREA:05-C]] ay binaha habang may rescue operation.']},
    }
    return [build_case(theme, language, contrast, marked[theme][language][i])
            for theme in THEMES for language in ('english', 'taglish') for i, contrast in enumerate(CONTRASTS)]
