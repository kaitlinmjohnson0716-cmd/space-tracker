"""The sources and how they are downloaded."""
import json
import time
import urllib.request
from datetime import date as _date, timedelta

BASE = "https://ll.thespacedevs.com/2.2.0/"
USER_AGENT = "space-tracker (student project)"


def source_urls(date):
    """Only the part we track is requested: launches in the next 60 days
    (so launches_next_30d is complete) and people currently in space."""
    horizon = (_date.fromisoformat(date) + timedelta(days=60)).isoformat()
    return {
        "launches": BASE + "launch/upcoming/?mode=list&limit=100&net__lte=" + horizon,
        "crew": BASE + "astronaut/?mode=list&limit=100&in_space=true",
    }


def fetch(url, tries=3, wait=(10, 30), timeout=30):
    """Download url and return the body bytes; retry on failure."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
            json.loads(body)  # must be valid JSON to count as a success
            return body
        except Exception as exc:
            last = exc
            if attempt < tries - 1:
                time.sleep(wait[min(attempt, len(wait) - 1)])
    raise last
