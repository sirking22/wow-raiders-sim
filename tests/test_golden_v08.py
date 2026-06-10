"""Golden + детерминизм + контракт для движка v0.8 (гекс)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from battle_v08 import BattleV08

GOLDEN = ROOT / "game-data/snapshots/snap-enc-005-v08-final.json"


def run_snapshot():
    snap = BattleV08().run_until_end()
    return {k: v for k, v in snap.items() if k != "log"}


def test_determinism():
    assert run_snapshot() == run_snapshot(), "v0.8 движок недетерминирован при одном seed"
    print("[ok] детерминизм: два прогона идентичны")


def test_golden():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert run_snapshot() == golden, "v0.8 прогон расходится с golden"
    print("[ok] golden: прогон совпадает с snap-enc-005-v08-final.json")


def test_contract():
    snap = BattleV08().run_until_end()
    assert snap["grid"]["type"] == "hex" and snap["grid"]["neighbors"] == 6
    assert snap["engine_version"] == "v0.8-hex"
    assert snap["victory_type"] in {"interrupt_elimination", "ritual_complete", "wipe", None}
    print("[ok] контракт v0.8: grid=hex(6) + victory_type")


if __name__ == "__main__":
    test_determinism()
    test_golden()
    test_contract()
    print("ALL V0.8 GOLDEN TESTS PASSED")
