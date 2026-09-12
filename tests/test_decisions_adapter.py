import json
from pathlib import Path

from policy_registry import PolicyRegistry
from policy_registry.adapters.decisions import (
    LOCATIONS_SCOPE,
    location_entries,
    register_decision_locations,
)


def build_control_center_root(tmp_path):
    """Mirror the real _control-center layout that the adapter derives paths from."""
    root = tmp_path / "_control-center"
    decisions = root / "_DECISIONS"
    decisions.mkdir(parents=True)
    (decisions / "TO-DECIDE-USER.txt").write_text(
        "Reale Entscheidungskette -- Volltext bleibt hier, nicht in der Registry.\n",
        encoding="utf-8",
    )
    (decisions / "DECIDED-AND-DONE.md").write_text(
        "# Umgesetzte Entscheidungen\n\nEcht getroffene Entscheidung, Volltext hier.\n",
        encoding="utf-8",
    )
    tools = decisions / "_tools"
    tools.mkdir()
    (tools / "decisions.index.json").write_text("{}\n", encoding="utf-8")

    templates = root.parent / ".AI" / "_templates" / "project-docs"
    templates.mkdir(parents=True)
    (templates / "DECISIONS.md").write_text(
        "# DECISIONS.md -- ADR-Vorlage\n", encoding="utf-8"
    )
    return root


def test_location_entries_are_pointer_only_and_stable_in_count(tmp_path):
    root = build_control_center_root(tmp_path)
    entries = location_entries(root, curated_on="2026-08-24")
    assert len(entries) == 5
    ids = {entry["id"] for entry in entries}
    assert ids == {
        "decision-location:chain-head",
        "decision-location:host-file-pattern",
        "decision-location:decided-and-done",
        "decision-location:machine-index",
        "decision-location:project-local-convention",
    }
    for entry in entries:
        assert entry["scope"] == LOCATIONS_SCOPE
        assert entry["version"] == "2026-08-24"
        assert set(entry["source"].keys()) & {"content", "body", "full_text", "payload"} == set()

    kinds = {entry["id"]: entry["kind"] for entry in entries}
    assert kinds["decision-location:chain-head"] == "decision"
    assert kinds["decision-location:host-file-pattern"] == "decision"
    assert kinds["decision-location:decided-and-done"] == "decision"
    assert kinds["decision-location:machine-index"] == "evidence"
    assert kinds["decision-location:project-local-convention"] == "rule"


def test_register_decision_locations_stores_no_decision_text(tmp_path):
    root = build_control_center_root(tmp_path)
    registry = PolicyRegistry(tmp_path / "local" / "registry.json")

    registered = register_decision_locations(registry, root, curated_on="2026-08-24")
    assert len(registered) == 5

    chain_head = registry.get("decision-location:chain-head")
    assert chain_head["source"]["uri"].endswith("TO-DECIDE-USER.txt")

    machine_index = registry.get("decision-location:machine-index")
    assert machine_index["source"]["uri"].endswith(
        str(Path("_DECISIONS") / "_tools" / "decisions.index.json")
    )

    serialized = registry.path.read_text(encoding="utf-8")
    assert "Reale Entscheidungskette" not in serialized
    assert "Echt getroffene Entscheidung" not in serialized

    # host-file-pattern points at the directory, not a specific host file
    host_pattern = registry.get("decision-location:host-file-pattern")
    assert host_pattern["source"]["uri"].endswith("_DECISIONS")
    assert host_pattern["source"]["pattern"] == "TO-DECIDE-USER-<HOST>.txt"


def test_register_decision_locations_is_scoped_for_broad_and_narrow_queries(tmp_path):
    root = build_control_center_root(tmp_path)
    registry = PolicyRegistry(tmp_path / "local" / "registry.json")
    register_decision_locations(registry, root, curated_on="2026-08-24")

    broad = registry.search(scope="decisions")
    assert len(broad) == 5

    narrow = registry.search(scope="decisions/locations/ticket-master")
    assert len(narrow) == 5  # inherited by descendants


def test_verify_reports_present_for_seeded_pointers(tmp_path):
    root = build_control_center_root(tmp_path)
    registry = PolicyRegistry(tmp_path / "local" / "registry.json")
    register_decision_locations(registry, root, curated_on="2026-08-24")

    result = registry.verify()
    assert result["ok"] is True
    states = {check["id"]: check["state"] for check in result["checks"]}
    assert states["decision-location:chain-head"] == "present"
    assert states["decision-location:host-file-pattern"] == "present"


def test_replace_true_updates_existing_entries_without_duplication(tmp_path):
    root = build_control_center_root(tmp_path)
    registry = PolicyRegistry(tmp_path / "local" / "registry.json")
    register_decision_locations(registry, root, curated_on="2026-08-24")
    register_decision_locations(registry, root, curated_on="2026-08-25")

    data = registry.load()
    ids = [entry["id"] for entry in data["entries"]]
    assert len(ids) == len(set(ids))  # no duplicate ids
    assert registry.get("decision-location:chain-head")["version"] == "2026-08-25"


def test_json_serialization_round_trip(tmp_path):
    root = build_control_center_root(tmp_path)
    registry = PolicyRegistry(tmp_path / "local" / "registry.json")
    register_decision_locations(registry, root, curated_on="2026-08-24")

    data = json.loads(registry.path.read_text(encoding="utf-8"))
    assert data["schema"] == "ellmos.policy-registry.v1"
    assert len(data["entries"]) == 5


def test_pointers_follow_the_control_move_and_fall_back_to_legacy(tmp_path):
    """_DECISIONS moved under _CONTROL on 2026-09-06; pointers must follow it.

    Regression for the live finding of 2026-09-12: five location pointers on
    ASUS-GEI verified as ``missing`` because the adapter kept building
    ``_control-center/_DECISIONS`` after the ledger had moved to
    ``_control-center/_CONTROL/_DECISIONS``.
    """
    # Legacy layout still resolves.
    legacy_root = build_control_center_root(tmp_path / "legacy")
    legacy = {e["id"]: e for e in location_entries(legacy_root, curated_on="2026-09-12")}
    assert legacy["decision-location:chain-head"]["source"]["origin"] == (
        "_control-center/_DECISIONS"
    )
    assert Path(legacy["decision-location:chain-head"]["source"]["uri"]).exists()

    # Moved layout wins when it exists, and the origin label follows.
    moved_root = tmp_path / "moved" / "_control-center"
    control = moved_root / "_CONTROL"
    control.mkdir(parents=True)
    inner = build_control_center_root(tmp_path / "moved" / "_staging")
    (inner / "_DECISIONS").rename(control / "_DECISIONS")
    moved = {e["id"]: e for e in location_entries(moved_root, curated_on="2026-09-12")}
    assert moved["decision-location:chain-head"]["source"]["origin"] == (
        "_control-center/_CONTROL/_DECISIONS"
    )
    assert moved["decision-location:machine-index"]["source"]["origin"] == (
        "_control-center/_CONTROL/_DECISIONS/_tools"
    )
    for entry_id in (
        "decision-location:chain-head",
        "decision-location:decided-and-done",
        "decision-location:host-file-pattern",
        "decision-location:machine-index",
    ):
        assert Path(moved[entry_id]["source"]["uri"]).exists(), entry_id
