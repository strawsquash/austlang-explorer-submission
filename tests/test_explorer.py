import csv
from pathlib import Path

import pytest

from explorer import compare_regions, haversine_km, load_records, nearest, region_counts, search


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


def test_compare_regions_counts_overlap_once():
    sample = [
        {"code": "A1", "regions": ("WA", "SA")},
        {"code": "A2", "regions": ("WA",)},
        {"code": "A3", "regions": ("SA",)},
    ]
    assert compare_regions(sample, "WA", "SA") == {
        "first_total": 2, "second_total": 2, "both": 1, "first_only": 1, "second_only": 1
    }


def test_compare_regions_rejects_same_region(records):
    with pytest.raises(ValueError):
        compare_regions(records, "WA", "WA")


def test_distance_same_point_is_zero():
    assert haversine_km(-31.95, 115.86, -31.95, 115.86) == 0


def test_nearest_sorts_by_distance(records):
    result = nearest(records, -31.95, 115.86, 5)
    assert len(result) == 5
    assert [distance for _, distance in result] == sorted(distance for _, distance in result)


def test_nearest_rejects_out_of_range(records):
    with pytest.raises(ValueError):
        nearest(records, 0, 0)


def test_nearest_excludes_missing_coordinates():
    sample = [
        {"code": "A1", "name": "With point", "latitude": -31.9, "longitude": 115.8},
        {"code": "A2", "name": "Without point", "latitude": None, "longitude": None},
    ]
    assert [r["code"] for r, _ in nearest(sample, -31.95, 115.86)] == ["A1"]


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


def test_loader_rejects_missing_required_column(tmp_path):
    path = tmp_path / "missing_url.csv"
    path.write_text("code,name,latitude,longitude\nX1,Example,-31.9,115.8\n", encoding="utf-8")
    with pytest.raises(ValueError, match="required columns"):
        load_records(path)


def test_search_ranks_exact_code_before_alias():
    sample = [
        {"code": "B2", "name": "Alpha", "alternate_names": "A1", "regions": ()},
        {"code": "A1", "name": "Zeta", "alternate_names": "", "regions": ()},
    ]
    assert [r["code"] for r in search(sample, "A1")] == ["A1", "B2"]
