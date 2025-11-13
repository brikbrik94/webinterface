# Service Adapter Interface

Dieses Dokument beschreibt die Schnittstelle, die alle Dienst-Adapter implementieren müssen, um in das Webinterface integriert zu werden.

## Überblick

Ein Adapter kapselt die Interaktion mit einem spezifischen Ausführungsumfeld (z. B. systemd, Docker, Kubernetes oder ein eigenes Skript). Das Backend arbeitet ausschließlich gegen die abstrakte Schnittstelle `ServiceAdapter` und erhält so ein einheitliches Datenmodell für alle Dienste.

```python
class ServiceAdapter(abc.ABC):
    key: str
    name: str
    metadata: Mapping[str, Any]

    def __init__(self, key: str, name: str, metadata: Optional[Mapping[str, Any]] = None):
        ...

    @abc.abstractmethod
    def fetch_state(self) -> ServiceState:
        """Ermittelt den aktuellen Status des Dienstes."""

    def start(self) -> None:
        """Optionaler Hook zum Starten des Dienstes."""

    def stop(self) -> None:
        """Optionaler Hook zum Stoppen des Dienstes."""

    def restart(self) -> None:
        """Optionaler Hook zum Neustarten des Dienstes."""
```

Der `ServiceState` ist ein einfaches Datenobjekt:

```python
@dataclass
class ServiceState:
    status: str
    details: Mapping[str, Any]
```

- `status`: Symbolischer Zustand (z. B. `ok`, `error`, `starting`, `unknown`).
- `details`: Beliebige Zusatzinformationen, die an das Frontend weitergegeben werden.

## Lebenszyklus eines Adapters

1. **Konfiguration laden:** Beim Start liest das Backend `config/services.yaml` ein und ermittelt anhand des Felds `adapter`, welche Implementierung verwendet werden soll.
2. **Initialisierung:** Jeder Adapter erhält `key`, `name`, optionale `metadata` sowie zusätzliche Parameter aus der Konfiguration (z. B. Kommandos, Ports, Credentials).
3. **Statusabfrage:** Das Backend ruft `fetch_state()` auf, um Statusinformationen zu sammeln.
4. **Aktionen:** Falls das Frontend später Buttons für Start/Stop/Restart anbietet, werden die entsprechenden Methoden aufgerufen.

## Eigene Adapter implementieren

1. **Neues Modul anlegen:** Legen Sie z. B. `backend/services/systemd.py` an.
2. **Klasse ableiten:** Erstellen Sie eine Klasse, die von `ServiceAdapter` erbt und alle relevanten Methoden implementiert.
3. **Registrieren:** Importieren Sie die Klasse im Paket `backend.services` und registrieren Sie sie über `registry.register("ihr-adapter", IhreKlasse)`, damit sie über die Konfiguration gefunden wird.
4. **Konfiguration erweitern:** Tragen Sie den neuen Adaptertypen und die benötigten Parameter in `config/services.yaml` ein.

## Beispiel: CommandService

Der mitgelieferte `CommandService`-Adapter führt Shell-Kommandos aus, die in der Konfiguration hinterlegt sind.

```yaml
services:
  - key: readsb
    name: readsb Receiver
    adapter: command
    commands:
      start: "systemctl start readsb.service"
      stop: "systemctl stop readsb.service"
      status: "systemctl status --no-pager readsb.service"
    metadata:
      host: "ais-adsb"
      category: "ADS-B"
      description: "Primary ADS-B decoder providing data to feeder services."
```

Die Schlüssel `start`, `stop`, `restart`, `status` sind optional, wobei mindestens `start` definiert sein sollte, damit der Dienst gestartet werden kann. `status` ermöglicht eine Zustandsanzeige. Weitere Metadaten können in `metadata` abgelegt werden und stehen dem Adapter als freies Dictionary zur Verfügung. Diese Werte erscheinen auch im UI (z. B. `host`, `category`, `description`).

Der Standard-`CommandService` erzeugt neben der rohen Kommandoausgabe auch eine aufbereitete Zusammenfassung, sofern die Ausgabe einem `systemctl status` ähnelt. Zeilen mit `Active:`, `Loaded:`, `Main PID:`, `Tasks:`, `Memory:` und `CPU:` werden herausgefiltert und unter `details.systemctl` zurückgeliefert, sodass Frontends die wichtigsten Kennzahlen ohne weiteres Parsen anzeigen können.

## Systemd-Erkennung für die UI

Zusätzlich zur YAML-Konfiguration stellt das Backend Hilfsfunktionen bereit, um alle systemd-Dienste des Hosts dynamisch zu erfassen:

- `backend/system/systemd.py` enthält die Funktionen `list_systemd_services()` sowie `service_states_for_units()`. Erstere liefert eine vollständige Liste aller Units samt Beschreibung, Lade-/Aktiv-Status und einer heuristischen Kennzeichnung, ob es sich um einen typischen Systemdienst handelt. Letztere ruft für eine Menge von Units `systemctl status` auf und gibt eine reduzierte Struktur mit `output` und `systemctl`-Zusammenfassung zurück.
- Die FastAPI-Endpunkte `GET /systemd/services` und `POST /systemd/services/status` kapseln diese Funktionen und versorgen das Frontend mit den Daten für die Konfigurationsseite.

Die UI speichert ausgewählte systemd-Units im Browser (Local Storage) und kombiniert sie auf dem Dashboard mit den statisch konfigurierten Diensten. Für dauerhaftes Monitoring empfiehlt es sich dennoch, relevante Dienste in `config/services.yaml` zu übernehmen, damit Metadaten und Kommandos konsistent hinterlegt sind.

## Erweiterungsmöglichkeiten

- **Authentifizierung:** Adapter können zusätzliche Parameter erwarten (z. B. API-Tokens). Diese werden im YAML unterhalb eines eigenen Schlüssels gespeichert.
- **Mehrstufige Statusabfragen:** `fetch_state()` kann komplexe Logik enthalten, z. B. das Parsen von JSON oder den Aufruf externer APIs.
- **Asynchrone Operationen:** Für Adapter mit langsamen Aufrufen kann `fetch_state()` asynchron gestaltet werden. FastAPI unterstützt `async def`-Handler; der Adapter kann dann `async`-Methoden bereitstellen, solange die Schnittstelle entsprechend erweitert wird.

Mit dieser Struktur lassen sich neue Dienste einfach integrieren, indem lediglich ein neues Adaptermodul und die zugehörige Konfiguration hinzugefügt werden.
