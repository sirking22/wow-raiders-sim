"""Golden + детерминизм-тесты для движка v0.7 (objective: interrupt ritual).

Запуск: python3 tests/test_golden_v07.py
  1) детерминизм: два прогона на одном seed идентичны;
  2) golden: канонический прогон (seed enc_005_v07, N=5) совпадает с фикстурой бит-в-бит (без log);
  3) контракт v0.7: в snapshot есть ritual, victory_type и death_saves-счётчики.
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from battle_v07 import BattleV07  # noqa: E402


def run_snapshot():
    return BattleV07().run_until_end()


def test_determinism():
    assert run_snapshot() == run_snapshot(), "v0.7 engine is not deterministic for the same seed"


def test_golden_snapshot():
    golden_path = ROOT / "fixtures" / "snap-enc-005-v07-final.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    snap = run_snapshot()
    live = {k: v for k, v in snap.items() if k != "log"}
    assert live == golden, "v0.7 engine output diverged from golden snapshot"


def test_v07_contract():
    snap = run_snapshot()
    assert "ritual" in snap and "required" in snap["ritual"], "snapshot must expose ritual clock"
    assert snap["victory_type"] in ("interrupt_elimination", "ritual_complete", "wipe", None)
    for aid, a in snap["actors"].items():
        ds = a["death_saves"]
        assert set(ds.keys()) == {"success", "fail"}, f"{aid} missing death_save counters"


if __name__ == "__main__":
    test_determinism()
    print("[ok] детерминизм: два прогона идентичны")
    test_golden_snapshot()
    print("[ok] golden: прогон совпадает с snap-enc-005-v07-final.json")
    test_v07_contract()
    print("[ok] контракт v0.7: ritual + victory_type + death_saves-счётчики")
    print("ALL V0.7 TESTS PASSED")
