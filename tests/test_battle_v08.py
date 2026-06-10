"""Гекс-инварианты боевого движка v0.8."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from battle_v04 import cell_to_xy, xy_to_cell
from battle_v08 import BattleV08, WIDTH, HEIGHT


def cells(sim):
    return list(sim.cells.keys())


def test_neighbors_six_unique_symmetric():
    sim = BattleV08()
    for c in cells(sim):
        nb = sim.neighbors(c)
        assert len(nb) <= 6, f"{c} имеет >6 соседей"
        assert len(set(nb)) == len(nb), f"{c}: дубли соседей"
        for n in nb:
            assert c in sim.neighbors(n), f"асимметрия {c}->{n}"
    print("[ok] соседи: <=6, без дублей, симметричны")


def test_adjacency_matches_hex_distance_one():
    sim = BattleV08()
    for c in cells(sim):
        for n in sim.neighbors(c):
            assert sim.cheb(c, n) == 1 and sim.adjacent(c, n)
    print("[ok] adjacency <-> hex-distance == 1")


def test_hex_distance_differs_from_chebyshev():
    sim = BattleV08()
    diffs = 0
    for c in cells(sim):
        x, y = cell_to_xy(c)
        nx, ny = x + 1, y + 1  # диагональ (Чебышёв = 1)
        if 1 <= nx <= WIDTH and 1 <= ny <= HEIGHT:
            if sim.cheb(c, xy_to_cell(nx, ny)) != 1:
                diffs += 1
    assert diffs > 0, "гекс-дистанция должна отличаться от Чебышёва на диагоналях"
    print(f"[ok] hex != chebyshev ({diffs} диагональных пар с дистанцией > 1)")


def test_los_blocked_by_full_cover():
    sim = BattleV08()
    cs = cells(sim)
    found = False
    for a in cs:
        for b in cs:
            if a == b:
                continue
            if "D4" in sim.line_cells(a, b)[1:-1]:
                ok, blockers = sim.los(a, b)
                assert (not ok) and "D4" in blockers
                found = True
                break
        if found:
            break
    assert found, "ожидалась гекс-линия сквозь D4 (full cover)"
    print("[ok] LOS блокируется полным укрытием (D4)")


def test_movement_budget_on_hex():
    sim = BattleV08()
    start = sim.actors["EZ"].pos
    goal = next(c for c in cells(sim)
                if sim.cells[c].walkable and 1 <= sim.cheb(start, c) <= 5)
    p = sim.path_to(start, goal, "EZ", 6)
    assert p and p[0] == start and p[-1] == goal and (len(p) - 1) <= 6
    print("[ok] гекс-путь уважает бюджет хода")


if __name__ == "__main__":
    test_neighbors_six_unique_symmetric()
    test_adjacency_matches_hex_distance_one()
    test_hex_distance_differs_from_chebyshev()
    test_los_blocked_by_full_cover()
    test_movement_budget_on_hex()
    print("ALL V0.8 HEX TESTS PASSED (5)")
