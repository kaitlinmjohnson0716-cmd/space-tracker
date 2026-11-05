# Space Tracker

[![tests](https://github.com/kaitlinmjohnson0716-cmd/space-tracker/actions/workflows/tests.yml/badge.svg)](https://github.com/kaitlinmjohnson0716-cmd/space-tracker/actions/workflows/tests.yml)

A tool that, once a day and on its own, downloads the upcoming rocket launches and the list of people currently in space, adds them to a history (one row per item per day), reports what moved, and publishes the result as an installable website.

Site: https://kaitlinmjohnson0716-cmd.github.io/space-tracker/

## Items

- **Launch providers** (about 20): every organization with a launch scheduled in the next 60 days. Key: `provider:<slug of the name>`.
- **People in space** (about 10): every human aboard a station right now. Key: `astro:<Launch Library person id>`. Non-human entries (test dummies, Laika) are dropped.

## Sources

Both come from the free [Launch Library 2](https://ll.thespacedevs.com/) API (JSON, no login).

| Source name | Format | URL (query) | What is kept |
|---|---|---|---|
| `launches` | JSON | `launch/upcoming/?mode=list&limit=100&net__lte=<date+60 days>` | Only launches in the next 60 days are requested, at most 100. |
| `crew` | JSON | `astronaut/?mode=list&limit=100&in_space=true` | Only people currently in space; non-humans are dropped when converting. |

Each is saved unchanged (compressed) as `data/raw/<date>/<source>.json.gz`. A source that fails after 3 tries writes no raw file that day; the run continues with the other source.

## Files

| Path | What it does |
|---|---|
| `tracker/sources.py` | The two URLs and the download with retries. |
| `tracker/convert.py` | Converts each raw source to rows with the common columns. |
| `tracker/history.py` | Builds `data/history.csv` from the raw files only. |
| `tracker/moves.py` | The move rule. |
| `tracker/status.py` | Writes `data/status.json`. |
| `tracker/issue.py` | Builds and publishes the daily GitHub Issue. |
| `tracker/run.py` | The daily pipeline. `python -m tracker.run` |
| `tracker/build.py` | Rebuilds the history from the raw files. `python -m tracker.build` |
| `tests/` | pytest suite. |
| `.github/workflows/daily.yml` | Runs the pipeline twice a day (06:17 and 18:17 UTC, the second is a backup) and commits the data. |
| `.github/workflows/tests.yml` | Runs the tests on every push. |
| `index.html`, `browse.html`, `trends.html` | The Today, Browse and Trends pages. |
| `common.js`, `style.css` | Shared code, navigation, fonts and colors. |
| `manifest.webmanifest`, `sw.js`, `icon-*.png` | Make the site installable and usable offline. |
| `vendor/chart.umd.min.js` | Chart.js 4.4.1, stored locally so charts work offline. |
| `tools/make_icons.py` | Draws the app icons. |
| `data/raw/` | The raw downloads, one folder per UTC date. |
| `data/history.csv` | One row per item per day. |
| `data/status.json` | Describes the latest run. |
| `data/source_log.csv` | The result of every source on every run, including failures. |

## history.csv columns

Sorted by `date`, then `item_id`. Dates are UTC (`YYYY-MM-DD`). A value the source does not give is empty.

| Column | Meaning |
|---|---|
| `date` | UTC date of the run. |
| `item_id` | Stable key: `provider:<slug>` or `astro:<id>`. |
| `item` | Name of the provider or person. |
| `source` | `launches` or `crew`. |
| `kind` | `provider` or `astronaut`. |
| `group` | Providers: country of the launch site used most often. Astronauts: their space agency. |
| `launches_next_7d` | Provider's launches scheduled from 00:00 UTC of that date up to 7 days later (count). |
| `launches_next_30d` | Same, for 30 days (count). |
| `days_to_next_launch` | Days from 00:00 UTC of that date to the provider's next scheduled launch (days, 2 decimals). |
| `days_in_space` | Total time this person has spent in space (days, 2 decimals). |
| `eva_hours` | Total spacewalk time (hours, 2 decimals). |

Launch distances are measured from the raw file's own date, so rebuilding the history later gives the same numbers.

## The move rule

Only launch providers are ranked (a person's `days_in_space` rises by one every day, which is not news). For each provider present on both the latest day and the previous day:

`score = |change in launches_next_30d| + |change in launches_next_7d|`

Providers with score 0 are not listed. The 10 highest scores are reported (ties broken by name), with old and new values. Items present on only one of the two days are listed as appeared or disappeared. The daily Issue and the Today page use this same rule; the Issue is opened every day, even when nothing moved, and the previous day's Issue is closed.

## Same-day reruns

A second run on the same UTC date replaces that day's raw files, rebuilds the history, and updates that day's Issue, so each day counts once. If a source fails on the second run, the earlier raw file for that day is kept (nothing is deleted).

## Build the history from the raw files

```
python -m tracker.build
```

## Run the tests

```
pip install pytest
python -m pytest
```
