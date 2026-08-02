"""Config-Loader für die Stationsliste aus config.yaml."""
import os
import yaml
from dataclasses import dataclass, field
from typing import List


@dataclass
class StationConfig:
    name: str
    type: str  # UBAHN | SBAHN | TRAM | BUS
    exclude_destinations: List[str] = field(default_factory=list)


@dataclass
class AppConfig:
    refresh_seconds: int
    cache_seconds: int
    departures_limit: int
    stations: List[StationConfig]


def load_config(path: str = None) -> AppConfig:
    path = path or os.environ.get("CONFIG_PATH", "config.yaml")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    stations = [
        StationConfig(
            name=s["name"],
            type=s["type"].upper(),
            exclude_destinations=s.get("exclude_destinations", []) or [],
        )
        for s in raw.get("stations", [])
    ]

    return AppConfig(
        refresh_seconds=int(raw.get("refresh_seconds", 60)),
        cache_seconds=int(raw.get("cache_seconds", 20)),
        departures_limit=int(raw.get("departures_limit", 10)),
        stations=stations,
    )
