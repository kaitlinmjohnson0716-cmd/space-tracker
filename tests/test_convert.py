from tracker.convert import (COLUMNS, convert_crew, convert_launches,
                             duration_days, slug)


def test_slug():
    assert slug("Avio S.p.A") == "avio-s-p-a"


def test_duration_days():
    assert duration_days("P10DT12H") == 10.5
    assert duration_days("PT6H30M") == 6.5 / 24
    assert duration_days("P0D") == 0
    assert duration_days("garbage") is None


def test_launches_columns_and_counts(launches_json):
    rows = {r["item_id"]: r for r in convert_launches(launches_json, "2026-11-05")}
    assert set(rows) == {"provider:spacex", "provider:rocket-lab"}
    s = rows["provider:spacex"]
    assert list(s) == COLUMNS
    assert s["launches_next_7d"] == 2      # Nov 5 and Nov 9 are within 7 days
    assert s["launches_next_30d"] == 2
    assert s["days_to_next_launch"] == 0.42
    assert s["group"] == "USA"
    assert s["kind"] == "provider" and s["source"] == "launches"
    assert rows["provider:rocket-lab"]["group"] == "New Zealand"


def test_launch_window_counts(launches_json):
    rows = {r["item_id"]: r for r in convert_launches(launches_json, "2026-11-05")}
    # Nov 5 and Nov 9 are both inside 7 days
    assert rows["provider:spacex"]["launches_next_7d"] == 2
    assert rows["provider:spacex"]["launches_next_30d"] == 2


def test_crew_drops_non_humans(crew_json):
    rows = convert_crew(crew_json, "2026-11-05")
    assert [r["item"] for r in rows] == ["Ann Astro", "Bo Cosmo"]
    a = rows[0]
    assert a["item_id"] == "astro:1" and a["group"] == "NASA"
    assert a["days_in_space"] == 10.5 and a["eva_hours"] == 6.5
    assert a["launches_next_30d"] == ""
