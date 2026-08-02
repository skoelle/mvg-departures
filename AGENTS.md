# AGENTS.md — Richtlinien für KI-Agenten

## Projekt-Kontext

MVG Departures Monitor: FastAPI-App für Münchner U-/S-Bahn-Abfahrtsanzeige. Mobile-optimiert, Docker-fähig, Config via YAML.

## Wichtige Dateien

| Datei | Zweck |
|---|---|
| `app/main.py` | FastAPI-App, Endpunkte, Caching, MVG-API-Aufrufe |
| `app/config.py` | Config-Loader: YAML → Dataclasses |
| `app/templates/index.html` | Jinja2-HTML-Template (Mobile-UI) |
| `config.yaml` | Stationskonfiguration (User-Input) |
| `requirements.txt` | Python-Dependencies |
| `Dockerfile` | Container-Build |
| `.github/workflows/build.yml` | CI/CD |

## Code-Conventions

- **Sprache**: Englisch im Code, Deutsch in UI/Comments (nur wo nötig)
- **Typisierung**: Python Dataclasses für Config, `typing.List`, `typing.Dict`
- **Caching**: In-memory Dicts, kein externes Tool (Redis etc.)
- **Logging**: `logging.getLogger("mvg-departures")`
- **Naming**: snake_case (Python), camelCase (HTML/CSS-Klassen)
- **Keine Comments**: Nur wenn explizit angefordert

## Entwicklung

### Starten

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Testen

Kein Test-Framework vorhanden. Bei Änderungen:
1. Manuell testen: `curl http://localhost:8000/api/departures`
2. HTML-Visualcheck: Browser `http://localhost:8000/`
3. Docker-Build prüfen: `docker build -t mvg-departures .`

### Linting

Kein Linter konfiguriert. Bei Bedarf: `ruff check app/` oder `black app/`

## Architektur-Entscheidungen

1. **Ein-Datei-App**: `main.py` enthält alle Endpunkte und Logik → bewusst simpel gehalten
2. **Keine DB**: Alles In-Memory → Neustart = Cache-Verlust (akzeptabel)
3. **Exclude-Filter**: Blacklist-Logik (alles anzeigen AUSSER exclude_destinations)
4. **Template-Rendering**: Server-seitig via Jinja2, kein Frontend-Framework
5. **Config-Pfad**: `CONFIG_PATH` Env-Var oder `config.yaml` als Fallback

## Typische Änderungen

### Neue Station hinzufügen
→ Nur `config.yaml` editieren, kein Code nötig

### Neuen Transporttyp hinzufügen
→ `TYPE_MAP` und `ICON_MAP` in `main.py` erweitern, CSS-Klasse `.icon-X` in `index.html` hinzufügen

### API-Endpoint ändern
→ Nur `app/main.py`, Funktionen `api_departures()` oder `index()`

### UI anpassen
→ Nur `app/templates/index.html` (inline CSS)

## Sicherheit

- Keine Secrets im Code
- Config.yaml kann sensitive Stationsnamen enthalten → in Produktion als Read-Only-Volume-Mount überschreiben; das Image enthält nur eine Default-Config
- GHCR-Token nur in CI, nie im Repo

## Deployment-Hinweise

- Immer `TZ=Europe/Berlin` setzen (MVG-API liefert Münchner Zeit)
- Config.yaml als Read-Only-Volume mounten
- Healthcheck auf `/healthz` verwenden
- Watchtower kompatibel: Image-Tag `latest` + SHA
