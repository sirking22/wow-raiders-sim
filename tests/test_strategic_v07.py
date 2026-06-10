"""Acceptance tests for the strategic turn engine.
Run: python3 tests/test_strategic_v07.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import strategic_v07 as strat
import hexgrid as hx


def _run():
    sm = strat.StrategicMap(seed="twilight_ruins_001")
    sm.run(strat.CANON_INTENTS)
    return sm


def test_log_is_1to1_with_turns():
    sm = _run()
    assert len(sm.log) == sm.turn, (len(sm.log), sm.turn)
    for i, entry in enumerate(sm.log, start=1):
        assert entry["turn"] == i


def test_frames_equal_turns_plus_one():
    sm = _run()
    assert len(sm.frames) == sm.turn + 1, (len(sm.frames), sm.turn)


def test_no_validation_errors():
    sm = _run()
    assert strat.validate(sm) == [], strat.validate(sm)


def test_paths_in_bounds_and_adjacent():
    sm = _run()
    for entry in sm.log:
        coords = []
        for label in entry["move"]["path"]:
            col = int(label.split("r")[0][1:])
            row = int(label.split("r")[1])
            assert hx.in_bounds((col, row), strat.WIDTH, strat.HEIGHT)
            coords.append((col, row))
        for a, b in zip(coords, coords[1:]):
            assert b in hx.neighbors(a)


def test_move_budget_respected():
    sm = _run()
    for entry in sm.log:
        assert entry["move"]["cost"] <= strat.SQUAD_MOVE


def test_encounter_triggers_with_battle_seed():
    sm = _run()
    seeds = [ev["battle_seed"] for e in sm.log for ev in e["events"] if ev["type"] == "encounter_triggered"]
    assert "enc_005_v07" in seeds, seeds


def test_determinism():
    a = _run()
    b = _run()
    assert [e["move"] for e in a.log] == [e["move"] for e in b.log]
    assert a.state == b.state


def test_reaches_terminal_state():
    sm = _run()
    assert sm.terminal(), sm.state


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL STRATEGIC TESTS PASSED (%d)" % len(fns))
