"""usmc:// ist ein Nicht-Dateisystem-Schema wie chat:// (2026-09-05).

Ohne diese Behandlung landeten die sechs usmc-promotion-Eintraege in verify()
als "missing" und hielten das Gesamtflag "ok" dauerhaft auf False.
"""
from policy_registry.model import expand_uri


def test_nicht_dateisystem_schemata_liefern_none():
    for uri in ("http://x/y", "https://x/y", "git+ssh://x/y", "chat://x", "usmc://facts/no-foreign-code"):
        assert expand_uri(uri) is None, uri


def test_pfade_liefern_weiterhin_einen_pfad():
    assert expand_uri("~/irgendwo/datei.md") is not None
