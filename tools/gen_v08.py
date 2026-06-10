"""Генератор канон-артефактов v0.8 (гекс-бой enc_005_v08)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from battle_v08 import BattleV08

snap = BattleV08().run_until_end()
(ROOT / "game-data/battle-reports").mkdir(parents=True, exist_ok=True)
(ROOT / "game-data/snapshots").mkdir(parents=True, exist_ok=True)
(ROOT / "game-data/battle-reports/enc-005-v08-final-state.json").write_text(
    json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "game-data/snapshots/snap-enc-005-v08-final.json").write_text(
    json.dumps({k: v for k, v in snap.items() if k != "log"}, ensure_ascii=False, indent=2), encoding="utf-8")
print("v0.8 golden written:", snap["winner"], snap["victory_type"], "round", snap["round"])
