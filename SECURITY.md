# Security Policy / Sicherheitsrichtlinie

[🇩🇪 Deutsche Version](#deutsche-sicherheitsrichtlinie) | [🇬🇧 English Version](#english-security-policy)

---

## English Security Policy

### Supported Versions

We provide active security maintenance for current releases:

| Version | Supported | Security Maintenance Level |
|---|---|---|
| `0.2.x` | :white_check_mark: | Active release line (Full security maintenance) |
| `0.1.x` | :white_check_mark: | Maintenance release line (Critical security fixes) |
| `< 0.1.0` | :x: | End of life (No security updates) |

### Core Security & Privacy Invariants

1. **Local-First & Zero-Egress Operation**: `policy-registry` is designed for offline, local-first execution. It stores all authoritative metadata on the local filesystem (`~/.policy-registry/registry.json` or custom path) and performs zero unauthenticated network telemetry or data exfiltration.
2. **Pointer-Only Architecture**: The registry exclusively stores metadata, scope boundaries, priorities, and SHA-256 content pointers (`source.uri`). It **never** stores full policy bodies, sensitive credentials, API keys, private tokens, or client case files in registry records.
3. **Cryptographic Delegation Verification**: The signed delegation resolver relies on an external, pinned Ed25519 trust store (`IssuerTrustStore`). A delegation grant or candidate cannot self-assert its issuer. The resolver strictly verifies issuer signatures before trusting embedded delegate keys.
4. **Advisory & Candidate-Only Boundaries**: Unsigned candidates, raw TOM-lm outputs, and self-asserted receipts never authorize actions. The current resolver outputs advisory candidate receipts with `cutover_enabled: false` and `authorizes_action: false`.
5. **BYUM Pointer Boundary**: The optional BYUM v2 seam accepts only a prevalidated, closed pointer envelope. It imports no BYUM code, parses no event journal, rejects raw/private/action/receipt fields, and emits candidate-only pending metadata that `resolve()` cannot treat as authority.
6. **Non-Elevation & Permission Safety**: `policy-registry` operates entirely in standard user space (RunAsInvoker) without requiring administrative or elevated privileges.

### Reporting a Vulnerability

If you discover a potential security vulnerability or integrity flaw in `policy-registry`, please report it privately:

- **Primary Security Contact**: `security@ellmos.ai`
- **Umbrella Security Contact**: `security@open-bricks.org` / `lukas@open-bricks.org`
- **Maintainer Direct**: `support@lukasgeiger.com`
- **GitHub Security Advisories**: [Open Private Security Advisory](https://github.com/ellmos-ai/policy-registry/security/advisories)

#### Security SLAs
- **Initial Response SLA**: Within 48 hours of receipt.
- **Triage & Status Assessment**: Within 5 business days.
- **Remediation & Advisory Publication**: Coordinated promptly with patch release.

Please do not disclose security issues publicly via GitHub Issues or discussions until a fix has been released. We coordinate release remediation promptly.

---

## Deutsche Sicherheitsrichtlinie

### Unterstützte Versionen

Wir pflegen die folgenden Versionslinien aktiv mit Sicherheitsupdates:

| Version | Unterstützt | Wartungsstufe |
|---|---|---|
| `0.2.x` | :white_check_mark: | Aktive Hauptlinie (Vollständige Sicherheitswartung) |
| `0.1.x` | :white_check_mark: | Wartungslinie (Kritische Sicherheitsfixes) |
| `< 0.1.0` | :x: | End of Life (Keine Sicherheitsupdates) |

### Grundlegende Sicherheits- und Datenschutzinvariante

1. **Local-First & Zero-Egress-Betrieb**: `policy-registry` ist für den vollständig lokalen Offline-Betrieb konzipiert. Alle autoritativen Metadaten werden im lokalen Dateisystem abgelegt (`~/.policy-registry/registry.json` oder konfigurierter Pfad). Es findet keinerlei unautorisierter Netzwerk-Egress oder Telemetrie-Transfer statt.
2. **Reine Zeiger-Architektur (Pointer-Only)**: Die Registry speichert ausschließlich Metadaten, Geltungsbereiche, Prioritäten und SHA-256-Hash-Pointer (`source.uri`). Sie speichert **niemals** vollständige Regeltexte, Zugangsdaten, API-Tokens oder vertrauliche Falldaten in den Registry-Einträgen.
3. **Kryptografische Delegationsprüfung**: Der signierte Delegations-Resolver setzt auf einen externen, gepinnten Ed25519-Trust-Store (`IssuerTrustStore`). Ein Grant oder Entscheidungskandidat kann seinen Aussteller nicht selbst autorisieren. Signaturen des Ausstellers werden vor der Auswertung eingebetteter Delegationsschlüssel geprüft.
4. **Beratender & rein kandidatenbasierter Modus**: Unsignierte Kandidaten, rohe TOM-lm-Ausgaben und selbstbehauptete Nachweise begründen keine Handlungsautorität. Der Resolver erzeugt rein beratende Empfangsbestätigungen (`cutover_enabled: false`, `authorizes_action: false`).
5. **BYUM-Pointer-Grenze**: Der optionale BYUM-v2-Seam akzeptiert ausschließlich einen vorvalidierten, geschlossenen Pointer-Umschlag. Er importiert keinen BYUM-Code, parst kein Ereignisjournal, weist Rohdaten-, Privat-, Action- und Receipt-Felder ab und erzeugt nur ausstehende Kandidatenmetadaten, die `resolve()` nicht als Autorität behandeln kann.
6. **Keine Rechteausweitung (Non-Elevation)**: `policy-registry` arbeitet vollständig im regulären Benutzerkontext (RunAsInvoker) ohne erhöhte Administratorrechte.

### Meldung von Sicherheitslücken

Wenn Sie eine potenzielle Sicherheitslücke oder einen Integritätsfehler in `policy-registry` finden, melden Sie diesen bitte vertraulich:

- **Primärer Sicherheitskontakt**: `security@ellmos.ai`
- **Dachverband-Sicherheitskontakt**: `security@open-bricks.org` / `lukas@open-bricks.org`
- **Entwickler-Direktkontakt**: `support@lukasgeiger.com`
- **GitHub Security Advisories**: [Private Sicherheitsmeldung einreichen](https://github.com/ellmos-ai/policy-registry/security/advisories)

#### Sicherheits-SLAs
- **Erstreaktions-SLA**: Innerhalb von 48 Stunden nach Eingang.
- **Triage & Statusbewertung**: Innerhalb von 5 Werktagen.
- **Behebung & Advisory-Veröffentlichung**: Zeitnah koordinierte Bereitstellung des Patches.

Bitte eröffnen Sie keine öffentlichen GitHub-Issues für Sicherheitsvorfälle. Wir bestätigen den Eingang von Hinweisen verlässlich und koordinieren die Behebung umgehend.
