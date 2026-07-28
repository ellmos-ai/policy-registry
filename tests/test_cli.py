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

