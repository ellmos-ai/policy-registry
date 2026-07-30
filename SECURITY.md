# Security

Die Registry speichert Metadaten und Quellpointer. Keine Secrets, Tokens,
Fallakten oder Regelvolltexte registrieren. `privacy` beschreibt die
Empfindlichkeit des referenzierten Materials, ersetzt aber keine
Dateisystemberechtigung.

Lokale Pfade können Informationen über Benutzer- oder Projektstrukturen
offenlegen. Aggregierte `.SYNC`-Sichten deshalb nur in bereits entsprechend
geschützte private Sync-Bereiche schreiben.

Fehler bitte privat an den Repository-Eigentümer melden.

## Signed Delegation Resolver

Delegation trust is external and pinned. A receipt or candidate cannot
self-assert its issuer. V1 accepts only Ed25519, verifies the issuer signature
before trusting the delegate key embedded in the grant, and then verifies the
candidate with that delegate key.

Raw TOM_lm output, raw evidence, unsigned candidates and self-asserted receipts
never authorize an action. The current implementation is candidate-only:
`cutover_enabled` and `authorizes_action` remain false even after all checks
pass.

Private signing keys and secrets do not belong in resolver inputs, the registry
or this repository. The module provides verification only; key generation,
signing, rotation and custody remain external responsibilities.

