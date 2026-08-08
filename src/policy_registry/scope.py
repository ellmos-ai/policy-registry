"""Shared scope and consumer matching for registry and delegation resolution.

Scope entries are hierarchical strings.  The four matching relations are,
from least to most specific: a global alias, an inherited parent, a descendant
wildcard (``/*``), and the exact candidate scope.  A sibling never matches.
The matcher is deliberately metadata-only; source freshness and authority are
enforced by the callers that resolve a matching entry.
"""

from __future__ import annotations

from typing import Literal

GLOBAL_SCOPES = frozenset({"*", "all", "global", "system-wide"})
ScopeRelation = Literal["global", "parent", "wildcard", "exact"]

_RELATION_RANK: dict[ScopeRelation, int] = {
    "global": 0,
    "parent": 1,
    "wildcard": 2,
    "exact": 3,
}


def scope_match_kind(
    entry_scope: str, candidate_scope: str
) -> ScopeRelation | None:
    """Return the shared relation for an entry and requested scope.

    ``entry_scope`` without a wildcard is inherited by descendants, while a
    trailing ``/*`` applies only to descendants and not to the parent itself.
    Global aliases match every non-empty candidate scope.  Delimiter-aware
    prefixes prevent ``project:alpha`` from matching a sibling such as
    ``project:alphabet``.
    """

    if not isinstance(entry_scope, str) or not isinstance(candidate_scope, str):
        return None
    if not entry_scope or not candidate_scope:
        return None
    if entry_scope in GLOBAL_SCOPES:
        return "global"
    if entry_scope.endswith("/*"):
        prefix = entry_scope[:-1]
        if candidate_scope.startswith(prefix) and len(candidate_scope) > len(prefix):
            return "wildcard"
        return None
    if candidate_scope == entry_scope:
        return "exact"
    parent_prefix = entry_scope.rstrip("/") + "/"
    if candidate_scope.startswith(parent_prefix):
        return "parent"
    return None


def scope_matches(entry_scope: str, candidate_scope: str) -> bool:
    """Return whether an entry scope applies to the candidate scope."""

    return scope_match_kind(entry_scope, candidate_scope) is not None


def scope_precedence(entry_scope: str, candidate_scope: str) -> tuple[int, int]:
    """Return ``(relation-rank, hierarchy-depth)`` for a matching scope.

    A non-match returns ``(-1, -1)``.  Exact scope wins over a descendant
    wildcard, which wins over inherited parent scope, which wins over global
    aliases.  For the same relation, the deepest applicable hierarchy wins.
    """

    relation = scope_match_kind(entry_scope, candidate_scope)
    if relation is None:
        return (-1, -1)
    if relation == "global":
        return (_RELATION_RANK[relation], 0)
    base = entry_scope.removesuffix("/*")
    depth = sum(1 for part in base.strip("/").split("/") if part)
    return (_RELATION_RANK[relation], depth)


def consumer_matches(consumers: object, consumer: str | None) -> bool:
    """Apply the shared consumer contract used by both resolution surfaces.

    An omitted/empty query consumer means no consumer filter.  An entry with
    no consumer restriction or ``*`` is universal; otherwise an exact code is
    required.  Malformed consumer metadata fails closed.
    """

    if consumer is None or consumer == "":
        return True
    if not isinstance(consumers, list):
        return False
    return not consumers or "*" in consumers or consumer in consumers


__all__ = [
    "GLOBAL_SCOPES",
    "ScopeRelation",
    "consumer_matches",
    "scope_match_kind",
    "scope_matches",
    "scope_precedence",
]
