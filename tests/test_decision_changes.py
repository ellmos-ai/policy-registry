import hashlib

import pytest

from policy_registry import PolicyRegistry, RegistryError


def rule_entry(entry_id: str) -> dict:
    return {
        "id": entry_id,
        "kind": "rule",
        "title": "Previous rule",
        "scope": "project:alpha",
        "owner": "LG",
        "authority": "explicit",
        "priority": 50,
        "precedence": 50,
        "version": "1",
        "hash": {"algorithm": "sha256", "value": "a" * 64},
        "valid_from": "2026-08-01",
        "privacy": "private",
        "source": {"uri": "C:/rules/previous.md"},
        "consumers": ["*"],
        "status": "active",
        "adoption": "adopted",
    }


def propose(registry: PolicyRegistry, change_id: str = "change:alpha-mode") -> dict:
    return registry.propose_change(
        change_id=change_id,
        title="Use the alpha mode",
        scope="project:alpha",
        owner="LG",
        session="session-501",
        quote="Use alpha mode from now on.",
        captured_at="2026-08-30T18:45:00Z",
        consumers=["codex"],
        priority=80,
        precedence=70,
    )


def test_propose_change_is_pending_and_records_bounded_chat_provenance(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")

    candidate = propose(registry)

    assert candidate["kind"] == "decision-candidate"
    assert candidate["adoption"] == "pending"
    assert candidate["authority"] == "chat-proposal"
    assert candidate["source"]["session"] == "session-501"
    assert candidate["source"]["quote"] == "Use alpha mode from now on."
    assert candidate["source"]["captured_at"] == "2026-08-30T18:45:00Z"
    assert candidate["hash"] == {
        "algorithm": "sha256",
        "value": hashlib.sha256(b"Use alpha mode from now on.").hexdigest(),
    }
    assert registry.resolve(scope="project:alpha")["status"] == "missing"


def test_adopt_change_materializes_an_adopted_rule_and_marks_candidate(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    propose(registry)

    result = registry.adopt_change(
        "change:alpha-mode",
        rule_id="rule:alpha-mode@v1",
        adopted_at="2026-08-30T19:00:00Z",
    )

    stored_candidate = registry.get("change:alpha-mode")
    stored_rule = registry.get("rule:alpha-mode@v1")
    assert result["candidate"]["adoption"] == "adopted"
    assert stored_candidate["adopted_as"] == "rule:alpha-mode@v1"
    assert stored_candidate["adopted_at"] == "2026-08-30T19:00:00Z"
    assert stored_rule["kind"] == "rule"
    assert stored_rule["adoption"] == "adopted"
    assert stored_rule["valid_from"] == "2026-08-30"
    assert stored_rule["hash"] == stored_candidate["hash"]
    assert stored_rule["adopted_from"] == "change:alpha-mode"
    assert registry.resolve(scope="project:alpha")["selected"]["id"] == "rule:alpha-mode@v1"


def test_adopt_change_supersedes_predecessor_through_append_only_rule_path(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_rule(rule_entry("rule:alpha-mode@v1"))
    propose(registry, "change:alpha-mode-v2")

    registry.adopt_change(
        "change:alpha-mode-v2",
        rule_id="rule:alpha-mode@v2",
        adopted_at="2026-08-30T19:05:00Z",
        supersedes="rule:alpha-mode@v1",
    )

    predecessor = registry.get("rule:alpha-mode@v1")
    successor = registry.get("rule:alpha-mode@v2")
    assert predecessor["status"] == "superseded"
    assert predecessor["hash"]["value"] == "a" * 64
    assert predecessor["superseded_by"] == successor["id"]
    assert successor["supersedes"] == predecessor["id"]
    assert successor["hash"]["value"]
    assert successor["valid_from"] == "2026-08-30"


def test_adoption_is_explicit_one_shot_and_rejects_non_candidate(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    propose(registry)
    registry.adopt_change(
        "change:alpha-mode",
        rule_id="rule:alpha-mode@v1",
        adopted_at="2026-08-30T19:00:00Z",
    )

    with pytest.raises(RegistryError, match="bereits adoptiert"):
        registry.adopt_change(
            "change:alpha-mode",
            rule_id="rule:alpha-mode@v2",
            adopted_at="2026-08-30T19:01:00Z",
        )

    registry.register_rule(rule_entry("rule:other@v1"))
    with pytest.raises(RegistryError, match="decision-candidate"):
        registry.adopt_change(
            "rule:other@v1",
            rule_id="rule:other@v2",
            adopted_at="2026-08-30T19:02:00Z",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("session", ""),
        ("quote", ""),
        ("captured_at", "not-a-time"),
    ],
)
def test_propose_change_rejects_incomplete_provenance(tmp_path, field, value):
    registry = PolicyRegistry(tmp_path / "registry.json")
    kwargs = {
        "change_id": "change:invalid",
        "title": "Invalid",
        "scope": "project:alpha",
        "owner": "LG",
        "session": "session-501",
        "quote": "Use alpha.",
        "captured_at": "2026-08-30T18:45:00Z",
    }
    kwargs[field] = value

    with pytest.raises(RegistryError):
        registry.propose_change(**kwargs)
