# policy-registry

`policy-registry` ist ein eigenständiges, wiederverwendbares **LOCAL-FIRST**
Register für Policies, Regeln und Entscheidungen. Es speichert Metadaten und
Pointer auf kanonische Quellen, nicht deren Volltext. Dadurch bleiben lokale
Quellen autoritativ und auffindbar, auch wenn OneDrive, `.SYNC` oder
`system-gap-master` nicht verfügbar sind.

## Sicherheits- und Autoritätsvertrag

- Die lokale Registry unter `~/.policy-registry/registry.json` ist autoritativ
  für ihre Metadaten.
- Kanonischer Regeltext bleibt an `source.uri`.
- `content`, `body`, `full_text` und `payload` werden als Registry-Felder
  abgewiesen.
- Gültige, explizit adoptierte `policy`, `rule` oder `decision` werden zuerst
  nach Priorität und Präzedenz aufgelöst.
- Fehlt eine Norm, reicht sie nicht aus oder widersprechen sich gleichrangige
  Normen, meldet die Auflösung einen **beratenden TOM-lm-Fallback**. Sie ruft
  TOM-lm nicht automatisch auf und verleiht seinem Ergebnis keine Autorität.
- Ein TOM-Ergebnis darf als `evidence` oder `decision-candidate` registriert
  werden. Erst eine explizite Adoption macht daraus eine generalisierte Policy.

## Metadatenmodell

Jeder Eintrag kennt mindestens:

| Feld | Bedeutung |
|---|---|
| `id`, `kind`, `title` | stabile Identität und Typ |
| `scope`, `consumers` | Geltungsbereich und konsumierende Akteure |
| `owner`, `authority` | Eigentümer und Autoritätsart |
| `priority`, `precedence` | Auflösungsrang |
| `version`, `hash` | Version und optionaler SHA-256-Nachweis |
| `privacy` | `public`, `internal`, `private`, `restricted` |
| `source.uri` | Pointer auf die kanonische Quelle |
| `status`, `adoption` | Lebenszyklus und explizite Übernahme |

Das normative JSON-Schema liegt unter
`schemas/policy-entry.schema.json`.

## CLI

```powershell
policy-registry init
policy-registry import-sync --root "$HOME\OneDrive\.SYNC\_policies" --slot workstation
policy-registry search "OneDrive" --consumer codex
policy-registry resolve --scope system-wide --query "OneDrive"
policy-registry verify
```

Ein alternativer lokaler Pfad kann mit `--registry` oder
`POLICY_REGISTRY_PATH` gesetzt werden.

`resolve` liefert Exit `0` nur bei eindeutiger expliziter Auflösung. `missing`,
`insufficient` und `conflict` liefern Exit `2` und einen strukturierten
TOM-lm-Hinweis mit `automatic_authority: false`.

## Python-API

```python
from policy_registry import PolicyRegistry

registry = PolicyRegistry()
matches = registry.search("release", scope=".AI/.MODULES", consumer="codex")
decision = registry.resolve(scope="system-wide", query="OneDrive")
```

## MCP

Der optionale MCP-Adapter stellt `policy_search`, `policy_get` und
`policy_resolve` bereit:

```powershell
pip install "policy-registry[mcp]"
python -m policy_registry.mcp_server
```

Das MCP-Extra ist für CLI und Python-API nicht erforderlich.

## `.SYNC/_policies` und system-gap-master

Der Adapter `policy_registry.adapters.sync_policies` liest die bestehenden
Formate:

- `library/P-*.md`
- `adoption/<slot>.json`
- `sources/<slot>.json`

Er migriert ausschließlich Metadaten, Pfade und Hashes. Die Quelldokumente
bleiben kanonisch. Eine aggregierte Sicht kann als
`_policies/registry/<slot>.json` in derselben bestehenden Struktur erzeugt
werden:

```powershell
policy-registry export-sync-view `
  --root "$HOME\OneDrive\.SYNC\_policies" `
  --slot workstation
```

`system-gap-master` ist ein optionaler Transportadapter. Ist es nicht
installiert oder `.SYNC` nicht erreichbar, bleiben Registrierung, Suche,
Auflösung und Prüfung vollständig funktionsfähig.

## Grenzen des MVP

- keine automatische Volltextindexierung;
- kein automatischer TOM-lm-Aufruf;
- keine automatische Adoption;
- kein Hosted-Service;
- keine Fremdhost-Synchronisation oder Behauptung über deren Zustand.

