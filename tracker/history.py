"""Build data/history.csv from the raw files alone."""
import csv
import re
import sys
from pathlib import Path

from .convert import COLUMNS, CONVERTERS, read_raw

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def raw_dates(root):
    raw = Path(root) / "data" / "raw"
    if not raw.is_dir():
        return []
    return sorted(p.name for p in raw.iterdir()
                  if p.is_dir() and DATE_RE.match(p.name)
                  and any(p.glob("*.gz")))


def rows_for_day(root, date):
    rows = []
    for source, convert in CONVERTERS.items():
        path = Path(root) / "data" / "raw" / date / (source + ".json.gz")
        if not path.exists():
            continue  # no raw file, no rows from this source that day
        try:
            rows.extend(convert(read_raw(path), date))
        except Exception as exc:  # a corrupt file must not break the build
            print("skip %s: %s" % (path, exc), file=sys.stderr)
    return rows


def build_history(root):
    rows = []
    for date in raw_dates(root):
        rows.extend(rows_for_day(root, date))
    rows.sort(key=lambda r: (r["date"], r["item_id"]))
    out = Path(root) / "data" / "history.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return rows


def read_history(root):
    path = Path(root) / "data" / "history.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
