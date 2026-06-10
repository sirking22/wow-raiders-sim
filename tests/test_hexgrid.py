"""Tests for hex geometry. Run: python3 tests/test_hexgrid.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine"))
import hexgrid as hx


def test_neighbors_are_six_and_distance_one():
    for h in [(0, 0), (3, 2), (4, 5), (2, 3)]:
        ns = hx.neighbors(h)
        assert len(ns) == 6, ns
        assert len(set(ns)) == 6, ns
        for n in ns:
            assert hx.distance(h, n) == 1, (h, n, hx.distance(h, n))


def test_distance_symmetry_and_self_zero():
    pts = [(0, 0), (5, 3), (2, 4), (7, 1)]
    for a in pts:
        assert hx.distance(a, a) == 0
        for b in pts:
            assert hx.distance(a, b) == hx.distance(b, a)


def test_in_range_counts():
    # radius 0 -> just center; radius 1 -> 7 hexes (center + 6)
    assert hx.hexes_in_range((3, 3), 0) == {(3, 3)}
    assert len(hx.hexes_in_range((3, 3), 1)) == 7


def test_reachable_and_path_respect_cost_and_bounds():
    W, H = 8, 6
    blocked = {(2, 2), (2, 3)}

    def cost(h):
        if h in blocked:
            return None  # impassable
        return 1

    dist = hx.reachable((0, 0), 3, W, H, cost)
    assert dist[(0, 0)] == 0
    assert all(v <= 3 for v in dist.values())
    assert (2, 2) not in dist  # blocked never entered
    for h in dist:
        assert hx.in_bounds(h, W, H)

    path, total = hx.shortest_path((0, 0), (5, 4), W, H, cost)
    assert path[0] == (0, 0) and path[-1] == (5, 4)
    for a, b in zip(path, path[1:]):
        assert b in hx.neighbors(a)
    assert total == len(path) - 1  # uniform cost 1


def test_unreachable_returns_none():
    W, H = 5, 5

    def wall(h):
        # column 2 fully blocked -> right side unreachable from left
        return None if h[0] == 2 else 1

    path, total = hx.shortest_path((0, 0), (4, 4), W, H, wall)
    assert path is None and total is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL HEXGRID TESTS PASSED (%d)" % len(fns))
