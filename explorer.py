"""Data loading and algorithms for the AustLang Explorer app."""

from __future__ import annotations

import csv
import math
from pathlib import Path


REQUIRED = {"code", "name", "alternate_names", "state_territory", "latitude", "longitude", "source_url"}


def load_records(path: str | Path) -> list[dict]:
    """Load and validate a published-data snapshot, keeping missing locations explicit."""
    with open(path, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError("Dataset is missing required columns")
        records = []
        codes = set()
        for row in reader:
            code = (row["code"] or "").strip()
            name = (row["name"] or "").strip()
            if not code or not name or code in codes:
                continue
            codes.add(code)
            lat, lon = _coordinates(row["latitude"], row["longitude"])
            records.append({
                "code": code,
                "name": name,
                "alternate_names": (row["alternate_names"] or "").strip(),
                "regions": tuple(part.strip().upper() for part in (row["state_territory"] or "").split(",") if part.strip()),
                "latitude": lat,
                "longitude": lon,
                "source_url": (row["source_url"] or "").strip(),
            })
    if len(records) < 200:
        raise ValueError(f"Dataset has {len(records)} valid records; at least 200 required")
    return records


def _coordinates(lat_text: str, lon_text: str) -> tuple[float | None, float | None]:
    try:
        lat, lon = float(lat_text), float(lon_text)
    except (TypeError, ValueError):
        return None, None
    if not (-45 <= lat <= -9 and 110 <= lon <= 155):
        return None, None
    return lat, lon


def search(records: list[dict], query: str = "", region: str = "All", limit: int = 100) -> list[dict]:
    """Rank code/name matches above alternate-name matches, then sort consistently."""
    words = query.casefold().strip().split()
    if limit < 1:
        return []
    ranked = []
    for record in records:
        if region != "All" and region not in record["regions"]:
            continue
        code = record["code"].casefold()
        name = record["name"].casefold()
        aliases = record["alternate_names"].casefold()
        if not all(word in f"{code} {name} {aliases}" for word in words):
            continue
        score = 0 if not words else sum(
            4 if code == word else 3 if name.startswith(word) else 2 if word in name else 1
            for word in words
        )
        ranked.append((-score, record["name"].casefold(), record["code"], record))
    ranked.sort(key=lambda item: item[:3])
    return [item[3] for item in ranked[:limit]]


def region_counts(records: list[dict]) -> dict[str, int]:
    """Count each record once in every region listed by the source."""
    counts: dict[str, int] = {}
    for record in records:
        for region in set(record["regions"]):
            counts[region] = counts.get(region, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    a1, a2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = a2 - a1, math.radians(lon2 - lon1)
    value = math.sin(dlat / 2) ** 2 + math.cos(a1) * math.cos(a2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(max(0, 1 - value)))


def nearest(records: list[dict], latitude: float, longitude: float, limit: int = 10) -> list[tuple[dict, float]]:
    """Find nearest published approximate points; this does not identify Country."""
    if not (-45 <= latitude <= -9 and 110 <= longitude <= 155):
        raise ValueError("Choose a point within the supported Australian coordinate range")
    if limit < 1:
        return []
    matches = [
        (record, haversine_km(latitude, longitude, record["latitude"], record["longitude"]))
        for record in records if record["latitude"] is not None and record["longitude"] is not None
    ]
    matches.sort(key=lambda item: (item[1], item[0]["name"].casefold()))
    return matches[:limit]
