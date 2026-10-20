"""Lossless relation grouping; never infers new location/event relationships."""
from copy import deepcopy

from .context_association_v42 import validate_output

LIMITATIONS = [
    'preview_only_not_verified_flood_data',
    'depth_time_and_matching_are_rules_not_learned_ner',
    'three_context_reference_holds_remain',
    'non_flood_access_omission_remains',
    'real_pure_tagalog_performance_unmeasured',
    'existing_results_are_exposed_silver_training_diagnostics',
    'no_database_history_or_map_policy_applied',
    'location_additions_and_boundary_replacements_are_rules_not_neural',
    'junction_type_family_lacks_standalone_real_correction',
]


def project(raw: dict, graph: dict) -> list[dict]:
    validate_output(raw, graph)
    mentions = {m['id']: m for m in graph['mentions']}
    facts = {f['id']: f for f in graph['facts']}
    groups: dict[tuple, dict] = {}
    for relation in graph['relations']:
        targets = sorted(relation['target_entity_ids'], key=lambda i: (mentions[i]['start'], mentions[i]['end'], i))
        evidence = sorted(relation['evidence'], key=lambda e: (e['start'], e['end'], e['text']))
        key = (tuple(targets), relation['scope'], tuple((e['start'], e['end'], e['text']) for e in evidence))
        group = groups.setdefault(key, {'target_entity_ids': targets, 'scope': relation['scope'],
            'evidence': deepcopy(evidence), 'relation_ids': [], 'depth': [], 'time': [], 'status': [], 'access': []})
        group['relation_ids'].append(relation['id'])
        fact = facts[relation['fact_id']]
        group[fact['kind']].append(deepcopy(fact))
    return list(groups.values())
