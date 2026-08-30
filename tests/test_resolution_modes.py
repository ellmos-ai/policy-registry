from policy_registry import PolicyRegistry
from policy_registry.authority import (
    CHAT_AUTHORITY_ONLY,
    GOVERNANCE_BOUND,
    USER_SOVEREIGN,
)


def entry(entry_id: str, **overrides) -> dict:
    value = {
        "id": entry_id,
        "kind": "rule",
        "title": "Governed choice",
        "scope": "project:alpha",
        "owner": "LG",
        "authority": "explicit",
        "priority": 50,
        "precedence": 50,
        "version": "1",
        "hash": {"algorithm": "sha256", "value": "a" * 64},
        "valid_from": "2026-08-01",
        "privacy": "private",
        "source": {"uri": "C:/rules/governed.md"},
        "consumers": ["*"],
        "status": "active",
        "adoption": "adopted",
    }
    value.update(overrides)
    return value


def test_same_governance_candidates_are_ranked_differently_by_mode(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_rule(entry("rule:governed"))
    kwargs = {
        "scope": "project:alpha",
        "current_instruction": "Use the current chat choice.",
        "session": "session-501",
        "instruction_at": "2026-08-30T19:10:00Z",
        "project_root": tmp_path,
    }

    governed = registry.resolve(mode=GOVERNANCE_BOUND, **kwargs)
    sovereign = registry.resolve(mode=USER_SOVEREIGN, **kwargs)
    chat_only = registry.resolve(mode=CHAT_AUTHORITY_ONLY, **kwargs)

    assert [item["id"] for item in governed["candidates"]] == ["rule:governed"]
    assert sovereign["candidates"] == governed["candidates"]
    assert chat_only["candidates"] == governed["candidates"]
    assert governed["selected"]["id"] == "rule:governed"
    assert governed["change_proposal_required"] is True
    assert sovereign["selected"]["kind"] == "current-user-instruction"
    assert sovereign["reconciliation"]["required"] is True
    assert sovereign["reconciliation"]["automatic"] is False
    assert chat_only["selected"]["kind"] == "current-user-instruction"
    assert chat_only["governance_binding"] is False


def test_governance_conflict_is_not_broken_by_chat_instruction(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_many([entry("rule:a"), entry("rule:b")])

    result = registry.resolve(
        scope="project:alpha",
        mode=GOVERNANCE_BOUND,
        current_instruction="Pick A.",
        project_root=tmp_path,
    )

    assert result["status"] == "conflict"
    assert result["selected"] is None
    assert result["interaction_effective"] == GOVERNANCE_BOUND


def test_user_sovereign_keeps_conflicting_governance_as_followup_candidate(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_many([entry("rule:a"), entry("rule:b")])

    result = registry.resolve(
        scope="project:alpha",
        mode=USER_SOVEREIGN,
        current_instruction="Use the user's current choice.",
        project_root=tmp_path,
    )

    assert result["status"] == "resolved"
    assert result["selected"]["kind"] == "current-user-instruction"
    assert result["governance"]["status"] == "conflict"
    assert result["reconciliation"]["candidate_ids"] == ["rule:a", "rule:b"]


def test_chat_authority_only_does_not_fall_back_to_governance(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_rule(entry("rule:governed"))

    result = registry.resolve(
        scope="project:alpha",
        mode=CHAT_AUTHORITY_ONLY,
        project_root=tmp_path,
    )

    assert result["status"] == "missing"
    assert result["selected"] is None
    assert result["governance"]["status"] == "resolved"


def test_governance_bound_uses_chat_only_when_no_governance_exists(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")

    result = registry.resolve(
        scope="project:alpha",
        mode=GOVERNANCE_BOUND,
        current_instruction="Proceed locally.",
        project_root=tmp_path,
    )

    assert result["status"] == "resolved"
    assert result["selected"]["kind"] == "current-user-instruction"
    assert result["selected"]["binding"] == "no-governance-found"


def test_required_kind_cannot_be_satisfied_by_untyped_chat_instruction(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")

    result = registry.resolve(
        scope="project:alpha",
        mode=GOVERNANCE_BOUND,
        current_instruction="Treat this as a policy.",
        required_kind="policy",
        project_root=tmp_path,
    )

    assert result["status"] == "insufficient"
    assert result["selected"] is None


def test_project_mode_applies_when_no_session_mode_is_passed(monkeypatch, tmp_path):
    monkeypatch.delenv("POLICY_INTERACTION_MODE", raising=False)
    (tmp_path / ".policy-registry.toml").write_text(
        '[policy_registry]\ninteraction_mode = "user-sovereign"\n',
        encoding="utf-8",
    )
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_rule(entry("rule:governed"))

    result = registry.resolve(
        scope="project:alpha",
        current_instruction="Use the current choice.",
        project_root=tmp_path,
    )

    assert result["interaction_effective"] == USER_SOVEREIGN
    assert result["interaction_source"] == "project"
    assert result["selected"]["kind"] == "current-user-instruction"
