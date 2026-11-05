"""Convert each raw source into rows with the common history columns."""
import gzip
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

COLUMNS = [
    "date", "item_id", "item", "source", "kind", "group",
    "launches_next_7d", "launches_next_30d", "days_to_next_launch",
    "days_in_space", "eva_hours",
]

_DURATION = re.compile(
    r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$"
)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def duration_days(text):
    """ISO-8601 duration such as P204DT23H44M34S -> days (float)."""
    m = _DURATION.match(text or "")
    if not m:
        return None
    d, h, mi, s = (float(x) if x else 0.0 for x in m.groups())
    return d + h / 24 + mi / 1440 + s / 86400


def _base(date, item_id, item, source, kind, group):
    row = dict.fromkeys(COLUMNS, "")
    row.update(date=date, item_id=item_id, item=item, source=source,
               kind=kind, group=group)
    return row


def convert_launches(data, date):
    """One row per launch provider with upcoming launches.

    Launch distances are measured from 00:00 UTC of the raw file's date, so
    the result depends only on the raw file and its folder date.
    """
    day0 = datetime.fromisoformat(date + "T00:00:00+00:00")
    by_provider = defaultdict(list)
    for r in data.get("results", []):
        net = datetime.fromisoformat(r["net"].replace("Z", "+00:00"))
        delta = (net - day0).total_seconds() / 86400
        if delta < 0:
            continue
        country = (r.get("location") or "").split(",")[-1].strip()
        by_provider[r["lsp_name"]].append((delta, country))
    rows = []
    for name, launches in by_provider.items():
        deltas = [d for d, _ in launches]
        countries = Counter(c for _, c in launches if c)
        group = countries.most_common(1)[0][0] if countries else ""
        row = _base(date, "provider:" + slug(name), name, "launches",
                    "provider", group)
        row["launches_next_7d"] = sum(d < 7 for d in deltas)
        row["launches_next_30d"] = sum(d < 30 for d in deltas)
        row["days_to_next_launch"] = round(min(deltas), 2)
        rows.append(row)
    return rows


def convert_crew(data, date):
    """One row per human currently in space (non-human 'astronauts' dropped)."""
    rows = []
    for r in data.get("results", []):
        if (r.get("type") or {}).get("name") == "Non-Human":
            continue
        row = _base(date, "astro:%s" % r["id"], r["name"], "crew",
                    "astronaut", r.get("agency") or "")
        days = duration_days(r.get("time_in_space"))
        eva = duration_days(r.get("eva_time"))
        row["days_in_space"] = "" if days is None else round(days, 2)
        row["eva_hours"] = "" if eva is None else round(eva * 24, 2)
        rows.append(row)
    return rows


CONVERTERS = {"launches": convert_launches, "crew": convert_crew}


def read_raw(path):
    with gzip.open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))
