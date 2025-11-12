# Lokales Service-Webinterface

Dieses Projekt stellt die Grundlage für ein lokales Webinterface bereit, mit dem Dienste wie OpenRouteService (ORS) oder das Fastest-Responding-Projekt überwacht und gesteuert werden können.

## Struktur

```
backend/               # FastAPI-Backend mit Service-Adaptern
  app.py               # Einstiegspunkt für die API
  config/loader.py     # YAML-Konfigurationslader
  services/            # Adapter-Schnittstelle und Implementierungen
frontend/              # Statisches UI mit Übersichts-, Detail- und Konfigurationsseite
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
   - `GET /services/status` liefert eine Statusübersicht für alle Dienste.
   - `GET /services/{key}` liefert Statusinformationen zu einem einzelnen Dienst.

## Weboberfläche

Nach dem Start von Uvicorn steht unter [http://localhost:8000/ui/](http://localhost:8000/ui/) eine Startseite bereit, die
alle konfigurierten Dienste samt Status- und Systemctl-Zusammenfassung anzeigt. Über einen Klick auf einen Eintrag gelangt
man zur Detailansicht unter `service.html?key=<dienst>`, die alle 15 Sekunden den ausgewählten Dienst aktualisiert und neben
dem Roh-Output auch Metadaten wie das ORS-Konfigurationsverzeichnis (`/var/lib/ors`) darstellt.

Über den Link „Anzeige konfigurieren“ gelangt man zur Seite `settings.html`. Dort lässt sich per Checkbox pro Dienst festlegen,
welche Einträge auf dem Dashboard erscheinen sollen. Die Auswahl wird im Browser (Local Storage) gespeichert; ohne Auswahl
werden automatisch alle Dienste angezeigt.

## Eigene Adapter hinzufügen

Eine detaillierte Beschreibung der Adapter-Schnittstelle befindet sich in [`docs/service_interface.md`](docs/service_interface.md). Kurzfassung:

1. Neue Adapterklasse in `backend/services/` anlegen und von `ServiceAdapter` ableiten.
2. Adapter im Paket registrieren (`registry.register("ihr-typ", IhreKlasse)`).
3. Adaptertyp und Parameter in `config/services.yaml` hinterlegen.

## Nächste Schritte

- Weitere Frontend-Seiten oder Framework-gestützte Oberflächen hinzufügen.
- Authentifizierung für den Zugang zum Webinterface ergänzen.
- Spezialisierte Adapter für systemd (DBus), Docker oder benutzerdefinierte Skripte implementieren.
