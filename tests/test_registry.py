import json

import pytest

from policy_registry import PolicyRegistry, RegistryError
from policy_registry.model import ValidationError


def entry(entry_id="P-1", **overrides):
    value = {
        "id": entry_id,
        "kind": "policy",
        "title": "Testregel",
        "summary": "Nur Metadaten.",
        "scope": "system-wide",
        "owner": "LG",
        "authority": "explicit",
        "priority": 100,
        "precedence": 100,
        "version": "1",
        "privacy": "private",
        "source": {"uri": "C:/rules/test.md", "type": "file", "canonical": True},
        "consumers": ["*"],
        "status": "active",
        "adoption": "adopted",
    }
    value.update(overrides)
    return value


def test_register_search_and_reload(tmp_path):
    path = tmp_path / "registry.json"
    registry = PolicyRegistry(path)
    registry.register(entry())
    assert registry.search("Testregel")[0]["id"] == "P-1"
    assert PolicyRegistry(path).get("P-1")["source"]["canonical"] is True


def test_duplicate_needs_replace(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register(entry())
    with pytest.raises(RegistryError):
        registry.register(entry())
    registry.register(entry(title="Neu"), replace=True)
    assert registry.get("P-1")["title"] == "Neu"


def test_full_text_fields_are_rejected(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    with pytest.raises(ValidationError):
        registry.register(entry(content="Regelvolltext"))
    with pytest.raises(ValidationError):
        registry.register(entry(source={"uri": "x", "body": "Regelvolltext"}))


def test_explicit_policy_wins_by_priority_and_precedence(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_many(
        [
            entry("low", priority=10, precedence=10),
            entry("high", priority=20, precedence=5),
        ]
    )
    result = registry.resolve(scope="system-wide")
    assert result["status"] == "resolved"
    assert result["selected"]["id"] == "high"
    assert result["fallback"] is None


def test_tie_is_conflict_and_tom_is_advisory_only(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_many([entry("A"), entry("B")])
    result = registry.resolve(scope="system-wide")
    assert result["status"] == "conflict"
    assert result["selected"] is None
    assert result["fallback"]["provider"] == "TOM-lm"
    assert result["fallback"]["automatic_authority"] is False
    assert result["fallback"]["general_policy_requires_explicit_adoption"] is True


def test_pending_policy_is_not_authority(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register(entry(adoption="pending"))
    result = registry.resolve(scope="system-wide")
    assert result["status"] == "missing"
    assert result["fallback"]["result_role"] == "evidence-or-decision-candidate"


def test_atomic_json_is_valid(tmp_path):
    path = tmp_path / "registry.json"
    PolicyRegistry(path).register(entry())
    assert json.loads(path.read_text(encoding="utf-8"))["schema"] == "ellmos.policy-registry.v1"
    assert not path.with_suffix(".json.tmp").exists()

