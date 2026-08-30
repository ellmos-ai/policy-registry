"""Authority interaction modes and project/session precedence (W501)."""

from policy_registry.authority import (
    CHAT_AUTHORITY_ONLY,
    DEFAULT_INTERACTION_MODE,
    GOVERNANCE_BOUND,
    INTERACTION_ENV_VAR,
    USER_SOVEREIGN,
    current_interaction_mode,
    describe,
    resolve_interaction_mode,
)


def test_default_interaction_mode_is_governance_bound(monkeypatch, tmp_path):
    monkeypatch.delenv(INTERACTION_ENV_VAR, raising=False)
    assert current_interaction_mode(project_root=tmp_path) == GOVERNANCE_BOUND
    assert DEFAULT_INTERACTION_MODE == GOVERNANCE_BOUND


def test_project_mode_is_loaded_from_project_root(monkeypatch, tmp_path):
    monkeypatch.delenv(INTERACTION_ENV_VAR, raising=False)
    (tmp_path / ".policy-registry.toml").write_text(
        '[policy_registry]\ninteraction_mode = "user-sovereign"\n',
        encoding="utf-8",
    )

    report = resolve_interaction_mode(project_root=tmp_path)

    assert report["mode"] == USER_SOVEREIGN
    assert report["source"] == "project"
    assert report["config_path"] == str(tmp_path / ".policy-registry.toml")


def test_session_argument_precedes_environment_and_project(monkeypatch, tmp_path):
    monkeypatch.setenv(INTERACTION_ENV_VAR, USER_SOVEREIGN)
    (tmp_path / ".policy-registry.toml").write_text(
        '[policy_registry]\ninteraction_mode = "user-sovereign"\n',
        encoding="utf-8",
    )

    report = resolve_interaction_mode(
        session_mode=CHAT_AUTHORITY_ONLY,
        project_root=tmp_path,
    )

    assert report["mode"] == CHAT_AUTHORITY_ONLY
    assert report["source"] == "session-argument"


def test_environment_session_mode_precedes_project(monkeypatch, tmp_path):
    monkeypatch.setenv(INTERACTION_ENV_VAR, GOVERNANCE_BOUND)
    (tmp_path / ".policy-registry.toml").write_text(
        '[policy_registry]\ninteraction_mode = "user-sovereign"\n',
        encoding="utf-8",
    )

    report = resolve_interaction_mode(project_root=tmp_path)

    assert report["mode"] == GOVERNANCE_BOUND
    assert report["source"] == "session-environment"


def test_invalid_session_or_project_configuration_fails_closed(monkeypatch, tmp_path):
    monkeypatch.delenv(INTERACTION_ENV_VAR, raising=False)
    (tmp_path / ".policy-registry.toml").write_text(
        '[policy_registry]\ninteraction_mode = "invented"\n',
        encoding="utf-8",
    )

    project_report = resolve_interaction_mode(project_root=tmp_path)
    session_report = resolve_interaction_mode(
        session_mode="invented",
        project_root=tmp_path,
    )

    assert project_report["mode"] == GOVERNANCE_BOUND
    assert project_report["source"] == "project-invalid-fallback"
    assert project_report["issue"]
    assert session_report["mode"] == GOVERNANCE_BOUND
    assert session_report["source"] == "session-invalid-fallback"


def test_malformed_or_ambiguous_project_configuration_fails_closed(monkeypatch, tmp_path):
    monkeypatch.delenv(INTERACTION_ENV_VAR, raising=False)
    (tmp_path / ".policy-registry.toml").write_text(
        '[policy_registry]\ninteraction_mode = "user-sovereign"\n'
        'interaction_mode = "chat-authority-only"\n',
        encoding="utf-8",
    )

    report = resolve_interaction_mode(project_root=tmp_path)

    assert report["mode"] == GOVERNANCE_BOUND
    assert report["source"] == "project-invalid-fallback"
    assert "TOML" in report["issue"]


def test_describe_reports_the_effective_interaction_mode(monkeypatch, tmp_path):
    monkeypatch.delenv(INTERACTION_ENV_VAR, raising=False)
    (tmp_path / ".policy-registry.toml").write_text(
        '[policy_registry]\ninteraction_mode = "user-sovereign"\n',
        encoding="utf-8",
    )

    report = describe(project_root=tmp_path)

    assert report["interaction_mode"] == USER_SOVEREIGN
    assert report["interaction_effective"] == USER_SOVEREIGN
    assert report["interaction_source"] == "project"
