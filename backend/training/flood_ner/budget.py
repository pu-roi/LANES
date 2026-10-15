"""Bound one revision's candidate review and additional article admission."""
from .collection import article_key


def collection_budget(candidate_urls: list[str], baseline_urls: list[str], admitted_urls: list[str], *,
                      candidate_limit: int = 300, article_limit: int = 200) -> dict:
    if type(candidate_limit) is not int or type(article_limit) is not int or min(candidate_limit, article_limit) < 1:
        raise ValueError('positive collection limits required')
    if any(not isinstance(values, list) or any(not isinstance(url, str) for url in values)
           for values in (candidate_urls, baseline_urls, admitted_urls)):
        raise ValueError('budget URLs must be JSON arrays of strings')
    baseline = {article_key(url) for url in baseline_urls}
    candidates = {article_key(url) for url in candidate_urls} - baseline
    admitted = {article_key(url) for url in admitted_urls} - baseline
    if len(candidates) > candidate_limit or len(admitted) > article_limit:
        raise ValueError('revision collection budget exceeded; retain quotas and report infeasibility')
    if not admitted <= candidates:
        raise ValueError('additional admitted articles must bind to reviewed candidate URLs')
    return {'schema_version': 'lanes-flood-ner-collection-budget-v1', 'candidate_limit': candidate_limit,
            'article_limit': article_limit, 'additional_candidate_urls': len(candidates),
            'additional_admitted_articles': len(admitted), 'baseline_article_keys': sorted(baseline),
            'candidate_article_keys': sorted(candidates), 'admitted_article_keys': sorted(admitted)}
