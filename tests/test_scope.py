import pytest

from policy_registry.scope import (
    consumer_matches,
    scope_match_kind,
    scope_matches,
    scope_precedence,
)


@pytest.mark.parametrize(
    ("entry_scope", "candidate_scope", "relation"),
    [
        ("system-wide", "project:alpha/release", "global"),
        ("project:alpha", "project:alpha/release", "parent"),
        ("project:alpha/*", "project:alpha/release", "wildcard"),
        ("project:alpha/release", "project:alpha/release", "exact"),
        ("project:alpha", "project:alphabet/release", None),
        ("project:alpha/*", "project:alpha", None),
        ("project:alpha/release", "project:alpha/other", None),
    ],
)
def test_scope_matcher_has_explicit_relations(
    entry_scope, candidate_scope, relation
):
    assert scope_match_kind(entry_scope, candidate_scope) == relation
    assert scope_matches(entry_scope, candidate_scope) is (relation is not None)


def test_scope_precedence_is_exact_then_wildcard_then_parent_then_global():
    candidate = "project:alpha/release"
    assert scope_precedence("system-wide", candidate) == (0, 0)
    assert scope_precedence("project:alpha", candidate) == (1, 1)
    assert scope_precedence("project:alpha/*", candidate) == (2, 1)
    assert scope_precedence(candidate, candidate) == (3, 2)
    assert scope_precedence("project:beta", candidate) == (-1, -1)


@pytest.mark.parametrize(
    ("consumers", "consumer", "matches"),
    [
        ([], "codex", True),
        (["*"], "codex", True),
        (["codex"], "codex", True),
        (["gemini"], "codex", False),
        (["codex"], None, True),
    ],
)
def test_consumer_matching_is_shared_and_fail_closed_for_restricted_codes(
    consumers, consumer, matches
):
    assert consumer_matches(consumers, consumer) is matches
