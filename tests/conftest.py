import json
import pytest


def launch(name, net, location="Cape Canaveral, FL, USA"):
    return {"lsp_name": name, "net": net, "location": location}


@pytest.fixture
def launches_json():
    return {"results": [
        launch("SpaceX", "2026-11-05T10:00:00Z"),
        launch("SpaceX", "2026-11-09T10:00:00Z"),
        launch("SpaceX", "2026-12-20T10:00:00Z"),
        launch("Rocket Lab", "2026-11-20T00:00:00Z", "Mahia, New Zealand"),
        launch("Old Co", "2026-11-04T23:00:00Z"),  # before the run day: ignored
    ]}


@pytest.fixture
def crew_json():
    return {"results": [
        {"id": 1, "name": "Ann Astro", "type": {"name": "Government"},
         "agency": "NASA", "time_in_space": "P10DT12H", "eva_time": "PT6H30M"},
        {"id": 2, "name": "Starman", "type": {"name": "Non-Human"},
         "agency": "SpaceX", "time_in_space": "P3000D", "eva_time": "P0D"},
        {"id": 3, "name": "Bo Cosmo", "type": {"name": "Government"},
         "agency": "ROSCOSMOS", "time_in_space": "P1D", "eva_time": "P0D"},
    ]}


def make_fetcher(launches, crew, fail=()):
    def fetch(url):
        name = "launches" if "launch/upcoming" in url else "crew"
        if name in fail:
            raise RuntimeError("boom")
        return json.dumps(launches if name == "launches" else crew).encode()
    return fetch
