# Changelog

All notable changes to `policy-registry` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-08-26

### Added
- Optional `adapters/byum.py` seam for already validated BYUM v2 pointer envelopes. It builds only
  `kind=decision-candidate`, `adoption=pending`, `authority=advisory-pointer` metadata and never
  imports BYUM, reads event files, or parses a decision journal.
- Closed Draft 2020-12 schema `schemas/byum-decision-candidate-pointer.v1.schema.json` for the
  protocol identity, prediction ID, structured/hash-bound `decision_ref`, projection pointer/hash,
  and redacted projection status.
- Content-addressed Candidate IDs combine prediction ID and the full projection SHA-256. Identical
  repeats fail as duplicates; a changed projection becomes a new append-only Candidate entry.
- Fail-closed tests for protocol/hash/locator drift, raw/private/action/receipt fields, attempted
  authority/adoption promotion, non-resolution as authority, optional manifest binding, and the
  absence of BYUM imports or file/event parsers.
- Identifier fields accept bounded ID tokens rather than arbitrary text, and BYUM projection URIs
  must be local pointers; remote content cannot enter through this seam.

### Changed
- Documented the BYUM seam in the English/German architecture, security contract, READMEs, TODO,
  manifest, and LLM index. It remains separate from the still-open TOM-lm connector decision.
- Repaired the recurring all-platform CI installation failure: current setuptools rejects a legacy
  Trove license classifier when an SPDX license expression is present. `license = "MIT"` remains
  canonical; the redundant classifier was removed and a PEP 639 regression test added.
- Restored the advertised Python 3.10 runtime compatibility by replacing the Python 3.11-only
  `datetime.UTC` import with `timezone.utc`, guarded by a source-level regression test.
- Verified 126/126 local tests, JSON Schema meta-validation, Python compilation, and Ruff.

## [0.1.4] - 2026-08-25

### Added
- D2-R2 Stufe 1 (T-20260825-601850637, Option C -- gestufte Umsetzung, kein DB-Umzug): `Registry.register_rule()` for append-only `kind=rule` entries with mandatory audit fields (`hash`, `valid_from`), enforced only on this new path so existing lightweight `kind=rule` pointers (e.g. `decisions.py`'s `project-local-convention`) keep working unchanged.
- Supersede mechanism: `register_rule(entry, supersedes=<id>)` marks the predecessor row `status="superseded"` + `superseded_by=<new id>` without mutating any other field -- modeled on `session-checkpoint`'s ADR-003/004/005 immutable-row pattern, adapted onto the existing `registry.json` store (no new storage layer).
- `authority.py`: `POLICY_AUTHORITY_MODE` env-var switch (`policy-only` default, `memory-only`/`memory+policy` reserved for a later stage) plus a read-only `usmc_present()` probe. Deliberately inert in this stage -- `describe()["effective"]` is always `policy-only`; no USMC rework.
- CLI: `register-rule <entry.json> [--supersedes <id>]`, `authority-status`.
- Documented that the existing `source-resolver` role `policy.registry` (not a separate `policy.source` role -- verified empirically, none exists) already serves as the policy-source resolver; no new resolver role built.
- `tests/test_rule_append_only.py`, `tests/test_authority.py`.

## [0.1.3] - 2026-08-24

### Added
- Added `adapters/decisions.py`: a pointer-only seam onto the real `_DECISIONS` locations (TO-DECIDE-USER chain head, host-file naming pattern, `DECIDED-AND-DONE.md`, the generated `decisions.index.json`, and the project-local `DECISIONS.md` convention template). Registers a fixed, small set of stable location pointers -- never individual decisions -- via `register_decision_locations()` and the new CLI command `policy-registry seed-decisions --control-center-root <path>`.
- Added `adapters/decision_clicker.py`: an optional, importable seam (`available()`) onto the sibling `decision-clicker` tool, mirroring the existing `system_gap.py` pattern. Chosen deliberately as the LIGHTER of the two mechanics proposed by ticket T-20260824-474639761 (fixed manifest bundle vs. optional import) -- see the module docstring and `ARCHITECTURE.md` for the full reasoning.
- Registered `decision-clicker-v1` as a `seam`-type adapter and `decision.clicker` as an `optional` capability in `ellmos-module.v2.json`, and added `decision.location.pointers` to `provides`.
- Added `tests/test_decisions_adapter.py` and `tests/test_decision_clicker_seam.py`.

### Changed
- User decision 2026-08-24 (F1=A-hybrid, out of T-20260824-911756255): policy-registry becomes the one module that KNOWS where decision records live, as pointers -- not a second store of decision content.

## [0.1.2] - 2026-08-23

### Added
- Added dedicated Multi-OS (`ubuntu-latest`, `windows-latest`, `macos-latest`) and Multi-Python (`3.10`, `3.11`, `3.12`, `3.13`) GitHub Actions CI workflow in `.github/workflows/ci.yml` with `actions/checkout@v4`, `actions/setup-python@v5`, Pip caching, `ruff check .` linting gate, and `pytest` execution.
- Added comprehensive PEP 621 metadata in `pyproject.toml` including standard classifiers (`Development Status :: 4 - Beta`, `Topic :: Security`, `Topic :: Software Development :: Libraries :: Python Modules`, `Operating System :: Microsoft :: Windows`, `Operating System :: POSIX :: Linux`, `Operating System :: MacOS`), explicit `keywords`, and complete `[project.urls]` (`Homepage`, `Documentation`, `Repository`, `Issues`, `Changelog`, `Security`, `Umbrella`).
- Added umbrella security disclosure contact (`lukas@open-bricks.org`) and GitHub Private Security Advisories portal link in bilingual `SECURITY.md`.
- Expanded automated metadata and invariant contract test suite in `tests/test_metadata.py` to 11 contract tests (+3 new tests: `test_ci_workflow_integrity`, `test_pyproject_pep621_classifiers_and_urls`, `test_offline_and_privacy_invariants` with AST verification of zero unauthorized network egress modules).
- Added GitHub Actions CI status badge in `README.md` and `README_de.md`.

### Changed
- Added version `0.1.2` parity to `ellmos-module.v2.json`.
- Synchronized `llms.txt` index timestamp to 2026-08-23 with 78 verified passing tests.
- Synchronized README test pass badges and test status to 78/78 tests.

### Verified
- Test suite: 78/78 passed in Python 3.12.10 (`pytest`, 100% green).
- Static analysis & linting: `ruff check .` 100% clean (0 warnings/errors).
- Python compilation: `python -m compileall src tests` 100% clean.

## [0.1.2] - 2026-08-21

### Added
- Added hardened bilingual `SECURITY.md` (English & German) with Local-First & Zero-Egress invariants, pointer-only boundaries, cryptographic delegation constraints, and direct vulnerability disclosure contacts (`security@ellmos.ai` / `support@lukasgeiger.com`).
- Added two interactive bilingual Mermaid diagrams in `README.md` and `README_de.md`:
  - Scope Resolution & Hierarchical Precedence Flowchart (`exact > /* > parent > global`, consumer evaluation, TOM-lm advisory fallback).
  - Signed Delegation Resolver Verification Sequence (pinned issuer trust store, Ed25519 grant & candidate verification lifecycle).
- Added comprehensive Shields.io badges (Python 3.10-3.13, Platform, Architecture, Security, Privacy, Pytest 75/75 Passing, llms.txt, and Ecosystems).
- Added expanded 16-tool Sibling Tools & Ecosystem Matrix across `ellmos-ai`, `dev-bricks`, and `open-bricks` in both documentation languages.
- Expanded metadata test suite in `tests/test_metadata.py` to 8 tests (bilingual security policy parity, Mermaid diagram integrity, ecosystem link validation, pyproject classifiers).
- Added explicit PEP 621 classifiers for Python 3.10, 3.11, 3.12, and 3.13 in `pyproject.toml`.

### Changed
- Updated `llms.txt` discovery index and verification timestamp to 2026-08-21 with 75 verified passing tests.
- Bumped version to `0.1.2` across `pyproject.toml` and `src/policy_registry/__init__.py`.

### Verified
- Test suite: 75/75 passed in Python 3.12.10 (`pytest`, 100% green).
- Static analysis & linting: `ruff check .` 100% clean (0 warnings/errors).
- Python compilation: `python -m compileall src tests` 100% clean.

## [0.1.1] - 2026-08-16

### Added
- Added full German documentation parity in `README_de.md` with matched structure, quickstart, CLI, Python API, MCP adapter, and security boundaries.
- Added comprehensive metadata, schema, and manifest parity test suite in `tests/test_metadata.py` (version consistency, required docs, schema validation, `llms.txt` integrity).
- Added `LLM-Ready` badge and sibling tools cross-linking matrix (`memoryhooker`, `ellmos-scheduler`, `ellmos-voice-io`, `automation-master`, `CodeBox`) in `README.md` and `README_de.md`.
- Added provider-neutral, Ed25519 signer-/issuer-bound delegated-avatar candidate resolver (`DelegationResolver`, `IssuerTrustStore`).
- Added unified hierarchical scope matching and precedence across `PolicyRegistry` and the signed delegation resolver.
- Added `[tool.ruff]` and `[tool.ruff.lint]` configuration in `pyproject.toml`.

### Changed
- Modernized PEP 621 license metadata to avoid setuptools deprecation warnings during isolated package builds.
- Bound optional MCP adapter to maintained `mcp>=1.28.1,<2` line.
- Updated `llms.txt` discovery index and verification timestamp to 2026-08-16.

### Verified
- Test suite: 72/72 passed in Python 3.12.10 (`pytest`, 100% green).
- Static analysis & linting: `ruff check .` 100% clean.
- Python compilation: `compileall` 100% clean.

## [0.1.0] - 2026-07-30

### Added
- Initial local-first policy pointer registry engine with CLI (`policy-registry`), Python API (`PolicyRegistry`), and MCP adapter.
- Schema definitions for policy entries, delegation grants, and resolution receipts in `schemas/`.
- Integration adapters for `.SYNC/_policies` metadata import and view exporting.
- Initial `llms.txt` index file and documentation suite.
