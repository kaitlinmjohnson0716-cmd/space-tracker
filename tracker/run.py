"""Daily pipeline: download, save raw, rebuild history, status, issue."""
import argparse
import csv
import gzip
import sys
from datetime import datetime, timezone
from pathlib import Path

from .convert import CONVERTERS
from .history import build_history, raw_dates, read_history
from .issue import build_issue, publish_issue
from .moves import compute_moves
from .sources import fetch, source_urls
from .status import build_status, write_status

ROOT = Path(__file__).resolve().parent.parent
LOG_FIELDS = ["date", "run_time", "source", "ok", "count", "error"]


def save_raw(root, date, source, body):
    folder = Path(root) / "data" / "raw" / date
    folder.mkdir(parents=True, exist_ok=True)
    # mtime=0 makes the gzip bytes identical for identical content
    with open(folder / (source + ".json.gz"), "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            gz.write(body)


def append_log(root, date, run_time, results):
    path = Path(root) / "data" / "source_log.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(LOG_FIELDS)
        for r in results:
            w.writerow([date, run_time, r["name"], str(r["ok"]).lower(),
                        r["count"], r["error"]])


def run(root=ROOT, now=None, fetcher=fetch, issue=True):
    now = now or datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    run_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []
    for name, url in source_urls(date).items():
        try:
            body = fetcher(url)
            save_raw(root, date, name, body)  # replaces today's file
            results.append({"name": name, "ok": True, "count": 0, "error": ""})
        except Exception as exc:  # one failing source must not stop the run
            results.append({"name": name, "ok": False, "count": 0,
                            "error": str(exc)[:200]})
    rows = build_history(root)
    for r in results:
        r["count"] = sum(1 for x in rows
                         if x["date"] == date and x["source"] == r["name"])
    dates = raw_dates(root)
    prev_dates = [d for d in dates if d < date]
    today = [x for x in rows if x["date"] == date]
    if today and prev_dates:
        prev = [x for x in rows if x["date"] == prev_dates[-1]]
        moves = compute_moves(prev, today)
    else:
        moves = {"moves": [], "new": [], "gone": []}
    status = build_status(root, run_time, results, rows, date, moves)
    write_status(root, status)
    append_log(root, date, run_time, results)
    body = build_issue(date, status, moves)
    (Path(root) / "data" / "issue.md").write_text(body, encoding="utf-8")
    if issue:
        publish_issue(date, body)
    return status


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--no-issue", action="store_true")
    args = p.parse_args(argv)
    status = run(issue=not args.no_issue)
    print(status["run_time"], "items:", status["items"],
          "sources:", status["sources"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
