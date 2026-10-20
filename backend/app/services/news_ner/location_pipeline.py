"""Shared source-bound v40 → v44 location adapter; no neural inference or I/O."""
from copy import deepcopy

from .contract import validate_raw_input
from . import location_repair_v40 as v40
from . import location_repair_v44 as v44

VERSION = 'lanes-location-pipeline-v46'
LOCATION_RULES = 'lanes-location-repair-v40+v44'
LOCATION_METHOD = 'combined'


def compose(raw: dict) -> dict:
    value = {k: raw[k] for k in ('record_id', 'text', 'mentions')}
    first = v40.propose(value, LOCATION_METHOD)
    second = v44.propose({**value, 'mentions': first['effective_mentions']}, LOCATION_METHOD,
                         neural_mentions=value['mentions'])
    return {'schema': VERSION, 'record_id': raw['record_id'], 'method': LOCATION_METHOD,
            'text_sha256': second['text_sha256'], 'stage_order': [v40.VERSION, v44.VERSION],
            'neural_mentions': deepcopy(first['neural_mentions']),
            'control_mentions': deepcopy(first['effective_mentions']),
            'effective_mentions': deepcopy(second['effective_mentions']),
            'proposals': deepcopy(first['proposals'] + second['proposals']),
            'abstentions': [{'implementation': implementation, **deepcopy(a)}
                           for implementation, stage in ((v40.VERSION, first), (v44.VERSION, second))
                           for a in stage['abstentions']]}


def from_neural_mentions(raw: dict) -> dict:
    """Run only explicit location proposals and unchanged v42 matching."""
    validate_raw_input(raw)
    from .context_association_v42 import extract
    proposal = compose(raw)
    graph = extract({**raw, 'mentions': proposal['effective_mentions']})
    return {'proposal': proposal, 'graph': graph}
