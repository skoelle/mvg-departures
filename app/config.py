# Copyright (c) 2026 Stefan Koelle (https://stefankoelle.de) - MIT License
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
class ProfileConfig:
    name: str
    stations: List[StationConfig] = field(default_factory=list)


@dataclass
class AppConfig:
    refresh_seconds: int
    cache_seconds: int
    departures_limit: int
    profiles: List[ProfileConfig]


def load_config(path: str = None) -> AppConfig:
    path = path or os.environ.get("CONFIG_PATH", "config.yaml")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    profiles = []
    for p in raw.get("profiles", []):
        stations = [
            StationConfig(
                name=s["name"],
                type=s["type"].upper(),
                exclude_destinations=s.get("exclude_destinations", []) or [],
            )
            for s in p.get("stations", [])
        ]
        profiles.append(ProfileConfig(name=p["name"], stations=stations))

    return AppConfig(
        refresh_seconds=int(raw.get("refresh_seconds", 60)),
        cache_seconds=int(raw.get("cache_seconds", 20)),
        departures_limit=int(raw.get("departures_limit", 10)),
        profiles=profiles,
    )
