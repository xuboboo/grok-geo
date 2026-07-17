"""Text normalization utilities for entity names, questions, and brand detection."""
from __future__ import annotations

import re
import unicodedata
from typing import Optional, Sequence

from .constants import COMPANY_SUFFIXES

# Punctuation pattern for entity name normalization
_PUNCT_ENTITY = re.compile(
    r'[，。！？；：、\u201c\u201d\u2018\u2019（）【】《》〈〉\[\]{}|\\/<>*~`@#$%^&*_+=]'
    r'|[,.!?;:\'"`\[\]{}]'
)

# Punctuation pattern for question normalization
_PUNCT_QUESTION = re.compile(
    r'[，。！？；：、\u201c\u201d\u2018\u2019（）【】《》\.,!?;:\'"`\[\]{}]'
)

# Fillers to strip from questions
_QUESTION_FILLERS = ("请问", "什么", "哪些", "如何", "怎么", "怎样", "吗", "呢")


def normalize_entity_name(name: str, *, strip_company_suffix: bool = True) -> str:
    if name is None:
        return ""
    text = re.sub(r'[™®©℠]', '', str(name))
    text = unicodedata.normalize('NFKC', text)
    text = text.replace('\u3000', ' ')
    text = _PUNCT_ENTITY.sub(' ', text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    if strip_company_suffix and text:
        for suffix in sorted(COMPANY_SUFFIXES, key=len, reverse=True):
            s = suffix.lower()
            if text.endswith(' ' + s):
                text = text[:-(len(s) + 1)].strip()
            elif text.endswith(s) and len(text) > len(s):
                text = text[:-len(s)].strip()
    return text


def names_conflict(a: str, b: str) -> bool:
    return normalize_entity_name(a) == normalize_entity_name(b) and bool(normalize_entity_name(a))


def normalize_question_text(text: str) -> str:
    t = unicodedata.normalize('NFKC', text or '')
    trans = str.maketrans('０１２３４５６７８９', '0123456789')
    t = t.translate(trans)
    t = t.lower()
    t = _PUNCT_QUESTION.sub('', t)
    t = re.sub(r'\s+', '', t)
    for w in _QUESTION_FILLERS:
        t = t.replace(w, '')
    return t


def contains_brand_token(text: str, brand_name: str, aliases: Optional[Sequence[str]] = None) -> bool:
    hay = normalize_entity_name(text, strip_company_suffix=False)
    needles = [normalize_entity_name(brand_name, strip_company_suffix=False)]
    for a in aliases or []:
        needles.append(normalize_entity_name(a, strip_company_suffix=False))
    for n in needles:
        if n and n in hay:
            return True
    return False