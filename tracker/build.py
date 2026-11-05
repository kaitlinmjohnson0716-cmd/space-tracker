"""Rebuild data/history.csv from the raw files:  python -m tracker.build"""
from .history import build_history
from .run import ROOT

if __name__ == "__main__":
    rows = build_history(ROOT)
    print("history.csv rebuilt:", len(rows), "rows")
