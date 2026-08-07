import json

from policy_registry import PolicyRegistry
from policy_registry.adapters.sync_policies import (
    export_aggregated_view,
    import_sync_pointers,
)


def build_sync_root(tmp_path):
    root = tmp_path / "_policies"
    for name in ("library", "adoption", "sources"):
        (root / name).mkdir(parents=True)
    (root / "library" / "P-001_test.md").write_text(
        "---\n"
        "id: P-001\n"
        "title: Test-Policy\n"
        "scope: system-wide\n"
        "status: active\n"
        "created: 2026-07-28\n"
        "decided_by: LG\n"
        "canonical_text: hier\n"
        "---\n\n# Regel\n\nVolltext bleibt hier.\n",
        encoding="utf-8",
    )
    (root / "adoption" / "workstation.json").write_text(
        json.dumps(
            {
                "host": "host-a",
                "policies": {
                    "P-001": {"status": "adopted", "actors": ["codex"]}
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "sources" / "workstation.json").write_text(
        json.dumps(
            {
                "host": "host-a",
                "updated": "2026-07-28",
                "sources": [
                    {
                        "id": "rules",
                        "path": "C:/rules",
                        "kind": "folder",
                        "pipeline": "test",
                        "purpose": "Testregeln",
                        "category": "pipeline-rules",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return root


def test_import_is_pointer_only_and_export_reuses_structure(tmp_path):
    root = build_sync_root(tmp_path)
    registry = PolicyRegistry(tmp_path / "local" / "registry.json")
    imported = import_sync_pointers(registry, root, slot="workstation")
    assert len(imported) == 2
    policy = registry.get("P-001")
    assert policy["hash"]["value"]
    assert policy["source"]["uri"].endswith("P-001_test.md")
    serialized = registry.path.read_text(encoding="utf-8")
    assert "Volltext bleibt hier" not in serialized

    view = export_aggregated_view(registry, root, slot="workstation")
    assert view == root / "registry" / "workstation.json"
    assert json.loads(view.read_text(encoding="utf-8"))["authority"] == "local-policy-registry"

