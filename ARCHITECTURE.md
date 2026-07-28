# Architekturentscheidung [U 2026-07-28]

## Entscheidung

`policy-registry` ist ein eigenständiges LOCAL-FIRST-Modul. Es hängt weder von
OneDrive noch von `system-gap-master` ab. Die lokale Registry ist für
Registry-Metadaten autoritativ; die referenzierte Quelldatei bleibt für den
Regeltext autoritativ.

## Grenzen

```text
kanonische lokale Quellen
          │ Pointer + Hash
          ▼
  lokale policy-registry ── CLI / Python-API / optional MCP
          │
          ├── optional: bestehende .SYNC/_policies-Sicht
          └── optional: system-gap-master als Transportseam
```

Die `.SYNC/_policies`-Struktur wird weiterverwendet. Es entsteht kein zweites
privates Bibliotheks- oder Adoptionsformat. Die Registry ergänzt sie um eine
lokale Auflösungs- und Discovery-Schicht.

## Präzedenz und TOM-lm

1. aktive, adoptierte und zeitlich gültige explizite Policy/Regel/Decision;
2. höhere `priority`;
3. höhere `precedence`;
4. Gleichstand an der Spitze bedeutet Konflikt, keine stille Auswahl.

Bei `missing`, `insufficient` oder `conflict` ist TOM-lm ausschließlich
beratender Fallback. Sein Ergebnis ist Evidence oder Decision-Kandidat.
Generalisierung erfordert eine explizite Adoption.

## Benennung und Kollisionen

Vor Anlage wurden am 2026-07-28 geprüft:

- lokale Repos unter `C:\_Local_DEV\repos`;
- `.AI/.MODULES` und der generierte Modulkatalog;
- Repositories der Organisationen `ellmos-ai` und `dev-bricks`;
- PyPI-Projektnamen.

Für `policy-registry` wurde keine Kollision gefunden.

