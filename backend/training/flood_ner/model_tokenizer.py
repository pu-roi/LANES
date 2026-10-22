"""Opt-in calamanCy boundary candidate; never changes source text or weights."""
from __future__ import annotations

import re
from typing import Any

TOKENIZER_NAME = 'lanes.tl.calamancy-address-v1'
INFIX = r'(?<=\w)[–—]-+(?=\w)'
PREFIX = r'^-'
SUFFIX = r'(?<=[A-Za-z0-9])-$'


def extend_pattern(callback: Any, extra: str) -> Any:
    """Extend the serialized trained tokenizer, rather than language Defaults."""
    pattern = getattr(getattr(callback, '__self__', None), 'pattern', None)
    if not isinstance(pattern, str):
        raise ValueError('candidate requires the pinned tokenizer regex callbacks')
    return re.compile(f'(?:{pattern})|(?:{extra})', callback.__self__.flags)


def apply_candidate(tokenizer: Any) -> None:
    tokenizer.infix_finditer = extend_pattern(tokenizer.infix_finditer, INFIX).finditer
    tokenizer.prefix_search = extend_pattern(tokenizer.prefix_search, PREFIX).search
    tokenizer.suffix_search = extend_pattern(tokenizer.suffix_search, SUFFIX).search
