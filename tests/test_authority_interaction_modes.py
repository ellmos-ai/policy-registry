"""T-20260830-167725484: zweite Schalterachse POLICY_INTERACTION_MODE
(chat-authority-only / governance-bound / user-sovereign) -- Stufe 1: nur
benannt, kein Verhalten geaendert (docs/AUTORITAETS-MODI.md)."""

from policy_registry.authority import (
    CHAT_AUTHORITY_ONLY,
    DEFAULT_INTERACTION_MODE,
    GOVERNANCE_BOUND,
    INTERACTION_ENV_VAR,
    KNOWN_INTERACTION_MODES,
    KNOWN_MODES,
    MEMORY_AND_POLICY,
    POLICY_ONLY,
    USER_SOVEREIGN,
    current_interaction_mode,
    describe,
)


def test_default_interaction_mode_is_governance_bound(monkeypatch):
    monkeypatch.delenv(INTERACTION_ENV_VAR, raising=False)
    assert current_interaction_mode() == GOVERNANCE_BOUND == DEFAULT_INTERACTION_MODE


def test_unknown_interaction_mode_falls_back_to_default(monkeypatch):
    monkeypatch.setenv(INTERACTION_ENV_VAR, "history-guided-organisational-systemwide-aware")
    assert current_interaction_mode() == GOVERNANCE_BOUND


def test_known_interaction_modes_round_trip(monkeypatch):
    for mode in (CHAT_AUTHORITY_ONLY, GOVERNANCE_BOUND, USER_SOVEREIGN):
        assert mode in KNOWN_INTERACTION_MODES
        monkeypatch.setenv(INTERACTION_ENV_VAR, mode)
        assert current_interaction_mode() == mode


def test_axes_are_independent():
    # Die Rangfolge-Achse darf keinen Wert mit der Quellen-Achse teilen --
    # sonst wuerde ein Wert stillschweigend beide Schalter bedienen.
    assert KNOWN_INTERACTION_MODES.isdisjoint(KNOWN_MODES)


def test_describe_reports_both_axes_but_effective_stays_status_quo(monkeypatch):
    monkeypatch.setenv("POLICY_AUTHORITY_MODE", MEMORY_AND_POLICY)
    monkeypatch.setenv(INTERACTION_ENV_VAR, USER_SOVEREIGN)
    report = describe()
    assert report["mode"] == MEMORY_AND_POLICY
    assert report["effective"] == POLICY_ONLY
    assert report["interaction_mode"] == USER_SOVEREIGN
    assert report["interaction_effective"] == GOVERNANCE_BOUND
