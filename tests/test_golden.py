"""Golden + determinism tests for the WoW Raiders v0.4 engine.

Запуск: python3 tests/test_golden.py
Проверяет:
  1) детерминизм: два прогона на одном seed идентичны;
  2) golden: прогон совпадает с зафиксированным snapshot бит-в-бит.
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from battle_v04 import BattleV04  # noqa: E402


def run_snapshot():
    sim = BattleV04()
    return sim.run_until_end()


def test_determinism():
    a = run_snapshot()
    b = run_snapshot()
    assert a == b, "engine is not deterministic for the same seed"


def test_golden_snapshot():
    golden_path = ROOT / "fixtures" / "snap-enc-005-v04-final.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    snap = run_snapshot()
    live = {k: v for k, v in snap.items() if k != "log"}
    assert live == golden, "engine output diverged from golden snapshot"


if __name__ == "__main__":
    test_determinism()
    print("[ok] determinism: два прогона идентичны")
    test_golden_snapshot()
    print("[ok] golden: прогон совпадает с snap-enc-005-v04-final.json")
    print("ALL TESTS PASSED")
