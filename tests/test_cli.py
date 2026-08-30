import json

from policy_registry.cli import main


def test_cli_init_and_unresolved_exit(tmp_path, capsys):
    path = tmp_path / "registry.json"
    assert main(["--registry", str(path), "init"]) == 0
    assert path.exists()
    assert (
        main(
            [
                "--registry",
                str(path),
                "resolve",
                "--scope",
                "system-wide",
            ]
        )
        == 2
    )
    output = capsys.readouterr().out
    assert '"automatic_authority": false' in output


def test_cli_register_from_json(tmp_path):
    path = tmp_path / "registry.json"
    entry_file = tmp_path / "entry.json"
    entry_file.write_text(
        json.dumps(
            {
                "id": "D-1",
                "kind": "decision",
                "title": "Explizite Entscheidung",
                "scope": "project",
                "owner": "LG",
                "authority": "explicit",
                "priority": 10,
                "precedence": 10,
                "version": "1",
                "privacy": "private",
                "source": {"uri": "C:/decisions/D-1.md"},
                "consumers": ["codex"],
                "status": "active",
                "adoption": "adopted",
            }
        ),
        encoding="utf-8",
    )
    assert main(["--registry", str(path), "register", str(entry_file)]) == 0
    assert main(["--registry", str(path), "get", "D-1"]) == 0


def test_cli_seed_decisions_registers_stable_location_pointers(tmp_path, capsys):
    control_center = tmp_path / "_control-center"
    (control_center / "_DECISIONS").mkdir(parents=True)
    (control_center.parent / ".AI" / "_templates" / "project-docs").mkdir(parents=True)

    path = tmp_path / "registry.json"
    assert (
        main(
            [
                "--registry",
                str(path),
                "seed-decisions",
                "--control-center-root",
                str(control_center),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["registered"] == 5

    assert main(["--registry", str(path), "search", "--scope", "decisions"]) == 0
    search_output = json.loads(capsys.readouterr().out)
    assert len(search_output) == 5


def test_cli_propose_adopt_and_mode_aware_resolve(tmp_path, capsys):
    path = tmp_path / "registry.json"
    project_root = tmp_path / "project"
    project_root.mkdir()

    assert (
        main(
            [
                "--registry",
                str(path),
                "propose-change",
                "--id",
                "change:cli",
                "--title",
                "CLI decision",
                "--scope",
                "project:cli",
                "--owner",
                "LG",
                "--session",
                "session-cli",
                "--quote",
                "Use CLI mode.",
                "--at",
                "2026-08-30T19:15:00Z",
            ]
        )
        == 0
    )
    proposed = json.loads(capsys.readouterr().out)
    assert proposed["kind"] == "decision-candidate"
    assert proposed["adoption"] == "pending"

    assert (
        main(
            [
                "--registry",
                str(path),
                "adopt",
                "change:cli",
                "--rule-id",
                "rule:cli@v1",
                "--at",
                "2026-08-30T19:16:00Z",
            ]
        )
        == 0
    )
    adopted = json.loads(capsys.readouterr().out)
    assert adopted["rule"]["id"] == "rule:cli@v1"
    assert adopted["rule"]["adoption"] == "adopted"

    assert (
        main(
            [
                "--registry",
                str(path),
                "resolve",
                "--scope",
                "project:cli",
                "--mode",
                "user-sovereign",
                "--instruction",
                "Use the current user choice.",
                "--project-root",
                str(project_root),
            ]
        )
        == 0
    )
    resolved = json.loads(capsys.readouterr().out)
    assert resolved["interaction_effective"] == "user-sovereign"
    assert resolved["selected"]["kind"] == "current-user-instruction"

