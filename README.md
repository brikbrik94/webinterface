# Lokales Service-Webinterface

Dieses Projekt stellt die Grundlage für ein lokales Webinterface bereit, mit dem Dienste wie OpenRouteService (ORS) oder das Fastest-Responding-Projekt überwacht und gesteuert werden können.

## Struktur

```
backend/               # FastAPI-Backend mit Service-Adaptern
  app.py               # Einstiegspunkt für die API
  config/loader.py     # YAML-Konfigurationslader
  services/            # Adapter-Schnittstelle und Implementierungen
  system/              # Helfer zur systemd-Erkennung
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
   python -m backend
   ```
   Der Prozess lauscht standardmäßig auf `0.0.0.0:8000` und ist somit aus dem lokalen
   Netzwerk erreichbar. Über die Umgebungsvariablen `WEB_HOST`, `WEB_PORT` und
   `WEB_RELOAD` (z. B. `WEB_RELOAD=1 python -m backend`) lässt sich das Verhalten
   anpassen. Alternativ kann weiterhin `uvicorn backend.app:app --reload --host 0.0.0.0`
   verwendet werden.
3. API testen:
   - `GET /services` listet alle konfigurierten Dienste.
   - `GET /services/status` liefert eine Statusübersicht für alle Dienste.
   - `GET /services/{key}` liefert Statusinformationen zu einem einzelnen Dienst.
   - `GET /systemd/services` gibt eine vollständige Liste der systemd-Services des Hosts zurück.
   - `POST /systemd/services/status` erwartet eine `units`-Liste und liefert den aktuellen `systemctl`-Status.
   - `GET /systemd/services/{unit}/journal` gibt die letzten Journal-Einträge einer Unit zurück (standardmäßig 200 Zeilen).

## Weboberfläche

Nach dem Start von Uvicorn steht unter [http://localhost:8000/ui/](http://localhost:8000/ui/) eine Startseite bereit, die
alle konfigurierten Dienste samt Status- und Systemctl-Zusammenfassung anzeigt. Über einen Klick auf einen Eintrag gelangt
man zur Detailansicht unter `service.html?key=<dienst>`, die alle 15 Sekunden den ausgewählten Dienst aktualisiert und neben
dem Roh-Output auch Metadaten wie das ORS-Konfigurationsverzeichnis (`/var/lib/ors`) darstellt. Wenn für einen Dienst eine
systemd-Unit bekannt ist (bei reinen systemd-Einträgen automatisch, sonst über `metadata.systemd_unit`), blendet die Detail-
seite zusätzlich die letzten `journalctl`-Meldungen ein, um Fehlerursachen schnell nachvollziehen zu können.

Über den Link „Anzeige konfigurieren“ gelangt man zur Seite `settings.html`. Dort lassen sich
zum einen die in der YAML konfigurierten Dienste per Checkbox ein- oder ausblenden; ohne
Auswahl erscheinen sie automatisch alle im Dashboard. Zusätzlich listet die Seite sämtliche
systemd-Services des Hosts auf (`/systemd/services`) und erlaubt es, weitere Units auszuwählen,
die temporär im Dashboard erscheinen sollen. Die Auswahl wird lokal im Browser (Local Storage)
gespeichert. Ein Filter blendet auf Wunsch typische Systemdienste aus, sodass sich individuelle
Dienste (etwa `ais-catcher` oder `readsb`) leichter finden lassen.

Das Dashboard kombiniert anschließend beide Quellen: konfigurierte Dienste werden wie gewohnt
über `/services/status` geladen, zusätzlich ausgewählte systemd-Units werden über
`/systemd/services/status` abgefragt und mit reduzierten Metadaten (systemctl-Ausgabe,
Lade-/Aktiv-Status) angezeigt. In der Detailansicht (`service.html`) erkennt das UI automatisch,
ob ein Eintrag aus der YAML stammt oder direkt via systemd eingeblendet wurde.

### Beispiel: AIS-/ADS-B-Raspberry-Pi

Die Datei [`config/services.yaml`](config/services.yaml) enthält neben ORS weitere
Beispiele für die Überwachung eines Raspberry Pi mit AIS- und ADS-B-Feeds (u. a.
`adsbexchange-feed`, `ais-catcher`, `readsb`, `tar1090`). Passen Sie die Einträge bei
Bedarf an Hostnamen oder Dienstnamen Ihrer Installation an. Zusätzliche Metadaten wie
`host`, `category` oder `systemd_unit` werden im UI angezeigt und helfen bei der
Kategorisierung sowie beim automatischen Abruf der passenden Journaleinträge.

## Eigene Adapter hinzufügen

Eine detaillierte Beschreibung der Adapter-Schnittstelle befindet sich in [`docs/service_interface.md`](docs/service_interface.md). Kurzfassung:

1. Neue Adapterklasse in `backend/services/` anlegen und von `ServiceAdapter` ableiten.
2. Adapter im Paket registrieren (`registry.register("ihr-typ", IhreKlasse)`).
3. Adaptertyp und Parameter in `config/services.yaml` hinterlegen.

## Nächste Schritte

- Weitere Frontend-Seiten oder Framework-gestützte Oberflächen hinzufügen.
- Authentifizierung für den Zugang zum Webinterface ergänzen.
- Spezialisierte Adapter für systemd (DBus), Docker oder benutzerdefinierte Skripte implementieren.
