# Changelog

## Unreleased

- Add a provider-neutral, Ed25519 signer-/issuer-bound delegated-avatar
  candidate resolver for `D-20260730-001`.
- Keep runtime cutover disabled: qualified candidates never authorize actions.
- Modernize PEP 621 license metadata to avoid setuptools deprecation warnings
  during isolated package builds.
- Unify hierarchical scope matching and precedence across `PolicyRegistry` and
  the signed delegation resolver, including parent scopes, `/*` descendants,
  global aliases, sibling exclusion, and consumer matching.

### Verified

- Synchronized documentation test status & `llms.txt` verification timestamp
  with the current suite (2026-08-08): Python 3.12.10,
  `pytest --collect-only` collected 66 tests and `pytest` passed 66/66 (100%
  green).

All notable changes to `policy-registry` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-07-30

### Added
- Added `llms.txt` index file for AI/LLM assistant context loading and documentation discovery.
- Added Shields.io ecosystem badges (Python 3.10+, License MIT, ellmos-ai, open-bricks, Pytest status) to `README.md`.
- Added Mermaid system architecture diagram to `README.md` illustrating local policy pointers, adapters, and agent integration.
- Added AI/LLM integration notice banner to `README.md`.

### Verified
- Verified current documented pytest status is maintained in the Unreleased
  section as the suite has expanded beyond the original 0.1.1 baseline.
