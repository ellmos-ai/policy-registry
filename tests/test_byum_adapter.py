from __future__ import annotations

import ast
import copy
import inspect
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from policy_registry import PolicyRegistry, RegistryError
from policy_registry.adapters import byum
from policy_registry.model import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]


def pointer() -> dict[str, object]:
    return {
        "schema": "ellmos.policy-registry.byum-pointer.v1",
        "byum_protocol": "byum.decision-prediction.v2",
        "prediction_id": "DP-001",
        "decision_ref": {
            "decision_id": "D-20260826-001",
            "index_key": "D-20260826-001/E01",
            "scope": "project:controlroom",
            "source_locator": {
                "path": ".TOPICS/_control-center/_DECISIONS/TO-DECIDE-USER_4.txt",
                "block_id": "E01",
            },
            "source_sha256": "a" * 64,
        },
        "projection": {
            "uri": "C:/private/byum/decision-prediction-report.json",
            "sha256": "b" * 64,
            "status": "validated",
        },
    }


def test_valid_v2_pointer_builds_closed_non_authoritative_entry():
    entry = byum.candidate_entry(pointer())

    assert entry["id"] == f"byum-candidate:DP-001@sha256:{'b' * 64}"
    assert entry["kind"] == "decision-candidate"
    assert entry["scope"] == "project:controlroom"
    assert entry["authority"] == "advisory-pointer"
    assert entry["status"] == "active"
    assert entry["adoption"] == "pending"
    assert entry["version"] == "byum.decision-prediction.v2"
    assert entry["hash"] == {"algorithm": "sha256", "value": "b" * 64}
    assert entry["source"] == {
        "uri": "C:/private/byum/decision-prediction-report.json",
        "type": "byum-projection",
        "canonical": False,
        "origin": "build-your-users-mind",
    }
    assert entry["provenance"] == {
        "protocol": "byum.decision-prediction.v2",
        "prediction_id": "DP-001",
        "decision_ref": pointer()["decision_ref"],
        "projection_status": "validated",
    }


def test_pointer_schema_and_policy_entry_schema_accept_the_adapter_contract():
    pointer_schema = json.loads(
        (REPO_ROOT / "schemas" / "byum-decision-candidate-pointer.v1.schema.json").read_text(encoding="utf-8")
    )
    entry_schema = json.loads((REPO_ROOT / "schemas" / "policy-entry.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(pointer_schema)
    Draft202012Validator.check_schema(entry_schema)
    Draft202012Validator(pointer_schema).validate(pointer())
    Draft202012Validator(entry_schema).validate(byum.candidate_entry(pointer()))


@pytest.mark.parametrize(
    "field",
    [
        "kind",
        "adoption",
        "authority",
        "options",
        "recommendation",
        "rationale",
        "reason",
        "prompt",
        "decision_text",
        "payload",
        "secure_text_payload",
        "action_receipt",
        "execution_authorized",
    ],
)
def test_raw_private_or_authority_fields_are_rejected(field):
    value = pointer()
    value[field] = "forbidden"
    with pytest.raises(ValidationError, match="unerwartete Pointer-Felder"):
        byum.candidate_entry(value)


def test_protocol_hash_locator_and_status_fail_closed():
    wrong_protocol = pointer()
    wrong_protocol["byum_protocol"] = "byum.decision-prediction.v1"
    with pytest.raises(ValidationError, match="BYUM-Protokoll"):
        byum.candidate_entry(wrong_protocol)

    missing_locator = pointer()
    del missing_locator["decision_ref"]["source_locator"]["block_id"]  # type: ignore[index]
    with pytest.raises(ValidationError, match="source_locator"):
        byum.candidate_entry(missing_locator)

    bad_source_hash = pointer()
    bad_source_hash["decision_ref"]["source_sha256"] = "not-a-hash"  # type: ignore[index]
    with pytest.raises(ValidationError, match="source_sha256"):
        byum.candidate_entry(bad_source_hash)

    bad_projection_hash = pointer()
    bad_projection_hash["projection"]["sha256"] = "A" * 64  # type: ignore[index]
    with pytest.raises(ValidationError, match="projection.sha256"):
        byum.candidate_entry(bad_projection_hash)

    bad_status = pointer()
    bad_status["projection"]["status"] = "executed"  # type: ignore[index]
    with pytest.raises(ValidationError, match="projection.status"):
        byum.candidate_entry(bad_status)


def test_identifiers_and_projection_pointer_cannot_smuggle_text_or_remote_content():
    raw_prediction_id = pointer()
    raw_prediction_id["prediction_id"] = "DP-001 release this raw decision text"
    with pytest.raises(ValidationError, match="prediction_id"):
        byum.candidate_entry(raw_prediction_id)

    raw_decision_id = pointer()
    raw_decision_id["decision_ref"]["decision_id"] = "D-1\nraw decision"  # type: ignore[index]
    with pytest.raises(ValidationError, match="decision_ref.decision_id"):
        byum.candidate_entry(raw_decision_id)

    remote_projection = pointer()
    remote_projection["projection"]["uri"] = "https://example.invalid/private-report.json"  # type: ignore[index]
    with pytest.raises(ValidationError, match="lokaler Pointer"):
        byum.candidate_entry(remote_projection)


def test_registration_uses_only_temp_registry_and_never_resolves_as_authority(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    stored = byum.register_candidate(registry, pointer())

    assert registry.get(stored["id"]) == stored
    assert registry.search(kind="decision-candidate") == [stored]
    result = registry.resolve(scope="project:controlroom", query="DP-001")
    assert result["status"] == "missing"
    assert result["selected"] is None
    assert result["candidates"] == []
    assert result["fallback"]["automatic_authority"] is False

    tampered = copy.deepcopy(stored)
    tampered["id"] = "byum-candidate:DP-001-tampered"
    tampered["adoption"] = "adopted"
    tampered["authority"] = "explicit"
    registry.register(tampered)
    assert registry.resolve(scope="project:controlroom")["status"] == "missing"


def test_registration_is_content_addressed_and_append_only(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry.json")
    first = byum.register_candidate(registry, pointer())

    with pytest.raises(RegistryError, match="existiert bereits"):
        byum.register_candidate(registry, pointer())

    advanced = pointer()
    advanced["projection"]["sha256"] = "c" * 64  # type: ignore[index]
    advanced["projection"]["status"] = "decision-observed"  # type: ignore[index]
    second = byum.register_candidate(registry, advanced)

    assert first["id"] != second["id"]
    assert len(registry.search(kind="decision-candidate")) == 2


def test_adapter_has_no_byum_import_file_reader_or_event_parser():
    source = inspect.getsource(byum)
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not any("build_your_users_mind" in name or "decision_prediction" in name for name in imported)
    assert "json" not in imported
    assert "open(" not in source
    assert "read_text" not in source
    assert "jsonl" not in source.casefold()


def test_manifest_declares_only_an_optional_byum_pointer_seam():
    manifest = json.loads((REPO_ROOT / "ellmos-module.v2.json").read_text(encoding="utf-8"))
    assert "byum.decision-candidate.pointer" in manifest["provides"]
    assert "byum.decision-prediction" in manifest["optional"]
    seam = next(adapter for adapter in manifest["adapters"] if adapter["id"] == "byum-pointer-v1")
    assert seam["type"] == "seam"
    assert seam["target"] == "build-your-users-mind"
    assert seam["status"] == "optional"
