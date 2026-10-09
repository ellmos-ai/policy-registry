"""Native source checks stay inspectable when a local pointer cannot be read."""
import errno
import hashlib
import json
from pathlib import Path

import pytest

import policy_registry.registry as implementation
from policy_registry import PolicyRegistry
from policy_registry.cli import main


def registry_with_sources(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    sources = []
    for identifier in ["blocked", "healthy"]:
        source = tmp_path / (identifier + ".md")
        source.write_bytes(b"Canonical test source\n")
        sources.append(source)
        registry.register({
            "id": identifier, "kind": "policy", "title": identifier,
            "scope": "system-wide", "owner": "test", "authority": "explicit",
            "priority": 1, "precedence": 1, "version": "1", "privacy": "private",
            "source": {"uri": str(source), "type": "file", "canonical": True},
            "hash": {"algorithm": "sha256", "value": hashlib.sha256(source.read_bytes()).hexdigest()},
            "consumers": ["*"], "status": "active", "adoption": "adopted",
        })
    return registry, sources


@pytest.mark.parametrize("error_number", [errno.EAGAIN, errno.EACCES])
@pytest.mark.parametrize("operation", ["stat", "hash"])
def test_unreadable_source_keeps_other_checks_and_registry_unchanged(
        tmp_path, monkeypatch, error_number, operation):
    registry, (blocked, healthy) = registry_with_sources(tmp_path)
    before = registry.path.read_bytes()
    marker = "PRIVATE_PATH_OR_TOKEN_MUST_NOT_LEAK"
    if operation == "stat":
        original = Path.stat

        def failing_stat(path, *args, **kwargs):
            if path == blocked:
                raise OSError(error_number, marker, str(blocked))
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "stat", failing_stat)
    else:
        original = implementation.sha256_file

        def failing_hash(path):
            if path == blocked:
                raise OSError(error_number, marker, str(blocked))
            return original(path)

        monkeypatch.setattr(implementation, "sha256_file", failing_hash)

    result = registry.verify()
    checks = {item["id"]: item for item in result["checks"]}
    assert checks["blocked"] == {"id": "blocked", "state": "unreadable"}
    assert checks["healthy"]["state"] == "ok"
    assert checks["healthy"]["actual"] == hashlib.sha256(healthy.read_bytes()).hexdigest()
    assert result["ok"] is False
    assert result["entries"] == 2
    assert marker not in json.dumps(result)
    assert registry.path.read_bytes() == before


def test_source_disappearing_during_hash_is_missing(tmp_path, monkeypatch):
    registry, (blocked, _) = registry_with_sources(tmp_path)
    original = implementation.sha256_file

    def disappearing_hash(path):
        if path == blocked:
            raise FileNotFoundError(errno.ENOENT, "not available", str(blocked))
        return original(path)

    monkeypatch.setattr(implementation, "sha256_file", disappearing_hash)
    checks = registry.verify()
    assert checks["ok"] is False
    assert checks["checks"][0] == {"id": "blocked", "state": "missing"}
    assert checks["checks"][1]["state"] == "ok"


def test_unreadable_source_can_recover_without_metadata_rewrite(tmp_path, monkeypatch):
    registry, (blocked, _) = registry_with_sources(tmp_path)
    original = implementation.sha256_file

    def failing_hash(path):
        if path == blocked:
            raise OSError(errno.EAGAIN, "try again")
        return original(path)

    with monkeypatch.context() as patch:
        patch.setattr(implementation, "sha256_file", failing_hash)
        assert registry.verify()["ok"] is False
    assert registry.verify()["ok"] is True
    assert all(item["state"] == "ok" for item in registry.verify()["checks"])


def test_non_io_programming_failure_is_not_hidden(tmp_path, monkeypatch):
    registry, _ = registry_with_sources(tmp_path)

    def unexpected_failure(path):
        raise ValueError("invalid implementation")

    monkeypatch.setattr(implementation, "sha256_file", unexpected_failure)
    with pytest.raises(ValueError, match="invalid implementation"):
        registry.verify()


def test_cli_verify_reports_unreadable_in_json(tmp_path, monkeypatch, capsys):
    registry, (blocked, _) = registry_with_sources(tmp_path)
    original = implementation.sha256_file

    def failing_hash(path):
        if path == blocked:
            raise OSError(errno.EAGAIN, "PRIVATE_ERROR")
        return original(path)

    monkeypatch.setattr(implementation, "sha256_file", failing_hash)
    # Existing CLI verify uses JSON["ok"], unlike the resolve exit-code contract.
    assert main(["--registry", str(registry.path), "verify"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False
    assert result["checks"][0] == {"id": "blocked", "state": "unreadable"}
    assert capsys.readouterr().err == ""
