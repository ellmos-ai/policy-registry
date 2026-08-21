<img src="assets/banner.png" width="100%" alt="policy-registry Banner">

# policy-registry

[![Python 3.10 | 3.11 | 3.12 | 3.13](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows | Linux | macOS](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/ellmos-ai/policy-registry)
[![Architecture: Local-First Pointer](https://img.shields.io/badge/architecture-Local--First%20Pointer-teal.svg)](ARCHITECTURE.md)
[![Security: Local-First / Zero-Egress](https://img.shields.io/badge/security-Local--First%20%7C%20Zero--Egress-success.svg)](SECURITY.md)
[![Privacy: 100% Offline](https://img.shields.io/badge/privacy-100%25%20Offline-brightgreen.svg)](SECURITY.md)
[![Ecosystem: ellmos--ai](https://img.shields.io/badge/Ecosystem-ellmos--ai-purple.svg)](https://github.com/ellmos-ai)
[![Ecosystem: open--bricks](https://img.shields.io/badge/Ecosystem-open--bricks-blue.svg)](https://github.com/open-bricks)
[![Tests: Pytest](https://img.shields.io/badge/Tests-Pytest%2075%2F75%20Passing-brightgreen.svg)](tests/)
[![LLM-Ready](https://img.shields.io/badge/LLM--Ready-llms.txt-orange.svg)](llms.txt)

[🇩🇪 Deutsch](README_de.md) | **🇬🇧 English**

> [!NOTE]
> **AI & LLM Integration Notice**: This repository includes an [`llms.txt`](llms.txt) index file tailored for automated context ingestion, agentic system prompts, and LLM code understanding.

`policy-registry` is an autonomous, reusable **LOCAL-FIRST** registry for policies, rules, and decisions. It stores metadata pointers and SHA-256 hashes referencing canonical sources rather than duplicating full text. This ensures local sources remain authoritative and discoverable even when OneDrive, `.SYNC`, or `system-gap-master` are unreachable.

---

## Test Status

Verified local test pass as of 2026-08-21 (Python 3.12.10):

- `python -m pytest --collect-only` collects 75 tests.
- `python -m pytest` passes 75/75 tests (100% green).
- `ruff check .` passes with 0 lint warnings.

---

## System Architecture

```mermaid
graph TD
    A["Canonical Sources (~/.SYNC/_policies / Local Files)"] -->|Pointer & SHA-256 Hash| B["Policy Registry (~/.policy-registry/registry.json)"]
    B --> C["CLI (policy-registry)"]
    B --> D["Python API (PolicyRegistry)"]
    B --> E["MCP Server Adapter (policy_search / policy_resolve)"]
    B --> G["Signed Delegation Resolver (Ed25519)"]
    E --> F["AI Agents & Frameworks (Codex / Gemini / Claude)"]
    D --> F
    G --> F
```

---

## Scope Resolution & Hierarchical Precedence

The diagram below illustrates how `PolicyRegistry` and the signed delegation resolver evaluate scopes, precedence ranks, and fallback advisories:

```mermaid
flowchart TD
    Q["Scope Query (e.g. project:alpha/sub)"] --> S{"Scope Match?"}
    S -- "Exact Match (project:alpha/sub)" --> R1["Rank 1: Exact Match"]
    S -- "Descendant Wildcard (project:alpha/*)" --> R2["Rank 2: Wildcard Match"]
    S -- "Parent Scope (project:alpha)" --> R3["Rank 3: Inherited Parent"]
    S -- "Global Alias (* / global / system-wide)" --> R4["Rank 4: Global Norm"]
    S -- "No Scope Match / Sibling" --> F1["TOM-lm Advisory Fallback (Missing)"]
    
    R1 --> C{"Consumer Match?"}
    R2 --> C
    R3 --> C
    R4 --> C
    
    C -- "Universal (* or empty)" --> P["Order by Priority & Precedence"]
    C -- "Exact Consumer Hit" --> P
    C -- "Consumer Filter Mismatch" --> F1
    
    P --> D{"Single Winner or Conflict?"}
    D -- "Definitive Entry" --> OUT["Status: OK (Exit Code 0)"]
    D -- "Conflicting Norms" --> F2["Status: Conflict (Advisory TOM Notice, Exit Code 2)"]
    D -- "Insufficient Definition" --> F3["Status: Insufficient (Advisory TOM Notice, Exit Code 2)"]
```

---

## Signed Delegation Verification Lifecycle

`policy-registry` provides cryptographic verification for issuer-delegated decision candidates:

```mermaid
sequenceDiagram
    autonumber
    participant Issuer as Issuer Trust Store (Pinned)
    participant Grant as Signed Delegation Grant
    participant Cand as Decision Candidate
    participant Res as DelegationResolver
    participant Agent as AI Agent / Consumer

    Res->>Issuer: Load trusted issuer Ed25519 public keys
    Res->>Grant: Verify issuer cryptographic signature on grant
    Note over Res,Grant: Grant authenticates delegate public key & capability bounds
    Res->>Cand: Verify delegate cryptographic signature on candidate
    Res->>Res: Check scope, expiration, policy pointers, and non-elevation
    Res-->>Agent: Return DelegationResolution (Advisory Receipt, cutover_enabled: false)
```

---

## Security & Authority Contract

- The local registry at `~/.policy-registry/registry.json` is authoritative for its metadata.
- Canonical policy text remains at `source.uri`.
- Fields like `content`, `body`, `full_text`, and `payload` are rejected as registry entries.
- Valid, explicitly adopted `policy`, `rule`, or `decision` entries resolve according to the shared hierarchical scope contract, followed by priority and precedence.
- If a norm is missing, insufficient, or in conflict, resolution reports an **advisory TOM-lm fallback notice** without automatic execution or unwarranted authority.
- TOM results may be recorded as `evidence` or `decision-candidate`. An explicit adoption is required to generalize into a policy.

### Scope Contract

`PolicyRegistry` and the signed delegation resolver share the matcher in [`src/policy_registry/scope.py`](src/policy_registry/scope.py):

1. Global aliases `*`, `all`, `global`, and `system-wide` match any scope.
2. Normal scopes match exactly and inherit to descendants (`project:alpha` applies to `project:alpha/release`).
3. `project:alpha/*` matches descendants only, not the parent itself.
4. Precedence order: `exact > /* > parent > global`. When relation matches, deeper path wins.
5. Sibling scopes do not match.
6. Empty consumer filter matches all; empty consumer list or `*` is universal; otherwise exact match is required.

---

## Metadata Model

Every entry supports the following fields:

| Field | Description |
|---|---|
| `id`, `kind`, `title` | Stable identifier and entry kind |
| `scope`, `consumers` | Scope boundaries and consumer actors |
| `owner`, `authority` | Owner and authority classification |
| `priority`, `precedence` | Resolution ordering rank |
| `version`, `hash` | Version and optional SHA-256 checksum |
| `privacy` | `public`, `internal`, `private`, `restricted` |
| `source.uri` | Pointer to canonical source document |
| `status`, `adoption` | Lifecycle state and explicit adoption record |

The normative JSON Schema is maintained at [`schemas/policy-entry.schema.json`](schemas/policy-entry.schema.json).

---

## CLI Usage

```powershell
policy-registry init
policy-registry import-sync --root "$HOME\OneDrive\.SYNC\_policies" --slot workstation
policy-registry search "OneDrive" --consumer codex
policy-registry resolve --scope system-wide --query "OneDrive"
policy-registry verify
```

An alternative registry path can be set with `--registry` or `POLICY_REGISTRY_PATH`.

`resolve` returns exit code `0` on definitive resolution. Statuses `missing`, `insufficient`, and `conflict` return exit code `2` with structured advisory guidance and `automatic_authority: false`.

---

## Python API

```python
from policy_registry import PolicyRegistry

registry = PolicyRegistry()
matches = registry.search("release", scope=".AI/.MODULES", consumer="codex")
decision = registry.resolve(scope="system-wide", query="OneDrive")
```

### Signed Delegation Resolver

`policy-registry` can verify an issuer-signed delegation grant and a delegate-signed decision candidate against a pinned trust store:

```powershell
policy-registry resolve-delegation `
  --grant signed-grant.json `
  --candidate signed-candidate.json `
  --trust-store issuer-trust.json
```

Full specification and boundaries: [`docs/SIGNED_DELEGATION_RESOLVER.md`](docs/SIGNED_DELEGATION_RESOLVER.md).

---

## Model Context Protocol (MCP) Server

The optional MCP server adapter provides `policy_search`, `policy_get`, and `policy_resolve`:

```powershell
pip install "policy-registry[mcp]"
python -m policy_registry.mcp_server
```

The MCP extra is bounded to the maintained MCP SDK v1 line `>=1.28.1,<2`.

---

## Ecosystem & Related Tools

`policy-registry` is part of the `ellmos-ai` and `open-bricks` local-first agent ecosystem:

| Repository | Purpose | Ecosystem |
|---|---|---|
| [`ellmos-ai/memoryhooker`](https://github.com/ellmos-ai/memoryhooker) | Hook-based long-term memory & context layer for LLM agents | `ellmos-ai` |
| [`ellmos-ai/ellmos-scheduler`](https://github.com/ellmos-ai/ellmos-scheduler) | Deterministic task runner and scheduler for multi-agent workflows | `ellmos-ai` |
| [`ellmos-ai/ellmos-voice-io`](https://github.com/ellmos-ai/ellmos-voice-io) | Speech I/O adapter for multimodal assistants | `ellmos-ai` |
| [`ellmos-ai/lock-master`](https://github.com/ellmos-ai/lock-master) | Multi-agent locking & lease protocol for concurrent autonomous workflows | `ellmos-ai` |
| [`ellmos-ai/ticket-master`](https://github.com/ellmos-ai/ticket-master) | Deterministic ticket management and lifecycle coordinator | `ellmos-ai` |
| [`ellmos-ai/clutch`](https://github.com/ellmos-ai/clutch) | Task execution coordinator and agent runtime | `ellmos-ai` |
| [`ellmos-ai/ellmos-controlcenter-mcp`](https://github.com/ellmos-ai/ellmos-controlcenter-mcp) | Gateway and orchestrator for local MCP tool bundles | `ellmos-ai` |
| [`ellmos-ai/ellmos-filecommander-mcp`](https://github.com/ellmos-ai/ellmos-filecommander-mcp) | Local-first desktop file management MCP server | `ellmos-ai` |
| [`ellmos-ai/ellmos-codecommander-mcp`](https://github.com/ellmos-ai/ellmos-codecommander-mcp) | AST-aware code analysis & transformation MCP server | `ellmos-ai` |
| [`ellmos-ai/n8n-manager-mcp`](https://github.com/ellmos-ai/n8n-manager-mcp) | Local-first n8n workflow management MCP server | `ellmos-ai` |
| [`dev-bricks/automation-master`](https://github.com/dev-bricks/automation-master) | Local-first event-sourcing ledger and credit-gate automation engine | `dev-bricks` |
| [`dev-bricks/DevCenter`](https://github.com/dev-bricks/DevCenter) | Developer workspace and automation cockpit | `dev-bricks` |
| [`dev-bricks/CodeBox`](https://github.com/dev-bricks/CodeBox) | Safe multi-language sandboxed execution environment | `dev-bricks` |
| [`dev-bricks/companion-for-agy`](https://github.com/dev-bricks/companion-for-agy) | PTY terminal companion and session manager for Antigravity | `dev-bricks` |
| [`dev-bricks/safe-start-for-codex`](https://github.com/dev-bricks/safe-start-for-codex) | Workspace initializer and preflight security checker for Codex | `dev-bricks` |
| [`open-bricks/open-bricks`](https://github.com/open-bricks) | Open-source developer tools umbrella | `open-bricks` |

---

## MVP Boundaries

- No automated full-text duplication or indexing.
- No automated TOM-lm execution.
- No automated adoption without explicit command.
- No cloud hosted dependencies (100% Local-First).
- No unauthenticated remote host mutations.

---

## License

MIT License — see [LICENSE](LICENSE).
