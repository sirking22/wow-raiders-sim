#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[1]
checks=[]
def check(name, ok, details=None):
    checks.append({"name":name,"ok":bool(ok),"details":details})
for rel in [
    "engine/hex_raid_simulator_v039.py",
    "engine/render_hex_field_v040.py",
    "game-data/raid-runs/campaign03_raid01_full_run_v039.json",
    "game-data/standards/hex-field-standard-v040.json",
    "docs/CODEX_HANDOFF.md",
    "docs/GITHUB_PUSH_PLAN.md",
]:
    check(f"exists {rel}", (ROOT/rel).exists())
run=json.loads((ROOT/"game-data/raid-runs/campaign03_raid01_full_run_v039.json").read_text(encoding="utf-8"))
check("raid successful extraction", run["status"]=="successful_extraction", run["status"])
check("both encounters victory", all(e["outcome"]=="victory" for e in run["encounter_results"]), [e["outcome"] for e in run["encounter_results"]])
check("all heroes alive", all(h["alive"] for h in run["heroes"].values()), run["heroes"])
std=json.loads((ROOT/"game-data/standards/hex-field-standard-v040.json").read_text(encoding="utf-8"))
check("three field types", len(std["field_types"])==3, len(std["field_types"]))
for img in [
    "visual-standards/png/hex_standard_tactical_11x9_v040.png",
    "visual-standards/png/hex_boss_arena_13x11_v040.png",
    "visual-standards/png/hex_corridor_chokepoint_12x7_v040.png",
    "visual-standards/png/raid01_v039_rectangular_hex_state_v040.png",
]:
    check(f"exists {img}", (ROOT/img).exists())
result={"schema_version":"wow-raiders.v040-verification","passed":all(c["ok"] for c in checks),"checks":checks,"issues":[c for c in checks if not c["ok"]]}
(ROOT/"game-data/qa/v040-verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
(ROOT/"qa").mkdir(exist_ok=True)
(ROOT/"qa/v040-verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"passed":result["passed"],"issues":len(result["issues"])},ensure_ascii=False))
sys.exit(0 if result["passed"] else 1)
