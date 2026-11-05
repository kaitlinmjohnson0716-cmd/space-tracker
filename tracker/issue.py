"""The daily GitHub Issue: biggest moves, new and gone items."""
import json
import subprocess


def fmt(n):
    return ("%g" % n)


def build_issue(date, status, moves):
    lines = ["# Space tracker: %s" % date, ""]
    lines.append("Run time (UTC): %s  " % status["run_time"])
    lines.append("Items tracked: %d  " % status["items"])
    lines.append("Days with data: %d" % status["days_with_success"])
    lines += ["", "## Sources", ""]
    for s in status["sources"]:
        lines.append("- %s: %s (%d rows)" %
                     (s["name"], "ok" if s["ok"] else "FAILED", s["count"]))
    lines += ["", "## Biggest moves since the previous run", ""]
    if moves["moves"]:
        lines.append("| Provider | Launches in 30 days | Launches in 7 days |")
        lines.append("|---|---|---|")
        for m in moves["moves"]:
            lines.append("| %s | %s -> %s | %s -> %s |" % (
                m["item"], fmt(m["old_30d"]), fmt(m["new_30d"]),
                fmt(m["old_7d"]), fmt(m["new_7d"])))
    else:
        lines.append("No provider changed its launch counts.")
    lines += ["", "## Appeared", ""]
    lines += ["- " + m["item"] for m in moves["new"]] or ["None."]
    lines += ["", "## Disappeared", ""]
    lines += ["- " + m["item"] for m in moves["gone"]] or ["None."]
    return "\n".join(lines) + "\n"


def _gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True,
                          text=True).stdout


def publish_issue(date, body):
    """Create (or update) the issue titled with the date; close older ones."""
    existing = json.loads(_gh("issue", "list", "--state", "all", "--limit",
                              "100", "--json", "number,title,state"))
    title = date
    same = [i for i in existing if i["title"] == title]
    if same:
        number = str(same[0]["number"])
        _gh("issue", "edit", number, "--body", body)
        if same[0]["state"] != "OPEN":
            _gh("issue", "reopen", number)
    else:
        url = _gh("issue", "create", "--title", title, "--body", body).strip()
        number = url.rsplit("/", 1)[-1]
    for i in existing:
        if i["state"] == "OPEN" and i["title"] != title:
            _gh("issue", "close", str(i["number"]), "--comment",
                "Superseded by %s." % title)
    return number
