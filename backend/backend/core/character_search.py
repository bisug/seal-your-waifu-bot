import re
from typing import Iterable

DEFAULT_CHARACTER_SEARCH_FIELDS = ("id", "name", "anime")
MAX_SEARCH_TERMS = 6


def _coerce_terms(query: str) -> list[str]:
    terms = []
    seen = set()
    for term in re.split(r"\s+", query.strip()):
        term = term.strip()
        if not term:
            continue
        key = term.casefold()
        if key in seen:
            continue
        seen.add(key)
        terms.append(term)
        if len(terms) >= MAX_SEARCH_TERMS:
            break
    return terms


def _field_path(field: str, field_prefix: str) -> str:
    return f"{field_prefix}{field}" if field_prefix else field


def _regex_clause(field: str, term: str, field_prefix: str) -> dict:
    escaped = re.escape(term)
    path = _field_path(field, field_prefix)
    if field == "id":
        return {
            "$or": [
                {path: {"$regex": escaped, "$options": "i"}},
                {
                    "$expr": {
                        "$regexMatch": {
                            "input": {"$toString": {"$ifNull": [f"${path}", ""]}},
                            "regex": escaped,
                            "options": "i",
                        }
                    }
                },
            ]
        }
    return {path: {"$regex": escaped, "$options": "i"}}


def _targeted_search(query: str) -> tuple[str, tuple[str, ...]]:
    lowered = query.casefold()
    prefixes = {
        "id:": ("id",),
        "id=": ("id",),
        "anime:": ("anime",),
        "anime=": ("anime",),
        "series:": ("anime",),
        "series=": ("anime",),
        "name:": ("name",),
        "name=": ("name",),
    }
    for prefix, fields in prefixes.items():
        if lowered.startswith(prefix):
            return query[len(prefix):].strip(), fields
    if query.startswith("#") and len(query) > 1:
        return query[1:].strip(), ("id",)
    return query, DEFAULT_CHARACTER_SEARCH_FIELDS


def build_character_search_filter(
    query: str | None,
    *,
    field_prefix: str = "",
    fields: Iterable[str] | None = None,
) -> dict | None:
    """Build a case-insensitive Mongo filter for the query, or None if empty."""
    text = (query or "").strip()
    if not text:
        return None

    if fields is None:
        text, target_fields = _targeted_search(text)
    else:
        target_fields = tuple(fields)

    terms = _coerce_terms(text)
    if not terms or not target_fields:
        return None

    term_filters = []
    for term in terms:
        clauses = [_regex_clause(field, term, field_prefix) for field in target_fields]
        term_filters.append({"$or": clauses} if len(clauses) > 1 else clauses[0])

    if len(term_filters) == 1:
        return term_filters[0]
    return {"$and": term_filters}
