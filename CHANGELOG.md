# Changelog

All notable changes to `policy-registry` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
