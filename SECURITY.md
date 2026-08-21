# Security Policy / Sicherheitsrichtlinie

[🇩🇪 Deutsche Version](#deutsche-sicherheitsrichtlinie) | [🇬🇧 English Version](#english-security-policy)

---

## English Security Policy

### Core Security & Privacy Invariants

1. **Local-First & Zero-Egress Operation**: `policy-registry` is designed for offline, local-first execution. It stores all authoritative metadata on the local filesystem (`~/.policy-registry/registry.json` or custom path) and performs zero unauthenticated network telemetry or data exfiltration.
2. **Pointer-Only Architecture**: The registry exclusively stores metadata, scope boundaries, priorities, and SHA-256 content pointers (`source.uri`). It **never** stores full policy bodies, sensitive credentials, API keys, private tokens, or client case files in registry records.
3. **Cryptographic Delegation Verification**: The signed delegation resolver relies on an external, pinned Ed25519 trust store (`IssuerTrustStore`). A delegation grant or candidate cannot self-assert its issuer. The resolver strictly verifies issuer signatures before trusting embedded delegate keys.
4. **Advisory & Candidate-Only Boundaries**: Unsigned candidates, raw TOM-lm outputs, and self-asserted receipts never authorize actions. The current resolver outputs advisory candidate receipts with `cutover_enabled: false` and `authorizes_action: false`.
5. **Non-Elevation & Permission Safety**: `policy-registry` operates entirely in standard user space without requiring administrative or elevated privileges.

### Reporting a Vulnerability

If you discover a potential security vulnerability or integrity flaw in `policy-registry`, please report it privately:

- **Primary Security Contact**: `security@ellmos.ai`
- **Maintainer Direct**: `support@lukasgeiger.com`

Please do not disclose security issues publicly via GitHub Issues or discussions until a fix has been released. We acknowledge receipt of security reports within 24 to 48 hours and coordinate release remediation promptly.

---

## Deutsche Sicherheitsrichtlinie

### Grundlegende Sicherheits- und Datenschutzinvariante

1. **Local-First & Zero-Egress-Betrieb**: `policy-registry` ist für den vollständig lokalen Offline-Betrieb konzipiert. Alle autoritativen Metadaten werden im lokalen Dateisystem abgelegt (`~/.policy-registry/registry.json` oder konfigurierter Pfad). Es findet keinerlei unautorisierter Netzwerk-Egress oder Telemetrie-Transfer statt.
2. **Reine Zeiger-Architektur (Pointer-Only)**: Die Registry speichert ausschließlich Metadaten, Geltungsbereiche, Prioritäten und SHA-256-Hash-Pointer (`source.uri`). Sie speichert **niemals** vollständige Regeltexte, Zugangsdaten, API-Tokens oder vertrauliche Falldaten in den Registry-Einträgen.
3. **Kryptografische Delegationsprüfung**: Der signierte Delegations-Resolver setzt auf einen externen, gepinnten Ed25519-Trust-Store (`IssuerTrustStore`). Ein Grant oder Entscheidungskandidat kann seinen Aussteller nicht selbst autorisieren. Signaturen des Ausstellers werden vor der Auswertung eingebetteter Delegationsschlüssel geprüft.
4. **Beratender & rein kandidatenbasierter Modus**: Unsignierte Kandidaten, rohe TOM-lm-Ausgaben und selbstbehauptete Nachweise begründen keine Handlungsautorität. Der Resolver erzeugt rein beratende Empfangsbestätigungen (`cutover_enabled: false`, `authorizes_action: false`).
5. **Keine Rechteausweitung (Non-Elevation)**: `policy-registry` arbeitet vollständig im regulären Benutzerkontext ohne erhöhte Administratorrechte.

### Meldung von Sicherheitslücken

Wenn Sie eine potenzielle Sicherheitslücke oder einen Integritätsfehler in `policy-registry` finden, melden Sie diesen bitte vertraulich:

- **Primärer Sicherheitskontakt**: `security@ellmos.ai`
- **Entwickler-Direktkontakt**: `support@lukasgeiger.com`

Bitte eröffnen Sie keine öffentlichen GitHub-Issues für Sicherheitsvorfälle. Wir bestätigen den Eingang von Hinweisen innerhalb von 24 bis 48 Stunden und koordinieren die Behebung umgehend.
