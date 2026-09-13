# -*- coding: utf-8 -*-
"""Prueft das eigene Modul-Manifest gegen das kanonische Schema -- vor dem Push.

Die Schemakopie unter `_schema/` ist genau das: eine Kopie. `_schema/PIN.json`
traegt den SHA-256 der kanonischen Fassung; der letzte Test hier schlaegt an, sobald beide
auseinanderlaufen. Dann nicht die Kopie von Hand anpassen, sondern neu synchronisieren:

    python <MODULES>/_scripts/sync_schema_to_repo.py --repo <dieses Repo>
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "_schema" / "ellmos.module.v2.schema.json"
PIN = ROOT / "_schema" / "PIN.json"
MANIFEST = ROOT / "ellmos-module.v2.json"


def _hash(pfad):
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    kanonisch = json.dumps(daten, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(kanonisch.encode("utf-8")).hexdigest()


class ModulManifestVertrag(unittest.TestCase):
    def test_manifest_erfuellt_das_schema(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("jsonschema nicht installiert (Test-Abhaengigkeit)")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        fehler = sorted(Draft202012Validator(schema).iter_errors(manifest),
                        key=lambda e: list(e.path))
        self.assertEqual(
            [], [f"{'/'.join(str(x) for x in e.path) or '(root)'}: {e.message}" for e in fehler]
        )

    def test_schemakopie_ist_nicht_von_ihrem_pin_abgewichen(self) -> None:
        """Faengt die HANDAENDERUNG an der Kopie -- mehr nicht.

        Pin und Kopie liegen beide in diesem Repo und wandern beim Sync gemeinsam.
        Dieser Fall allein sagt daher nichts darueber, ob der Kanon weitergezogen ist;
        dafuer ist der naechste Test da.
        """
        pin = json.loads(PIN.read_text(encoding="utf-8"))
        self.assertEqual(
            pin["sha256"], _hash(SCHEMA),
            "Die Schemakopie weicht von ihrem Pin ab -- neu synchronisieren statt von Hand aendern.",
        )

    def test_pin_entspricht_dem_kanonischen_schema(self) -> None:
        """Faengt den KANONISCHEN Drift: die Regel ist weitergezogen, die Kopie nicht.

        Der Test davor konnte das nie sehen -- er vergleicht zwei Dateien desselben
        Repos. Am 2026-09-13 wurde das gemessen: nach einer kanonischen Schemaaenderung
        blieben die Vertragstests in coma und policy-registry gruen, obwohl beide Kopien
        veraltet waren (T-20260913-148672421).

        Warum der Kanon nicht als Paket eingebunden wird: Die Module hier sind bewusst
        laufzeit-abhaengigkeitsfrei. Deshalb dasselbe Muster wie in system-explorers
        tests/test_manifest_schema_drift.py -- pruefen WENN das Schema erreichbar ist,
        sonst ueberspringen. Ein uebersprungener Test ist ehrlicher als eine erzwungene
        Kopplung an einen Hostpfad. Der taegliche Rundgang
        `sync_schema_to_repo.py --check` faengt die Faelle, in denen hier uebersprungen
        wird.
        """
        kanon = Path.home() / "OneDrive" / ".TOPICS" / ".AI" / ".MODULES" / "_templates" / SCHEMA.name
        if not kanon.is_file():
            self.skipTest(f"kanonisches Schema auf diesem Host nicht erreichbar: {kanon}")
        pin = json.loads(PIN.read_text(encoding="utf-8"))
        self.assertEqual(
            pin["sha256"], _hash(kanon),
            "Das kanonische Schema ist weitergezogen, diese Kopie nicht. Neu synchronisieren: "
            "python <MODULES>/_scripts/sync_schema_to_repo.py --repo <dieses Repo>",
        )


if __name__ == "__main__":
    unittest.main()
