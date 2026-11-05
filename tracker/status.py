"""data/status.json: a description of the latest run."""
import json
from pathlib import Path

from .history import raw_dates


def build_status(root, run_time, results, history_rows, date, moves):
    dates = raw_dates(root)
    items = [r for r in history_rows if r["date"] == date]
    return {
        "run_time": run_time,
        "first_run_date": dates[0] if dates else None,
        "days_with_success": len(dates),
        "items": len(items),
        "new_today": [m["item_id"] for m in moves["new"]],
        "gone_today": [m["item_id"] for m in moves["gone"]],
        "sources": [{"name": r["name"], "ok": r["ok"], "count": r["count"]}
                    for r in results],
    }


def write_status(root, status):
    path = Path(root) / "data" / "status.json"
    path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
