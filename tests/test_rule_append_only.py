"""D2-R2 Stufe 1 (T-20260825-601850637 Option C): Audit-Pflichtfelder für
kind=rule + Append-only-/Supersede-Mechanismus (session-checkpoint-ADR-Muster:
immutable rows, kein Ueberschreiben, Supersession statt Loeschung)."""

import pytest

from policy_registry import PolicyRegistry, RegistryError

VALID_HASH = {"algorithm": "sha256", "value": "a" * 64}


def rule_entry(entry_id="rule:test", **overrides):
    value = {
        "id": entry_id,
        "kind": "rule",
        "title": "Testregel",
        "summary": "Nur Metadaten.",
        "scope": "system-wide",
        "owner": "LG",
        "authority": "explicit",
        "priority": 100,
        "precedence": 100,
        "version": "1",
        "hash": dict(VALID_HASH),
        "valid_from": "2026-08-25",
        "privacy": "private",
        "source": {"uri": "C:/rules/test.md", "type": "file", "canonical": True},
        "consumers": ["*"],
        "status": "active",
        "adoption": "adopted",
    }
    value.update(overrides)
    return value


def test_register_rule_requires_hash_and_valid_from(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    with pytest.raises(RegistryError):
        registry.register_rule(rule_entry(hash=None))
    with pytest.raises(RegistryError):
        registry.register_rule(rule_entry(valid_from=None))


def test_plain_register_of_kind_rule_still_works_without_audit_fields(tmp_path):
    """Bestehende leichte kind=rule-Pointer (z.B. decisions.py
    'project-local-convention') wurden nie fuer diese Audit-Disziplin gebaut
    und duerfen durch Stufe 1 nicht rueckwirkend brechen -- die Pflicht gilt
    NUR fuer den neuen Append-only-Weg (register_rule()), nicht fuer das
    bestehende register()/register_many()."""
    registry = PolicyRegistry(tmp_path / "registry.json")
    entry = rule_entry("rule:legacy-pointer")
    del entry["hash"]
    del entry["valid_from"]
    registered = registry.register(entry)
    assert registered["kind"] == "rule"


def test_policy_kind_unaffected_by_rule_audit_requirement(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    entry = rule_entry(kind="policy")
    del entry["hash"]
    del entry["valid_from"]
    # kind=policy hat weiterhin KEINE strukturelle Pflicht fuer hash/valid_from
    # (Stufe 1 aendert nur kind=rule) -- register() darf hier nicht scheitern.
    registered = registry.register(entry)
    assert registered["kind"] == "policy"


def test_register_rule_is_append_only(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_rule(rule_entry())
    with pytest.raises(RegistryError):
        registry.register_rule(rule_entry())  # gleiche id -> kein Ueberschreiben


def test_register_rule_rejects_non_rule_kind(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    with pytest.raises(RegistryError):
        registry.register_rule(rule_entry(kind="policy"))


def test_register_rule_supersede_keeps_old_row_content_intact(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    v1 = registry.register_rule(rule_entry("rule:test@v1", title="Erste Fassung"))
    v2 = registry.register_rule(
        rule_entry("rule:test@v2", title="Zweite Fassung", version="2"),
        supersedes="rule:test@v1",
    )

    stored_v1 = registry.get("rule:test@v1")
    stored_v2 = registry.get("rule:test@v2")

    # Alte Zeile bleibt inhaltlich unveraendert (Titel/hash/version identisch
    # zum Registrierungszeitpunkt) -- nur status/superseded_by kommen dazu.
    assert stored_v1["title"] == "Erste Fassung"
    assert stored_v1["hash"] == v1["hash"]
    assert stored_v1["version"] == "1"
    assert stored_v1["status"] == "superseded"
    assert stored_v1["superseded_by"] == "rule:test@v2"

    assert stored_v2["title"] == "Zweite Fassung"
    assert stored_v2["status"] == "active"
    assert stored_v2["supersedes"] == "rule:test@v1"
    assert v2["id"] == "rule:test@v2"


def test_register_rule_unknown_supersedes_target_fails(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    with pytest.raises(RegistryError):
        registry.register_rule(rule_entry(), supersedes="rule:does-not-exist")


def test_register_rule_double_supersede_chain_breaks(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_rule(rule_entry("rule:test@v1"))
    registry.register_rule(rule_entry("rule:test@v2", version="2"), supersedes="rule:test@v1")
    with pytest.raises(RegistryError):
        # v1 ist schon superseded -- ein zweiter Supersede-Versuch auf
        # dieselbe alte Zeile ist kein gueltiger Kettenschritt.
        registry.register_rule(rule_entry("rule:test@v3", version="3"), supersedes="rule:test@v1")


def test_resolve_only_returns_current_rule_version(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register_rule(rule_entry("rule:test@v1", scope="ai"))
    registry.register_rule(
        rule_entry("rule:test@v2", scope="ai", version="2"), supersedes="rule:test@v1"
    )
    result = registry.resolve(scope="ai", consumer="claude-code")
    assert result["status"] == "resolved"
    assert result["selected"]["id"] == "rule:test@v2"
    ids = [e["id"] for e in result["candidates"]]
    assert "rule:test@v2" in ids
    assert "rule:test@v1" not in ids
