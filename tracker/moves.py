"""The move rule: what changed between two consecutive days."""

LIMIT = 10


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_moves(prev_rows, cur_rows, limit=LIMIT):
    """Compare the previous run's rows with the latest run's rows.

    Rule: only launch providers are ranked (crew day counts rise by one
    every day, which is not news). score = |change in launches_next_30d|
    + |change in launches_next_7d|. Items with score 0 are not listed.
    The top `limit` are kept, largest score first, ties by item name.
    Items present on only one day are reported as new or gone.
    """
    prev = {r["item_id"]: r for r in prev_rows}
    cur = {r["item_id"]: r for r in cur_rows}
    moves = []
    for item_id, now in cur.items():
        before = prev.get(item_id)
        if before is None or now["kind"] != "provider":
            continue
        o30, n30 = num(before["launches_next_30d"]), num(now["launches_next_30d"])
        o7, n7 = num(before["launches_next_7d"]), num(now["launches_next_7d"])
        if None in (o30, n30, o7, n7):
            continue
        score = abs(n30 - o30) + abs(n7 - o7)
        if score:
            moves.append({
                "item_id": item_id, "item": now["item"], "score": score,
                "old_30d": o30, "new_30d": n30, "old_7d": o7, "new_7d": n7,
            })
    moves.sort(key=lambda m: (-m["score"], m["item"]))
    new = sorted(i for i in cur if i not in prev)
    gone = sorted(i for i in prev if i not in cur)
    return {
        "moves": moves[:limit],
        "new": [{"item_id": i, "item": cur[i]["item"]} for i in new],
        "gone": [{"item_id": i, "item": prev[i]["item"]} for i in gone],
    }
