# Lokales Service-Webinterface

Dieses Projekt stellt die Grundlage für ein lokales Webinterface bereit, mit dem Dienste wie OpenRouteService (ORS) oder das Fastest-Responding-Projekt überwacht und gesteuert werden können.

## Struktur

```
backend/               # FastAPI-Backend mit Service-Adaptern
  app.py               # Einstiegspunkt für die API
  config/loader.py     # YAML-Konfigurationslader
  services/            # Adapter-Schnittstelle und Implementierungen
config/services.yaml   # Beispielkonfiguration für Dienste
docs/service_interface.md # Detaillierte Schnittstellenbeschreibung
```

## Voraussetzungen

- Python 3.11+
- `pip` oder `uv` zum Installieren von Abhängigkeiten

## Installation

1. Virtuelle Umgebung anlegen (optional, aber empfohlen):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Abhängigkeiten installieren:
   ```bash
   pip install fastapi uvicorn pyyaml
   ```

## Entwicklung

1. Konfiguration anpassen: Bearbeiten Sie `config/services.yaml` und tragen Sie Ihre Dienste, Adaptertypen und Kommandos ein.
2. Server starten:
   ```bash
   uvicorn backend.app:app --reload
   ```
3. API testen:
   - `GET /services` listet alle konfigurierten Dienste.
   - `GET /services/{key}` liefert Statusinformationen zu einem Dienst.

## Eigene Adapter hinzufügen

Eine detaillierte Beschreibung der Adapter-Schnittstelle befindet sich in [`docs/service_interface.md`](docs/service_interface.md). Kurzfassung:

1. Neue Adapterklasse in `backend/services/` anlegen und von `ServiceAdapter` ableiten.
2. Adapter im Paket registrieren (`registry.register("ihr-typ", IhreKlasse)`).
3. Adaptertyp und Parameter in `config/services.yaml` hinterlegen.

## Nächste Schritte

- Frontend hinzufügen (z. B. mit React, Vue oder HTMX) zur Visualisierung und Steuerung.
- Authentifizierung für den Zugang zum Webinterface ergänzen.
- Spezialisierte Adapter für systemd, Docker oder benutzerdefinierte Skripte implementieren.
