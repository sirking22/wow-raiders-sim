"""Пакетный прогон: сравнение динамики v0.4 / v0.5 / v0.6 / v0.7 на одних сидах.

Запуск: python3 tools/run_batch.py [N]

v0.7 вводит objective «interrupt ritual» — победа врага возможна без вайпа (ritual_complete).
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from battle_v04 import BattleV04
from battle_v05 import BattleV05
from battle_v06 import BattleV06
from battle_v07 import BattleV07

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
SEEDS = [f"enc_005_run_{i:02d}" for i in range(1, N + 1)]


def downed_heroes(snap):
    return sorted(aid for aid, a in snap["actors"].items()
                  if a["team"] == "heroes" and ("downed" in a["statuses"] or "dead" in a["statuses"]))


def run(cls, seed):
    snap = cls(seed=seed).run_until_end(max_activations=160)
    return {
        "winner": snap["winner"],
        "victory_type": snap.get("victory_type"),
        "round": snap["round"],
        "acts": snap["activation_count"],
        "heroes_down": downed_heroes(snap),
        "mech": snap.get("mechanics_summary", {}),
        "ritual": snap.get("ritual", {}),
    }


def winrate(results):
    return sum(1 for r in results if r["winner"] == "heroes"), len(results)


ENGINES = [("v0.4", BattleV04), ("v0.5", BattleV05), ("v0.6", BattleV06), ("v0.7", BattleV07)]
out = {name: [run(cls, s) for s in SEEDS] for name, cls in ENGINES}

print("=" * 104)
print(f"{'seed':<18}" + "".join(f"{name+' (win/R/hd)':<20}" for name, _ in ENGINES))
print("-" * 104)
for i, s in enumerate(SEEDS):
    row = f"{s:<18}"
    for name, _ in ENGINES:
        r = out[name][i]
        row += f"{r['winner'][:3]} R{r['round']:<2} hd={len(r['heroes_down'])}".ljust(20)
    print(row)
print("-" * 104)
for name, _ in ENGINES:
    w, n = winrate(out[name])
    avg_r = sum(r["round"] for r in out[name]) / n
    hd = sum(len(r["heroes_down"]) for r in out[name])
    print(f"{name}: heroes winrate {w}/{n} | ср.раундов {avg_r:.1f} | всего выбываний героев {hd}")

# v0.7 разбивка по типам победы + ритуал
vt = {}
for r in out["v0.7"]:
    vt[r["victory_type"]] = vt.get(r["victory_type"], 0) + 1
tot_channels = sum(r["ritual"].get("progress", 0) for r in out["v0.7"])
tot_disrupts = sum(r["ritual"].get("disrupted", 0) for r in out["v0.7"])
print("-" * 104)
print(f"v0.7 victory types: {vt}")
print(f"v0.7 ritual: required={out['v0.7'][0]['ritual'].get('required')} | "
      f"всего каналов {tot_channels} | всего срывов (bloodied) {tot_disrupts}")
mech6 = out["v0.6"][0]["mech"].keys()
agg6 = {k: sum(r["mech"].get(k, 0) for r in out["v0.6"]) for k in mech6}
print(f"v0.6 totals: {agg6}")
print("=" * 104)

(ROOT / "game-data").mkdir(exist_ok=True)
(ROOT / "game-data" / "batch-v04-v07.json").write_text(
    json.dumps({"seeds": SEEDS, "results": out,
                "winrate": {name: list(winrate(out[name])) for name, _ in ENGINES},
                "v07_victory_types": vt, "v06_totals": agg6}, ensure_ascii=False, indent=2), encoding="utf-8")
print("saved -> game-data/batch-v04-v07.json")
