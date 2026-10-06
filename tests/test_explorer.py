import csv
from pathlib import Path

import pytest

from explorer import haversine_km, load_records, nearest, region_counts, search


DATA = Path(__file__).parents[1] / "data" / "austlang.csv"


@pytest.fixture(scope="module")
def records():
    return load_records(DATA)


def test_snapshot_meets_record_minimum(records):
    assert len(records) >= 200


def test_codes_are_unique(records):
    assert len({r["code"] for r in records}) == len(records)


def test_search_exact_code(records):
    assert search(records, "A1")[0]["code"] == "A1"


def test_search_is_case_insensitive(records):
    assert [r["code"] for r in search(records, "noongar")] == [r["code"] for r in search(records, "NOONGAR")]


def test_search_region_filter(records):
    assert all("WA" in r["regions"] for r in search(records, region="WA"))


def test_search_empty_limit(records):
    assert search(records, limit=0) == []


def test_region_counts_multi_tag():
    sample = [{"regions": ("WA", "SA")}, {"regions": ("WA",)}]
    assert region_counts(sample) == {"WA": 2, "SA": 1}


def test_distance_same_point_is_zero():
    assert haversine_km(-31.95, 115.86, -31.95, 115.86) == 0


def test_nearest_sorts_by_distance(records):
    result = nearest(records, -31.95, 115.86, 5)
    assert len(result) == 5
    assert [distance for _, distance in result] == sorted(distance for _, distance in result)


def test_nearest_rejects_out_of_range(records):
    with pytest.raises(ValueError):
        nearest(records, 0, 0)


def test_invalid_coordinates_are_missing(records):
    assert any(r["latitude"] is None and r["longitude"] is None for r in records)


def test_loader_rejects_incomplete_dataset(tmp_path):
    path = tmp_path / "small.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["code", "name", "alternate_names", "state_territory", "latitude", "longitude", "source_url"])
        writer.writeheader()
        writer.writerow({"code": "X1", "name": "Example"})
    with pytest.raises(ValueError, match="at least 200"):
        load_records(path)
