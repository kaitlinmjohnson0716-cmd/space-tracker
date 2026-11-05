from tracker.moves import compute_moves


def row(item_id, d30, d7, kind="provider", name=None):
    return {"item_id": item_id, "item": name or item_id, "kind": kind,
            "launches_next_30d": str(d30), "launches_next_7d": str(d7)}


def test_score_and_order():
    prev = [row("a", 5, 1), row("b", 3, 0), row("c", 2, 2)]
    cur = [row("a", 9, 2), row("b", 2, 0), row("c", 2, 2)]
    m = compute_moves(prev, cur)["moves"]
    assert [x["item_id"] for x in m] == ["a", "b"]   # c did not move
    assert m[0]["score"] == 5 and m[1]["score"] == 1
    assert (m[0]["old_30d"], m[0]["new_30d"]) == (5, 9)


def test_limit():
    prev = [row("i%02d" % i, 1, 0) for i in range(15)]
    cur = [row("i%02d" % i, 2 + i, 0) for i in range(15)]
    assert len(compute_moves(prev, cur)["moves"]) == 10
    assert len(compute_moves(prev, cur, limit=3)["moves"]) == 3


def test_new_and_gone():
    prev = [row("a", 1, 0), row("old", 1, 0)]
    cur = [row("a", 1, 0), row("fresh", 1, 0, name="Fresh Co")]
    r = compute_moves(prev, cur)
    assert [x["item_id"] for x in r["new"]] == ["fresh"]
    assert [x["item_id"] for x in r["gone"]] == ["old"]
    assert r["moves"] == []


def test_astronauts_not_ranked():
    prev = [row("astro:1", "", "", kind="astronaut")]
    cur = [row("astro:1", "", "", kind="astronaut")]
    assert compute_moves(prev, cur)["moves"] == []
