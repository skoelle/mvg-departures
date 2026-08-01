# SPEC.md — MVG Departures Monitor

## 1. Überblick

Kompakter Abfahrtsmonitor für Münchner U-Bahn- und S-Bahn-Abfahrten. Primär für mobile Nutzung optimiert. Baut auf der öffentlichen MVG-API auf.

## 2. Architektur

```
mvg-departures/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI-App, Endpunkte, Caching
│   ├── config.py          # Config-Loader (YAML → Dataclasses)
│   └── templates/
│       └── index.html     # Jinja2-Template (mobile HTML-Ansicht)
├── config.yaml            # Stationskonfiguration
├── requirements.txt       # Python-Dependencies
├── Dockerfile             # Multi-Stage Build (python:3.12-slim)
├── docker-compose.yml     # Deployment-Beispiel
└── .github/workflows/
    └── build.yml          # CI/CD: Docker-Build + GHCR-Push
```

## 3. Technologie-Stack

| Komponente | Technologie |
|---|---|
| Runtime | Python 3.12 |
| Web-Framework | FastAPI |
| Templating | Jinja2 |
| API-Client | `mvg` (PyPI) |
| Config | YAML (`pyyaml`) |
| Server | Uvicorn |
| Container | Docker (python:3.12-slim) |
| CI/CD | GitHub Actions → GHCR |

## 4. Datenfluss

```
config.yaml
    ↓
load_config() → AppConfig (Dataclass)
    ↓
Für jede Station:
    resolve_station_id(name) → station_id (mit Memory-Cache)
    ↓
MvgApi(station_id).departures(limit, transport_types)
    ↓
Filter: exclude_destinations (exakter Stringvergleich)
    ↓
Berechnung: delay_min, format time_str
    ↓
In-memory Cache (cache_seconds)
    ↓
Response: JSON oder HTML-Template
```

## 5. Endpunkte

| Route | Methode | Beschreibung |
|---|---|---|
| `/` | GET | Mobile HTML-Ansicht, Auto-Refresh alle 60s |
| `/api/departures` | GET | JSON-Liste aller gefilterten Abfahrten |
| `/healthz` | GET | Healthcheck (`{"status": "ok"}`) |

## 6. Konfiguration (`config.yaml`)

```yaml
refresh_seconds: 60          # Meta-Refresh-Intervall (HTML)
cache_seconds: 20            # API-Cache pro Station
departures_limit: 10         # Max. Abfahrten pro Station

stations:
  - name: "Station Name, München"
    type: "UBAHN"            # UBAHN | SBAHN | TRAM | BUS
    exclude_destinations:    # Exakter Stringvergleich
      - "Zielstation"
```

### Filter-Logik

- `exclude_destinations` filtert per exaktem `destination`-Stringvergleich
- Alles, was NICHT in der Liste steht, wird angezeigt
- Neue/unbekannte Ziele erscheinen automatisch → keine lautlos verschwundenen Linienänderungen

## 7. Caching

- **Station-ID-Cache**: Globales Dict `_station_id_cache`, lifetime=Session
- **Departures-Cache**: Pro Station+Typ, TTL=`cache_seconds` (Standard: 20s)
- Kein Persistence-Layer → Cache geht bei Neustart verloren

## 8. UI

- Dunkles Theme (`#111417` Background)
- Farbliche Unterscheidung: U-Bahn (blau `#005ca9`), S-Bahn (grün `#00933b`), Tram (rot `#e2001a`), Bus (grau `#55545a`)
- Anzeige: Linie, Ziel, Abfahrtszeit, Verspätung (gelb/rot), Entfall, Störungsmeldungen
- Responsive, für Smartphone-First optimiert

## 9. Deployment

- **Lokal**: `uvicorn app.main:app --reload`
- **Docker**: `docker run -p 8000:8000 -v $(pwd)/config.yaml:/app/config.yaml mvg-departures`
- **Production**: Docker-Image von GHCR, Config via Volume-Mount, TZ=Europe/Berlin
- **Healthcheck**: Uvicorn-Endpoint `/healthz` (30s Interval)

## 10. CI/CD

- Trigger: Push auf `main`
- Build: Docker-Image → `ghcr.io/<owner>/<repo>:latest` + Short-SHA-Tag
- Cleanup: Behält nur letzte 4 Image-Versionen
- Voraussetzung: Repo-Actions Permissions auf "Read and write"

## 11. MVG-API

- Basis: `https://www.mvg.de/api/bgw-pt/v3/`
- Station-Lookup: `/locations?query=<name>`
- Abfahrten: `/departures?globalId=<id>&limit=<n>&transportTypes=<type>`
- Auth: Keine (öffentlich)

## 12. Einschränkungen

- Kein WebSocket/Live-Updates → nur periodischer Refresh
- Keine persistenten Daten → Cache geht bei Restart verloren
- Kein Test-Suite vorhanden
- Kein Rate-Limiting auf Client-Seite
- Ein `config.yaml` pro Deployment (kein Multi-Tenancy)
