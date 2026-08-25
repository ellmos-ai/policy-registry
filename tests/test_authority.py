"""D2-R2 Stufe 1: POLICY_AUTHORITY_MODE-Schalter -- nur Schalter+Doku, kein
USMC-Umbau (T-20260825-601850637 Option C)."""

from policy_registry.authority import (
    DEFAULT_MODE,
    ENV_VAR,
    KNOWN_MODES,
    MEMORY_AND_POLICY,
    MEMORY_ONLY,
    POLICY_ONLY,
    current_mode,
    describe,
    usmc_present,
)


def test_default_mode_is_policy_only(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert current_mode() == POLICY_ONLY == DEFAULT_MODE


def test_unknown_mode_falls_back_to_default(monkeypatch):
    monkeypatch.setenv(ENV_VAR, "something-invented")
    assert current_mode() == DEFAULT_MODE


def test_known_modes_round_trip(monkeypatch):
    for mode in (POLICY_ONLY, MEMORY_ONLY, MEMORY_AND_POLICY):
        assert mode in KNOWN_MODES
        monkeypatch.setenv(ENV_VAR, mode)
        assert current_mode() == mode


def test_describe_is_always_effective_policy_only(monkeypatch):
    # Auch wenn ein zukuenftiger Modus konfiguriert ist, bleibt Stufe 1
    # wirkungslos -- "effective" ist heute IMMER policy-only.
    monkeypatch.setenv(ENV_VAR, MEMORY_AND_POLICY)
    report = describe()
    assert report["mode"] == MEMORY_AND_POLICY
    assert report["effective"] == POLICY_ONLY
    assert "usmc" in report


def test_usmc_present_is_read_only_probe():
    report = usmc_present()
    assert set(report.keys()) == {"importable", "db_path", "db_exists"}
    assert isinstance(report["importable"], bool)
    assert isinstance(report["db_exists"], bool)
