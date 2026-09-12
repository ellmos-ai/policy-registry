# Third-Party Licenses & Transparency Notice

> **Project:** `ellmos-ai/policy-registry`  
> **Audited:** 2026-09-12  
> **Repository License:** [MIT License](LICENSE)  
> **Architecture & Privacy:** 100% Local-First, Zero-Egress, Unprivileged User-Mode (`RunAsInvoker`), Cryptographic Ed25519 Delegation, Fail-Closed Governance

---

## Executive Summary & Compliance Assurance

`policy-registry` is designed and operated under strict architectural, privacy, and governance invariants: **100% Local-First, Zero-Egress by default, unprivileged user-mode execution (`RunAsInvoker`), pointer-only storage, and cryptographic signed delegation verification**. The core policy registry, scope matcher, decision adapter, and signed delegation engine execute strictly within local filesystem boundaries without any unsolicited external network communication, telemetry exfiltration, or remote tracking.

All direct, optional, development, and transitive dependencies utilized across `policy-registry` are distributed under strictly **permissive open-source licenses** (MIT, Apache-2.0, BSD-3-Clause, PSFL-2.0). There are **zero AGPL or proprietary restrictive copyleft constraints**, ensuring maximum safety and portability for local developer environments, autonomous multi-agent swarms, and enterprise workstations.

Furthermore, `policy-registry` guarantees:
1. **100% Local-First & Zero Egress (INV-LOCAL-01):** The registry and delegation resolver operate entirely offline on local filesystem paths (`~/.policy-registry/registry.json`). Zero network sockets, zero telemetry exfiltration.
2. **Pointer-Only Architecture (INV-PTR-02):** Stores canonical URI references (`source.uri`), SHA-256 checksums, scopes, and priorities. Strictly rejects full-text payload or body duplication.
3. **Ed25519 Cryptographic Delegation (INV-CRYPTO-03):** Verifies issuer grants and delegate candidate signatures locally against a pinned public trust store (`IssuerTrustStore`) without external PKI dependencies.
4. **Advisory TOM-lm & Fail-Closed Fallback (INV-FAIL-04):** Ambiguous, missing, or conflicting norms return status code `2` with advisory TOM-lm notices and `automatic_authority: false`.
5. **Append-Only Audited Rule Register (INV-APPEND-05):** Explicit `adopt` materializes audited rules via append-only rows. Superseding an existing rule never deletes historical records.
6. **Effective Interaction Authority Modes (INV-MODE-06):** Effective runtime modes (`governance-bound` default, `user-sovereign`, `chat-authority-only`) evaluated with session override and project fallback.
7. **Unprivileged Non-Elevation / RunAsInvoker (INV-PRIV-07):** Runs strictly unprivileged in standard user space without elevated or administrative privileges.
8. **Multi-OS CI Matrix (INV-MAT-08):** Automated cross-platform matrix testing across Ubuntu, Windows, and macOS on Python 3.10, 3.11, 3.12, and 3.13.
9. **Strict CI Concurrency & Bytecode Gate (INV-GATE-09):** `cancel-in-progress: true` prevents redundant runner compute; whole-repo `compileall` ensures 100% valid bytecode.
10. **Dual Security Response & Triage SLA (INV-SLA-10):** Strict 48-hour response acknowledgment and 5-business-day triage commitment via canonical security reporting channels (`security@ellmos.ai`, `security@open-bricks.org`, `support@lukasgeiger.com`, `lukas@open-bricks.org`).

---

## Direct Runtime Dependencies

| Package | Constraint | Role / Functional Scope | License | Project Repository / Upstream |
|:---|:---:|:---|:---|:---|
| **Python Standard Library** | `>=3.10` | Core registry data model, JSON serialization, SQLite / file I/O, hash digests (SHA-256), scope AST parsing, CLI arguments | [PSFL-2.0](https://docs.python.org/3/license.html) | [python/cpython](https://github.com/python/cpython) |
| **cryptography** | `>=42` | Cryptographic primitives: Ed25519 signature verification, public key handling, hash-bound delegation integrity | [Apache-2.0 / BSD-3-Clause](https://github.com/pyca/cryptography/blob/main/LICENSE) | [pyca/cryptography](https://github.com/pyca/cryptography) |
| **tomli** | `>=2` | Standard-compliant TOML parser for project configuration (`.policy-registry.toml`) on Python < 3.11 | [MIT](https://github.com/hukkin/tomli/blob/master/LICENSE) | [hukkin/tomli](https://github.com/hukkin/tomli) |

---

## Optional Runtime Dependencies (Model Context Protocol / MCP Extra)

| Package | Constraint | Role / Functional Scope | License | Project Repository / Upstream |
|:---|:---:|:---|:---|:---|
| **mcp** | `>=1.28.1,<2` | Stdio MCP protocol adapter providing `policy_search`, `policy_get`, and `policy_resolve` tool surfaces for AI coding agents | [MIT](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE) | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) |

*Note on MCP:* The MCP adapter is an optional extra (`pip install "policy-registry[mcp]"`) strictly constrained to the maintained SDK v1 line. The base library and CLI operate independently without the MCP package.

---

## Direct Development, Test & Build Tooling

| Package | Constraint | Usage & Purpose | License | Source / Upstream |
|:---|:---:|:---|:---|:---|
| **pytest** | `>=8` | Automated test runner, contract verification suites, mock fixtures | [MIT](https://github.com/pytest-dev/pytest/blob/main/LICENSE) | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| **jsonschema** | `>=4.23` | Draft-07 / 2020-12 schema validation for policy entries and BYUM pointer envelopes | [MIT](https://github.com/python-jsonschema/jsonschema/blob/main/COPYING) | [python-jsonschema/jsonschema](https://github.com/python-jsonschema/jsonschema) |
| **setuptools** | `>=68` | Standard PEP 517/621 build backend and wheel packaging | [MIT](https://github.com/pypa/setuptools/blob/main/LICENSE) | [pypa/setuptools](https://github.com/pypa/setuptools) |
| **ruff** | `latest` | High-performance Python linter and code formatting enforcement | [MIT / Apache-2.0](https://github.com/astral-sh/ruff/blob/main/LICENSE-MIT) | [astral-sh/ruff](https://github.com/astral-sh/ruff) |

---

## Transitive Build & Test Inventory

All transitive dependencies have been audited and verified for permissive open-source license compliance:

| Package | Direct Dependency | License | Project Upstream |
|:---|:---|:---|:---|
| **cffi** | cryptography | MIT | https://github.com/python-cffi/cffi |
| **pycparser** | cffi | BSD-3-Clause | https://github.com/eliben/pycparser |
| **attrs** | jsonschema | MIT | https://github.com/python-attrs/attrs |
| **jsonschema-specifications** | jsonschema | MIT | https://github.com/python-jsonschema/jsonschema-specifications |
| **referencing** | jsonschema | MIT | https://github.com/python-jsonschema/referencing |
| **rpds-py** | referencing / jsonschema | MIT | https://github.com/crate-py/rpds |
| **pluggy** | pytest | MIT | https://github.com/pytest-dev/pluggy |
| **iniconfig** | pytest | MIT | https://github.com/pytest-dev/iniconfig |
| **packaging** | pytest / build | Apache-2.0 / BSD-2-Clause | https://github.com/pypa/packaging |
| **colorama** | pytest | BSD-3-Clause | https://github.com/tartley/colorama |

---

## Distribution Notes & Compliance Verification

- Installing the core package via `pip install policy-registry` installs exclusively permissive open-source packages (`cryptography`, and `tomli` if Python < 3.11).
- The cryptographic engine uses Ed25519 exclusively via `cryptography.hazmat.primitives.asymmetric.ed25519`. No external C binaries or unverified native libraries are loaded.
- Whole-repository automated contract tests (`tests/test_metadata.py`) continuously verify that no unauthorized network modules (`requests`, `urllib.request`, `httpx`, `aiohttp`, `urllib3`) are imported in `src/policy_registry/`.
