import csv
import json
from datetime import datetime, timezone

from conftest import make_fetcher
from tracker.history import build_history, raw_dates
from tracker.run import run


def at(day, hour=6):
    return datetime(2026, 11, day, hour, 0, 0, tzinfo=timezone.utc)


def do_run(root, launches, crew, day, hour=6, fail=()):
    return run(root, now=at(day, hour), fetcher=make_fetcher(launches, crew, fail),
               issue=False)


def read_rows(root):
    with open(root / "data" / "history.csv", newline="") as f:
        return list(csv.DictReader(f))


def test_first_run_files(tmp_path, launches_json, crew_json):
    st = do_run(tmp_path, launches_json, crew_json, 5)
    assert (tmp_path / "data/raw/2026-11-05/launches.json.gz").exists()
    assert (tmp_path / "data/raw/2026-11-05/crew.json.gz").exists()
    assert st["items"] == 4 and st["days_with_success"] == 1
    assert st["first_run_date"] == "2026-11-05"
    assert st["sources"] == [{"name": "launches", "ok": True, "count": 2},
                             {"name": "crew", "ok": True, "count": 2}]
    rows = read_rows(tmp_path)
    assert [(r["date"], r["item_id"]) for r in rows] == sorted(
        (r["date"], r["item_id"]) for r in rows)


def test_second_run_same_day_counts_once(tmp_path, launches_json, crew_json):
    do_run(tmp_path, launches_json, crew_json, 5, hour=6)
    first = (tmp_path / "data/history.csv").read_text()
    st = do_run(tmp_path, launches_json, crew_json, 5, hour=18)
    assert st["days_with_success"] == 1
    assert (tmp_path / "data/history.csv").read_text() == first
    assert len(raw_dates(tmp_path)) == 1


def test_second_run_replaces_that_days_data(tmp_path, launches_json, crew_json):
    do_run(tmp_path, launches_json, crew_json, 5, hour=6)
    launches_json["results"].append(
        {"lsp_name": "ISRO", "net": "2026-11-12T00:00:00Z", "location": "India"})
    st = do_run(tmp_path, launches_json, crew_json, 5, hour=18)
    ids = [r["item_id"] for r in read_rows(tmp_path)]
    assert "provider:isro" in ids and ids.count("provider:isro") == 1
    assert st["items"] == 5


def test_build_is_reproducible_from_raw(tmp_path, launches_json, crew_json):
    do_run(tmp_path, launches_json, crew_json, 5)
    do_run(tmp_path, launches_json, crew_json, 6)
    before = (tmp_path / "data/history.csv").read_bytes()
    (tmp_path / "data/history.csv").unlink()
    build_history(tmp_path)
    assert (tmp_path / "data/history.csv").read_bytes() == before


def test_failed_source_writes_no_raw_and_run_survives(tmp_path, launches_json, crew_json):
    st = do_run(tmp_path, launches_json, crew_json, 5, fail=("crew",))
    assert not (tmp_path / "data/raw/2026-11-05/crew.json.gz").exists()
    assert (tmp_path / "data/raw/2026-11-05/launches.json.gz").exists()
    crew = [s for s in st["sources"] if s["name"] == "crew"][0]
    assert crew == {"name": "crew", "ok": False, "count": 0}
    assert {r["source"] for r in read_rows(tmp_path)} == {"launches"}
    log = (tmp_path / "data/source_log.csv").read_text()
    assert "crew,false,0,boom" in log


def test_all_sources_failing_still_finishes(tmp_path, launches_json, crew_json):
    st = do_run(tmp_path, launches_json, crew_json, 5, fail=("crew", "launches"))
    assert st["items"] == 0 and st["days_with_success"] == 0
    assert st["first_run_date"] is None


def test_new_and_gone_between_days(tmp_path, launches_json, crew_json):
    do_run(tmp_path, launches_json, crew_json, 5)
    crew_json["results"].pop()                       # Bo leaves
    crew_json["results"].append(
        {"id": 9, "name": "Cy New", "type": {"name": "Government"},
         "agency": "ESA", "time_in_space": "P1D", "eva_time": "P0D"})
    st = do_run(tmp_path, launches_json, crew_json, 6)
    assert st["new_today"] == ["astro:9"]
    assert st["gone_today"] == ["astro:3"]
    assert st["days_with_success"] == 2


def test_issue_file_written_every_day(tmp_path, launches_json, crew_json):
    do_run(tmp_path, launches_json, crew_json, 5)
    do_run(tmp_path, launches_json, crew_json, 6)
    body = (tmp_path / "data/issue.md").read_text()
    assert body.startswith("# Space tracker: 2026-11-06")
    assert "SpaceX | 2 -> 1" in body      # the Nov 5 launch has passed


def test_issue_with_no_changes():
    from tracker.issue import build_issue
    status = {"run_time": "t", "items": 1, "days_with_success": 2,
              "sources": [{"name": "launches", "ok": False, "count": 0}]}
    body = build_issue("2026-11-07", status,
                       {"moves": [], "new": [], "gone": []})
    assert "No provider changed" in body and "FAILED" in body
