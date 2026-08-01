"""MVG Departures Monitor - FastAPI App."""
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from mvg import MvgApi, TransportType

from app.config import load_config, StationConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mvg-departures")

app = FastAPI(title="MVG/S-Bahn Departures Monitor")
templates = Jinja2Templates(directory="app/templates")

config = load_config()

TYPE_MAP = {
    "UBAHN": TransportType.UBAHN,
    "SBAHN": TransportType.SBAHN,
    "TRAM": TransportType.TRAM,
    "BUS": TransportType.BUS,
}

ICON_MAP = {
    "UBAHN": "U",
    "SBAHN": "S",
    "TRAM": "T",
    "BUS": "B",
}

_station_id_cache: Dict[str, str] = {}
_departures_cache: Dict[str, Dict[str, Any]] = {}


def resolve_station_id(name: str) -> str:
    if name in _station_id_cache:
        return _station_id_cache[name]
    station = MvgApi.station(name)
    if not station:
        raise ValueError(f"Station nicht gefunden: {name}")
    _station_id_cache[name] = station["id"]
    return station["id"]


def fetch_departures_for_station(station_cfg: StationConfig) -> List[Dict[str, Any]]:
    cache_key = f"{station_cfg.name}:{station_cfg.type}"
    now = time.time()
    cached = _departures_cache.get(cache_key)
    if cached and (now - cached["ts"] < config.cache_seconds):
        return cached["data"]

    try:
        station_id = resolve_station_id(station_cfg.name)
        transport_type = TYPE_MAP.get(station_cfg.type)
        mvgapi = MvgApi(station_id)
        raw_departures = mvgapi.departures(
            limit=config.departures_limit,
            transport_types=[transport_type] if transport_type else None,
        )
    except Exception as exc:
        logger.exception("Fehler beim Abruf fuer Station %s", station_cfg.name)
        return []

    result = []
    for dep in raw_departures:
        destination = dep.get("destination", "")
        if destination in station_cfg.exclude_destinations:
            continue

        planned = dep.get("planned")
        actual = dep.get("time")
        delay_min = 0
        if planned and actual:
            delay_min = round((actual - planned) / 60)

        result.append({
            "station": station_cfg.name,
            "type": station_cfg.type,
            "icon": ICON_MAP.get(station_cfg.type, "?"),
            "line": dep.get("line", ""),
            "destination": destination,
            "time_epoch": actual,
            "time_str": datetime.fromtimestamp(actual).strftime("%H:%M") if actual else "",
            "delay_min": delay_min,
            "cancelled": dep.get("cancelled", False),
            "messages": dep.get("messages", []) or [],
        })

    _departures_cache[cache_key] = {"ts": now, "data": result}
    return result


def get_all_departures() -> List[Dict[str, Any]]:
    all_deps: List[Dict[str, Any]] = []
    for station_cfg in config.stations:
        all_deps.extend(fetch_departures_for_station(station_cfg))
    all_deps.sort(key=lambda d: d["time_epoch"] or 0)
    return all_deps


@app.get("/api/departures")
def api_departures():
    return JSONResponse(content={"departures": get_all_departures()})


@app.get("/")
def index(request: Request):
    departures = get_all_departures()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "departures": departures,
            "refresh_seconds": config.refresh_seconds,
            "generated_at": datetime.now().strftime("%H:%M:%S"),
        },
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
