---
name: policy-registry
version: 0.2.4
description: "Use policy-registry to discover, resolve, propose, adopt, and verify local-first policy, rule, and decision pointers via CLI, Python API, or MCP."
---

# policy-registry Product Skill

## Overview

`policy-registry` (`0.2.4`, MIT) is a local-first, pointer-only metadata registry for policies, rules, and decisions. It stores metadata pointers (`id`, `kind`, `scope`, `owner`, `priority`, `precedence`, `version`, `privacy`, `source.uri`, optional `hash`) in `~/.policy-registry/registry.json` (or `--registry` / `POLICY_REGISTRY_PATH`) without duplicating canonical full-text files.

## When to Use / Boundaries

- **Use for:** registering policy/rule/decision pointers, deterministic scope/consumer resolution (`governance-bound`, `user-sovereign`, `chat-authority-only`), hash-bound `propose-change` / explicit `adopt` workflows, local source verification (`verify`), and Ed25519 signed delegation resolution (`resolve-delegation`).
- **Do not use for:** storing full policy payloads (`content`, `body`, `full_text`, `payload` are rejected), automated norm enforcement without user confirmation, or remote/network policy fetching (100% zero-egress).

## Installation & Entrypoints

```bash
pip install -e .
# Optional MCP server extra:
pip install -e ".[mcp]"
```

- CLI: `policy-registry [--registry <path>] <subcommand>`
- MCP server (stdio via FastMCP): `policy-registry-mcp`
- Python API: `from policy_registry import PolicyRegistry, DelegationResolver, IssuerTrustStore`

## Core CLI Commands & Readback

| Task | Command | Notes / Exit Codes |
|---|---|---|
| Initialize registry | `policy-registry init` | Creates local JSON registry (`0` on success) |
| List entries | `policy-registry list` | JSON list of registered pointers |
| Get single entry | `policy-registry get <id>` | Returns entry JSON or non-zero if missing |
| Search pointers | `policy-registry search [query] [--scope S] [--consumer C] [--kind K]` | Filtered metadata search |
| Resolve norm | `policy-registry resolve --scope <S> [--consumer C] [--query Q] [--mode M]` | Exit `0` = resolved; Exit `2` = `missing`/`insufficient`/`conflict` (advisory, `automatic_authority: false`) |
| Propose chat change | `policy-registry propose-change --id ID --title T --scope S --owner O --session SID --quote Q --at ISO8601` | Records `decision-candidate` / `adoption=pending` |
| Adopt candidate | `policy-registry adopt <candidate_id> --rule-id <rule_id> --at ISO8601 [--supersedes OLD]` | Materializes audited append-only rule |
| Verify local sources | `policy-registry verify` | Checks local pointer hashes (`ok`, `unreadable`, `missing`) without mutating hashes |
| Authority mode status | `policy-registry authority-status [--mode M] [--project-root DIR]` | Reports effective interaction mode |
| Verify signed delegation | `policy-registry resolve-delegation --grant <json> --candidate <json> --trust-store <json> [--at ISO8601]` | Fail-closed Ed25519 verification (`cutover_enabled: false`) |

## MCP Tools (`policy-registry-mcp`)

- `policy_search(query="", scope="", consumer="")`: Find metadata pointers without copying canonical policy text.
- `policy_get(entry_id)`: Return one registry entry by stable ID.
- `policy_resolve(scope, query="", consumer="", mode="", current_instruction="", project_root="")`: Resolve explicit norms; returns advisory fallback when unresolved.

## Verification & References

- Always check exit code and JSON output (`status`, `ok`, `automatic_authority`) after `resolve` or `verify`.
- Full documentation: [`README.md`](README.md), [`README_de.md`](README_de.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/AUTORITAETS-MODI.md`](docs/AUTORITAETS-MODI.md), [`docs/SIGNED_DELEGATION_RESOLVER.md`](docs/SIGNED_DELEGATION_RESOLVER.md), [`llms.txt`](llms.txt).
