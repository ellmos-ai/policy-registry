import base64
import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import jsonschema
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from policy_registry import DelegationResolver, IssuerTrustStore, PolicyRegistry
from policy_registry.cli import main
from policy_registry.delegation import (
    CANDIDATE_SCHEMA,
    GRANT_SCHEMA,
    RESULT_SCHEMA,
    TRUST_STORE_SCHEMA,
)

AT = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def public_bytes(key):
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def b64(value):
    return base64.b64encode(value).decode("ascii")


def pin(value):
    return hashlib.sha256(value).hexdigest()


def sign_object(value, private_key, *, kind, id_field, hash_field):
    unsigned = {
        key: item
        for key, item in value.items()
        if key not in {id_field, hash_field, "signature"}
    }
    content_hash = hashlib.sha256(canonical(unsigned)).hexdigest()
    value[id_field] = ("ar-" if kind == "grant" else "decision-") + content_hash
    value[hash_field] = content_hash
    value["signature"] = b64(
        private_key.sign(f"policy-registry:{kind}:v1:{content_hash}".encode("ascii"))
    )
    return value


def registry_entry(entry_id, source_uri, source_hash, **overrides):
    entry = {
        "id": entry_id,
        "kind": "decision",
        "title": "Explicit authority source",
        "scope": "system-wide",
        "owner": "LG",
        "authority": "explicit-user-decision",
        "priority": 100,
        "precedence": 100,
        "version": "1",
        "privacy": "private",
        "source": {
            "uri": str(source_uri),
            "type": "file",
            "canonical": True,
        },
        "hash": {"algorithm": "sha256", "value": source_hash},
        "consumers": ["*"],
        "status": "active",
        "adoption": "adopted",
    }
    entry.update(overrides)
    return entry


@pytest.fixture
def signed_context(tmp_path):
    source = tmp_path / "decision.txt"
    source.write_text(
        "D-20260730-001 explicit delegated-avatar authority",
        encoding="utf-8",
    )
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    registry = PolicyRegistry(tmp_path / "registry.json")
    registry.register(registry_entry("D-20260730-001", source, source_hash))

    issuer_private = Ed25519PrivateKey.generate()
    issuer_public = public_bytes(issuer_private)
    delegate_private = Ed25519PrivateKey.generate()
    delegate_public = public_bytes(delegate_private)
    trust = {
        "schema": TRUST_STORE_SCHEMA,
        "issuers": [
            {
                "issuer_id": "owner:lukas",
                "key_id": "ed25519:20260730",
                "algorithm": "ed25519",
                "public_key": b64(issuer_public),
                "key_pin": pin(issuer_public),
            }
        ],
    }
    grant = {
        "schema": GRANT_SCHEMA,
        "receipt_id": "",
        "authority_source_id": "D-20260730-001",
        "authority_source_content_hash": source_hash,
        "registry_content_hash": hashlib.sha256(
            canonical(
                {
                    "schema": registry.load()["schema"],
                    "entries": registry.load()["entries"],
                }
            )
        ).hexdigest(),
        "issuer": {
            "id": "owner:lukas",
            "key_id": "ed25519:20260730",
            "key_pin": pin(issuer_public),
        },
        "delegate": {
            "id": "decision-avatar:primary",
            "key_id": "ed25519:avatar-1",
            "algorithm": "ed25519",
            "public_key": b64(delegate_public),
            "key_pin": pin(delegate_public),
        },
        "issued_at": "2026-07-30T10:00:00Z",
        "expires_at": "2026-07-31T10:00:00Z",
        "review_at": "2026-07-31T08:00:00Z",
        "scopes": ["project:alpha/*"],
        "action_patterns": ["deploy:artifact/*"],
        "consumers": ["codex"],
        "excluded_scopes": [],
        "excluded_actions": ["deploy:artifact/delete"],
        "minimum_confidence": 0.90,
        "receipt_content_hash": "",
        "signature_algorithm": "ed25519",
        "signature": "",
    }
    sign_object(
        grant,
        issuer_private,
        kind="grant",
        id_field="receipt_id",
        hash_field="receipt_content_hash",
    )
    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "candidate_id": "",
        "decision_type": "predicted/delegated-avatar-decision",
        "delegation_receipt_id": grant["receipt_id"],
        "delegation_content_hash": grant["receipt_content_hash"],
        "subject": {
            "id": "decision-avatar:primary",
            "key_id": "ed25519:avatar-1",
        },
        "scope": "project:alpha/release",
        "action_code": "deploy:artifact/save",
        "consumer_code": "codex",
        "confidence": 0.95,
        "reason_codes": ["evidence-consistent", "scope-match"],
        "evidence_refs": [
            {
                "evidence_id": "pe-" + "a" * 64,
                "content_hash": "b" * 64,
            }
        ],
        "provenance": {
            "provider_code": "provider:neutral",
            "avatar_id": "oid-" + "c" * 64,
            "skill_id": "oid-" + "d" * 64,
            "model_id": "oid-" + "e" * 64,
        },
        "created_at": "2026-07-30T11:00:00Z",
        "candidate_content_hash": "",
        "signature_algorithm": "ed25519",
        "signature": "",
    }
    sign_object(
        candidate,
        delegate_private,
        kind="candidate",
        id_field="candidate_id",
        hash_field="candidate_content_hash",
    )
    return {
        "registry": registry,
        "trust": trust,
        "grant": grant,
        "candidate": candidate,
        "issuer_private": issuer_private,
        "delegate_private": delegate_private,
        "source": source,
    }


def resign_grant(context, grant):
    return sign_object(
        grant,
        context["issuer_private"],
        kind="grant",
        id_field="receipt_id",
        hash_field="receipt_content_hash",
    )


def resign_candidate(context, candidate, grant=None):
    grant = grant or context["grant"]
    candidate["delegation_receipt_id"] = grant["receipt_id"]
    candidate["delegation_content_hash"] = grant["receipt_content_hash"]
    return sign_object(
        candidate,
        context["delegate_private"],
        kind="candidate",
        id_field="candidate_id",
        hash_field="candidate_content_hash",
    )


def refresh_registry_binding(context):
    grant = copy.deepcopy(context["grant"])
    data = context["registry"].load()
    grant["registry_content_hash"] = hashlib.sha256(
        canonical(
            {
                "schema": data["schema"],
                "entries": sorted(data["entries"], key=lambda item: item["id"]),
            }
        )
    ).hexdigest()
    resign_grant(context, grant)
    candidate = copy.deepcopy(context["candidate"])
    resign_candidate(context, candidate, grant)
    return grant, candidate


def resolve(context, grant=None, candidate=None, at=AT):
    resolver = DelegationResolver(
        context["registry"],
        IssuerTrustStore.from_dict(context["trust"]),
        now_provider=lambda: at,
    )
    return resolver.resolve(
        grant or context["grant"],
        candidate or context["candidate"],
    )


def test_published_json_schemas_validate_signed_contract(signed_context):
    schema_root = Path(__file__).parents[1] / "schemas"
    instances = {
        "signed-delegation-grant.v1.schema.json": signed_context["grant"],
        "delegated-avatar-decision-candidate.v2.schema.json": signed_context[
            "candidate"
        ],
        "delegation-issuer-trust.v1.schema.json": signed_context["trust"],
        "delegation-resolution.v1.schema.json": resolve(signed_context).to_dict(),
    }
    assert instances["delegation-resolution.v1.schema.json"]["schema"] == RESULT_SCHEMA

    for filename, instance in instances.items():
        schema = json.loads((schema_root / filename).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(instance)


def test_qualified_candidate_never_authorizes_while_cutover_is_false(signed_context):
    result = resolve(signed_context)
    assert result.status == "candidate-qualified"
    assert result.qualified_for_future_cutover is True
    assert result.cutover_enabled is False
    assert result.authorizes_action is False
    assert "grant-issuer-signature" in result.verified
    assert "candidate-delegate-signature" in result.verified
    assert "current-project-global-policy-context" in result.verified


def test_untrusted_self_asserted_issuer_is_rejected(signed_context):
    trust = copy.deepcopy(signed_context["trust"])
    trust["issuers"][0]["issuer_id"] = "owner:other"
    resolver = DelegationResolver(
        signed_context["registry"],
        IssuerTrustStore.from_dict(trust),
    )
    result = resolver.resolve(
        signed_context["grant"],
        signed_context["candidate"],
        at=AT,
    )
    assert result.status == "rejected"
    assert "not trusted" in result.reasons[0]
    assert result.authorizes_action is False


@pytest.mark.parametrize(
    ("target", "field", "value", "expected"),
    [
        ("grant", "minimum_confidence", 0.85, "canonical content"),
        ("candidate", "confidence", 0.99, "canonical content"),
        ("candidate", "signature", "A" * 88, "signature"),
    ],
)
def test_tampering_is_rejected(signed_context, target, field, value, expected):
    grant = copy.deepcopy(signed_context["grant"])
    candidate = copy.deepcopy(signed_context["candidate"])
    (grant if target == "grant" else candidate)[field] = value
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert expected in result.reasons[0]
    assert result.authorizes_action is False


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("expires_at", "2026-07-30T11:30:00Z", "expired"),
        ("review_at", "2026-07-30T11:30:00Z", "requires current review"),
    ],
)
def test_expired_or_review_due_grant_is_rejected(
    signed_context,
    field,
    value,
    expected,
):
    grant = copy.deepcopy(signed_context["grant"])
    grant[field] = value
    resign_grant(signed_context, grant)
    candidate = copy.deepcopy(signed_context["candidate"])
    resign_candidate(signed_context, candidate, grant)
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert expected in result.reasons[0]


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("scope", "project:beta/release", "scope is outside"),
        ("action_code", "publish:public/release", "action is outside"),
        ("action_code", "deploy:artifact/delete", "explicitly excluded"),
        ("consumer_code", "other-agent", "consumer is outside"),
        ("confidence", 0.89, "below the signed threshold"),
    ],
)
def test_scope_action_exclusion_and_confidence_fail_closed(
    signed_context,
    field,
    value,
    expected,
):
    candidate = copy.deepcopy(signed_context["candidate"])
    candidate[field] = value
    resign_candidate(signed_context, candidate)
    result = resolve(signed_context, candidate=candidate)
    assert result.status == "rejected"
    assert expected in result.reasons[0]


@pytest.mark.parametrize(
    "global_scope",
    [
        "all/*",
        "all/automation",
        "global/*",
        "global/automation",
        "system-wide/*",
        "system-wide/automation",
    ],
)
def test_global_scope_namespaces_are_rejected_in_signed_grant(
    signed_context,
    global_scope,
):
    grant = copy.deepcopy(signed_context["grant"])
    grant["scopes"] = [global_scope]
    resign_grant(signed_context, grant)
    candidate = copy.deepcopy(signed_context["candidate"])
    candidate["scope"] = global_scope.removesuffix("/*") + "/release"
    resign_candidate(signed_context, candidate, grant)

    result = resolve(signed_context, grant=grant, candidate=candidate)

    assert result.status == "rejected"
    assert result.authorizes_action is False
    assert "global wildcard is forbidden" in result.reasons[0]


@pytest.mark.parametrize(
    "global_scope",
    ["all/automation", "global/automation", "system-wide/automation"],
)
def test_global_scope_namespaces_are_rejected_in_candidate(
    signed_context,
    global_scope,
):
    candidate = copy.deepcopy(signed_context["candidate"])
    candidate["scope"] = global_scope
    resign_candidate(signed_context, candidate)

    result = resolve(signed_context, candidate=candidate)

    assert result.status == "rejected"
    assert result.authorizes_action is False
    assert "global blank-scope delegation is forbidden" in result.reasons[0]


def test_registry_snapshot_is_loaded_once_for_hash_and_policy_context(signed_context):
    source = signed_context["source"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    signed_context["registry"].register(
        registry_entry(
            "D-PROJECT-DENY",
            source,
            source_hash,
            title="Current project deny",
            scope="project:alpha/release",
            effect="deny",
            action_patterns=["deploy:artifact/*"],
        )
    )
    grant, candidate = refresh_registry_binding(signed_context)
    signed_snapshot = signed_context["registry"].load()
    later_snapshot = copy.deepcopy(signed_snapshot)
    later_snapshot["entries"] = [
        entry
        for entry in later_snapshot["entries"]
        if entry["id"] != "D-PROJECT-DENY"
    ]

    class SequencedRegistry(PolicyRegistry):
        def __init__(self):
            super().__init__("unused-registry.json")
            self.loads = 0

        def load(self):
            self.loads += 1
            selected = signed_snapshot if self.loads == 1 else later_snapshot
            return copy.deepcopy(selected)

    registry = SequencedRegistry()
    result = DelegationResolver(
        registry,
        IssuerTrustStore.from_dict(signed_context["trust"]),
        now_provider=lambda: AT,
    ).resolve(grant, candidate)

    assert registry.loads == 1
    assert result.status == "rejected"
    assert result.policy_resolution["status"] == "denied"


def test_hard_confidence_floor_cannot_be_lowered_by_issuer(signed_context):
    grant = copy.deepcopy(signed_context["grant"])
    grant["minimum_confidence"] = 0.70
    resign_grant(signed_context, grant)
    candidate = copy.deepcopy(signed_context["candidate"])
    resign_candidate(signed_context, candidate, grant)
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert "hard floor" in result.reasons[0]


def test_current_explicit_project_deny_has_higher_authority(signed_context):
    source = signed_context["source"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    signed_context["registry"].register(
        registry_entry(
            "D-PROJECT-DENY",
            source,
            source_hash,
            title="Current project deny",
            scope="project:alpha/release",
            effect="deny",
            action_patterns=["deploy:artifact/*"],
        )
    )
    grant, candidate = refresh_registry_binding(signed_context)
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert result.policy_resolution["status"] == "denied"
    assert result.policy_resolution["selected"] == ["D-PROJECT-DENY"]


def test_parent_project_scope_is_part_of_current_conflict_context(signed_context):
    source = signed_context["source"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    signed_context["registry"].register(
        registry_entry(
            "D-PROJECT-PARENT-DENY",
            source,
            source_hash,
            title="Parent project deny",
            scope="project:alpha",
            effect="deny",
            action_patterns=["deploy:artifact/*"],
        )
    )
    grant, candidate = refresh_registry_binding(signed_context)
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert result.policy_resolution["selected"] == ["D-PROJECT-PARENT-DENY"]


def test_project_explicit_allow_precedes_global_explicit_deny(signed_context):
    source = signed_context["source"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    signed_context["registry"].register_many(
        [
            registry_entry(
                "D-GLOBAL-DENY",
                source,
                source_hash,
                title="Older global deny",
                effect="deny",
                action_patterns=["deploy:artifact/*"],
            ),
            registry_entry(
                "D-PROJECT-ALLOW",
                source,
                source_hash,
                title="Current project allow",
                scope="project:alpha/release",
                effect="allow",
                action_patterns=["deploy:artifact/*"],
            ),
        ]
    )
    grant, candidate = refresh_registry_binding(signed_context)
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "candidate-qualified"
    assert result.policy_resolution["selected"] == ["D-PROJECT-ALLOW"]
    assert result.authorizes_action is False


def test_binding_policy_precedes_explicit_project_allow(signed_context):
    source = signed_context["source"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    signed_context["registry"].register_many(
        [
            registry_entry(
                "P-GLOBAL-BINDING-DENY",
                source,
                source_hash,
                title="Binding safety policy",
                kind="policy",
                authority="binding-policy",
                effect="deny",
                action_patterns=["deploy:artifact/*"],
            ),
            registry_entry(
                "D-PROJECT-ALLOW",
                source,
                source_hash,
                title="Project allow",
                scope="project:alpha/release",
                effect="allow",
                action_patterns=["deploy:artifact/*"],
            ),
        ]
    )
    grant, candidate = refresh_registry_binding(signed_context)
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert result.policy_resolution["status"] == "denied"
    assert result.policy_resolution["selected"] == ["P-GLOBAL-BINDING-DENY"]


def test_equal_higher_authority_conflict_is_rejected(signed_context):
    source = signed_context["source"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    signed_context["registry"].register_many(
        [
            registry_entry(
                "D-ALLOW",
                source,
                source_hash,
                scope="project:alpha/release",
                effect="allow",
                action_patterns=["deploy:artifact/*"],
            ),
            registry_entry(
                "D-DENY",
                source,
                source_hash,
                scope="project:alpha/release",
                effect="deny",
                action_patterns=["deploy:artifact/*"],
            ),
        ]
    )
    grant, candidate = refresh_registry_binding(signed_context)
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert result.policy_resolution["status"] == "conflict"


def test_applicable_policy_without_machine_conflict_metadata_blocks(
    signed_context,
):
    source = signed_context["source"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    signed_context["registry"].register(
        registry_entry(
            "P-UNMATERIALIZED",
            source,
            source_hash,
            kind="policy",
            authority="binding",
            title="Applicable but prose-only policy",
        )
    )
    grant, candidate = refresh_registry_binding(signed_context)
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert result.policy_resolution["status"] == "unresolved"
    assert result.policy_resolution["unresolved"] == ["P-UNMATERIALIZED"]


def test_registry_change_after_signed_grant_requires_new_review(signed_context):
    source = signed_context["source"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    signed_context["registry"].register(
        registry_entry(
            "D-NEW-AFTER-GRANT",
            source,
            source_hash,
            title="New current decision",
            effect="allow",
            action_patterns=["deploy:artifact/*"],
        )
    )
    result = resolve(signed_context)
    assert result.status == "rejected"
    assert "differs from the signed delegation snapshot" in result.reasons[0]
    assert result.authorizes_action is False


def test_stale_current_authority_source_is_rejected(signed_context):
    signed_context["source"].write_text("changed", encoding="utf-8")
    result = resolve(signed_context)
    assert result.status == "rejected"
    assert "stale" in result.reasons[0]


def test_stale_current_policy_source_blocks_conflict_resolution(
    signed_context,
    tmp_path,
):
    policy_source = tmp_path / "policy.txt"
    policy_source.write_text("current binding policy", encoding="utf-8")
    policy_hash = hashlib.sha256(policy_source.read_bytes()).hexdigest()
    signed_context["registry"].register(
        registry_entry(
            "P-BINDING-ALLOW",
            policy_source,
            policy_hash,
            title="Binding allow",
            kind="policy",
            authority="binding-policy",
            effect="allow",
            action_patterns=["deploy:artifact/*"],
        )
    )
    grant, candidate = refresh_registry_binding(signed_context)
    policy_source.write_text("silently changed", encoding="utf-8")
    result = resolve(signed_context, grant=grant, candidate=candidate)
    assert result.status == "rejected"
    assert result.policy_resolution["status"] == "unresolved"
    assert result.policy_resolution["unresolved"] == ["P-BINDING-ALLOW"]


@pytest.mark.parametrize("forbidden", ["raw", "content", "payload", "private_key"])
def test_raw_tom_evidence_and_secret_fields_never_authorize(
    signed_context,
    forbidden,
):
    candidate = copy.deepcopy(signed_context["candidate"])
    candidate[forbidden] = "self-asserted"
    result = resolve(signed_context, candidate=candidate)
    assert result.status == "rejected"
    assert "forbidden" in result.reasons[0]
    assert result.authorizes_action is False


def test_cli_outputs_candidate_status_without_authorization(
    signed_context,
    tmp_path,
    capsys,
):
    grant_path = tmp_path / "grant.json"
    candidate_path = tmp_path / "candidate.json"
    trust_path = tmp_path / "trust.json"
    grant_path.write_text(json.dumps(signed_context["grant"]), encoding="utf-8")
    candidate_path.write_text(
        json.dumps(signed_context["candidate"]),
        encoding="utf-8",
    )
    trust_path.write_text(json.dumps(signed_context["trust"]), encoding="utf-8")
    exit_code = main(
        [
            "--registry",
            str(signed_context["registry"].path),
            "resolve-delegation",
            "--grant",
            str(grant_path),
            "--candidate",
            str(candidate_path),
            "--trust-store",
            str(trust_path),
            "--at",
            "2026-07-30T12:00:00Z",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 4
    assert output["status"] == "historical-audit-qualified"
    assert output["evaluation_time_mode"] == "historical-audit"
    assert output["qualified_for_future_cutover"] is False
    assert output["cutover_enabled"] is False
    assert output["authorizes_action"] is False
