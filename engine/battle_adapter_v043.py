"""v0.43 adapter between calculated campaign rules and legacy hex battle.

The adapter is intentionally read-only against BattleV08. It proves the mapping
boundary first: v0.42 hero/action data -> v0.8-compatible actor/action contract
-> explicit loss report. Later versions can turn the contract into a runtime
BattleV09 without breaking v0.8 golden tests.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List

import campaign_v042
from battle_v08 import BattleV08


SCHEMA_VERSION = "blackstar-raiders.battle-adapter.v0.43"
SCREEN_SCHEMA = "blackstar-raiders.battle-adapter-screen.v0.43"
ADAPTER_ID = "campaign01_v043_battle_adapter"
V08_SEED = "enc_005_v08"


PLAYER_TO_V08_ACTOR = {
    "EZ": {
        "actor_id": "EZ",
        "fit": "strong",
        "reason": "v0.8 EZ is already a controller/caster analogue.",
    },
    "Candy Peace": {
        "actor_id": "EL",
        "fit": "strong",
        "reason": "v0.8 EL is a protection/frontline analogue.",
    },
    "Dr.Feed": {
        "actor_id": "HE",
        "fit": "weak",
        "reason": "v0.8 has no native medic slot; HE is only a temporary third-hero carrier.",
    },
}


ENEMY_TO_V08_ACTOR = {
    "blight_sergeant": {"actor_id": "SG", "fit": "partial", "reason": "armored pressure unit"},
    "rust_gunner": {"actor_id": "XB", "fit": "partial", "reason": "ranged pressure unit"},
    "relic_thrall_pack": {"actor_id": "WG", "fit": "partial", "reason": "mobile melee pressure"},
}


ACTION_TO_V08 = {
    "prism_lock": {
        "support_level": "partial",
        "v08_equivalent": "eldritch_blast + hex/focus-mark family",
        "missing": ["objective progress", "psyker risk clock"],
    },
    "scan_relic_signal": {
        "support_level": "missing",
        "v08_equivalent": None,
        "missing": ["non-combat scan action", "intel gain", "objective clue progress"],
    },
    "stabilize_ally": {
        "support_level": "partial",
        "v08_equivalent": "lay_on_hands family",
        "missing": ["Dr.Feed native medic actor", "consumable loadout spend"],
    },
    "field_injector": {
        "support_level": "missing",
        "v08_equivalent": None,
        "missing": ["bonus-action consumable healing"],
    },
    "guard_line": {
        "support_level": "partial",
        "v08_equivalent": "protective_guard / protection_reaction",
        "missing": ["squad-wide mitigation pool", "threat anchoring"],
    },
    "raise_shield": {
        "support_level": "partial",
        "v08_equivalent": "protection_reaction",
        "missing": ["bonus-action shield stance"],
    },
    "secure_exit_lane": {
        "support_level": "missing",
        "v08_equivalent": None,
        "missing": ["extraction lane objective", "readiness score"],
    },
    "reposition": {
        "support_level": "partial",
        "v08_equivalent": "move / cautious_step",
        "missing": ["directive-scored movement intent"],
    },
    "breach_fire": {
        "support_level": "partial",
        "v08_equivalent": "crossbow / ranged attack family",
        "missing": ["noise clock", "breach objective progress"],
    },
    "precision_shot": {
        "support_level": "partial",
        "v08_equivalent": "shortbow+sneak / crossbow family",
        "missing": ["precision-tagged objective pressure"],
    },
    "reload_or_vent": {
        "support_level": "missing",
        "v08_equivalent": None,
        "missing": ["weapon heat / reload preparation"],
    },
}


def build_adapter_report(v042_run: Dict[str, Any] | None = None, battle_seed: str = V08_SEED) -> Dict[str, Any]:
    v042 = copy.deepcopy(v042_run) if v042_run is not None else campaign_v042.simulate_campaign()
    battle_snapshot = BattleV08(seed=battle_seed).run_until_end()
    actor_contract = build_actor_contract(v042, battle_snapshot)
    action_contract = build_action_contract(v042)
    loss_report = build_loss_report(actor_contract, action_contract)
    adapter_screen = build_adapter_screen(v042, battle_snapshot, actor_contract, action_contract, loss_report)
    report = {
        "schema": SCHEMA_VERSION,
        "adapter_id": ADAPTER_ID,
        "source_run": {
            "schema": v042["schema"],
            "run_id": v042["run_id"],
            "rules_schema": v042["rules_summary"]["schema"],
        },
        "target_battle": {
            "engine_version": battle_snapshot["engine_version"],
            "seed": battle_snapshot["seed"],
            "snapshot_id": battle_snapshot["snapshot_id"],
            "winner": battle_snapshot["winner"],
            "victory_type": battle_snapshot["victory_type"],
            "round": battle_snapshot["round"],
            "activation_count": battle_snapshot["activation_count"],
            "grid": battle_snapshot["grid"],
            "actor_ids": sorted(battle_snapshot["actors"]),
            "mechanics_summary": battle_snapshot["mechanics_summary"],
        },
        "actor_contract": actor_contract,
        "action_contract": action_contract,
        "loss_report": loss_report,
        "adapter_screen": adapter_screen,
        "next_runtime_requirement": {
            "id": "battle_v09_external_roster_runtime",
            "goal": "Allow battle runtime to accept external roster, action plan, objective clocks, and medic/support roles.",
            "must_preserve": ["BattleV08 golden tests", "hex grid invariants", "deterministic seed behavior"],
        },
    }
    report["validation_errors"] = validate_adapter_report(report)
    return report


def build_actor_contract(v042: Dict[str, Any], battle_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    v042_squad = _squad_from_v042(v042)
    actors = battle_snapshot["actors"]
    hero_mappings = []
    for hero in v042_squad:
        player = hero["player"]
        mapping = PLAYER_TO_V08_ACTOR[player]
        target = actors[mapping["actor_id"]]
        hero_mappings.append(
            {
                "player": player,
                "v042_hero": hero["hero"],
                "v042_role": hero["role"],
                "target_v08_actor": mapping["actor_id"],
                "target_v08_class": target["class"],
                "fit": mapping["fit"],
                "reason": mapping["reason"],
                "stat_projection": project_hero_to_v08_actor(hero, target),
            }
        )

    latest_enemy_state = v042["tactical_rounds"][-1]["enemy_state"]
    enemy_mappings = []
    for enemy in latest_enemy_state:
        mapping = ENEMY_TO_V08_ACTOR[enemy["id"]]
        target = actors[mapping["actor_id"]]
        enemy_mappings.append(
            {
                "v042_enemy": enemy["id"],
                "target_v08_actor": mapping["actor_id"],
                "target_v08_class": target["class"],
                "fit": mapping["fit"],
                "reason": mapping["reason"],
                "stat_projection": {
                    "source_hp": enemy["hp"],
                    "target_hp": target["hp"],
                    "source_armor": enemy["armor"],
                    "target_ac": target["ac"],
                    "source_threat": enemy["threat"],
                },
            }
        )

    return {
        "hero_mappings": hero_mappings,
        "enemy_mappings": enemy_mappings,
        "unmapped_v08_actors": sorted(set(actors) - {m["target_v08_actor"] for m in hero_mappings + enemy_mappings}),
    }


def project_hero_to_v08_actor(hero: Dict[str, Any], target_actor: Dict[str, Any]) -> Dict[str, Any]:
    derived = hero["derived"]
    attrs = hero["attributes"]
    projected_ac = 10 + derived["armor"] + derived["evasion"]
    return {
        "hp": {"source": hero["max_hp"], "target_current": target_actor["hp"], "target_max": target_actor["max_hp"]},
        "ac": {"source_projected": projected_ac, "target": target_actor["ac"]},
        "movement": {"source": derived["movement"], "v08_default": target_actor["resources"].get("movement")},
        "action_budget": {"source": {"main": 1, "bonus": 1}, "v08_resources": {"action": 1, "bonus_action": 1, "reaction": 1}},
        "dndish_stats_projection": {
            "str": 8 + attrs["force"],
            "dex": 8 + attrs["agility"],
            "con": 8 + attrs["endurance"],
            "int": 8 + attrs["tech"],
            "wis": 8 + attrs["will"],
            "cha": 8 + attrs["presence"],
        },
    }


def build_action_contract(v042: Dict[str, Any]) -> Dict[str, Any]:
    action_docs = []
    seen = set()
    for round_doc in v042["tactical_rounds"]:
        for hero_action in round_doc["hero_actions"]:
            for action_kind in ("main_action", "bonus_action"):
                action = hero_action[action_kind]
                key = (hero_action["actor"], action_kind, action["id"])
                if key in seen:
                    continue
                seen.add(key)
                mapping = ACTION_TO_V08[action["id"]]
                action_docs.append(
                    {
                        "player": hero_action["actor"],
                        "kind": action_kind,
                        "v042_action": action["id"],
                        "support_level": mapping["support_level"],
                        "v08_equivalent": mapping["v08_equivalent"],
                        "missing": mapping["missing"],
                        "score": action["score"],
                        "top_score_components": _top_score_components(action["score_components"]),
                        "effect": action["effect"],
                    }
                )
    support_counts: Dict[str, int] = {}
    for doc in action_docs:
        support_counts[doc["support_level"]] = support_counts.get(doc["support_level"], 0) + 1
    return {
        "action_mappings": action_docs,
        "support_counts": support_counts,
        "all_v042_actions_have_mapping_doc": all(doc["v042_action"] in ACTION_TO_V08 for doc in action_docs),
    }


def build_loss_report(actor_contract: Dict[str, Any], action_contract: Dict[str, Any]) -> Dict[str, Any]:
    actor_gaps = []
    for mapping in actor_contract["hero_mappings"]:
        if mapping["fit"] != "strong":
            actor_gaps.append(
                {
                    "type": "actor_fit",
                    "player": mapping["player"],
                    "severity": "high" if mapping["player"] == "Dr.Feed" else "medium",
                    "issue": mapping["reason"],
                }
            )
    action_gaps = []
    for doc in action_contract["action_mappings"]:
        if doc["support_level"] in ("partial", "missing"):
            action_gaps.append(
                {
                    "type": "action_mapping",
                    "player": doc["player"],
                    "action": doc["v042_action"],
                    "support_level": doc["support_level"],
                    "missing": doc["missing"],
                }
            )
    missing_count = action_contract["support_counts"].get("missing", 0)
    partial_count = action_contract["support_counts"].get("partial", 0)
    return {
        "adapter_status": "contract_only_not_runtime_replacement",
        "runtime_risk": "high" if missing_count else "medium" if partial_count else "low",
        "actor_gaps": actor_gaps,
        "action_gaps": action_gaps,
        "required_engine_work": [
            "external roster injection",
            "Dr.Feed native medic/support actor",
            "objective and extraction clocks inside tactical runtime",
            "bonus-action consumables",
            "route/quest scan actions in combat",
        ],
    }


def build_adapter_screen(
    v042: Dict[str, Any],
    battle_snapshot: Dict[str, Any],
    actor_contract: Dict[str, Any],
    action_contract: Dict[str, Any],
    loss_report: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "schema": SCREEN_SCHEMA,
        "screen_id": f"{ADAPTER_ID}_screen_battle_adapter_review",
        "stage": "battle_adapter_review",
        "title": "Battle Adapter Review",
        "time_index": len(v042["screen_payloads"]),
        "state": {
            "source_run_id": v042["run_id"],
            "source_rules": v042["rules_summary"]["schema"],
            "target_engine": battle_snapshot["engine_version"],
            "target_grid": battle_snapshot["grid"],
            "actor_contract": actor_contract,
            "support_counts": action_contract["support_counts"],
            "loss_report": loss_report,
        },
        "ui_panels": [
            {"id": "source_campaign"},
            {"id": "actor_mapping"},
            {"id": "action_mapping"},
            {"id": "loss_report"},
            {"id": "next_engine_work"},
        ],
        "log_refs": [v042["run_id"], battle_snapshot["snapshot_id"]],
        "calculation_refs": ["engine/battle_adapter_v043.py", "engine/rules_v042.py", "engine/battle_v08.py"],
        "render_contract": {
            "source_of_truth": ["state", "log_refs", "calculation_refs"],
            "must_show": ["source_run_id", "target_engine", "actor_contract", "support_counts", "loss_report"],
            "must_not_invent": ["runtime integration is complete", "Dr.Feed native medic support in v0.8", "battle_v08 accepts external roster"],
        },
        "next_decisions": [
            {"id": "build_battle_v09_external_roster", "label": "Build BattleV09 external roster runtime"},
            {"id": "keep_adapter_contract_only", "label": "Keep adapter as review gate and improve mappings"},
        ],
    }


def validate_adapter_report(report: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if report.get("schema") != SCHEMA_VERSION:
        errors.append("bad adapter schema")
    if report["source_run"]["schema"] != campaign_v042.SCHEMA_VERSION:
        errors.append("source run is not v0.42")
    if report["target_battle"]["engine_version"] != "v0.8-hex":
        errors.append("target battle is not v0.8-hex")
    if report["target_battle"]["grid"]["type"] != "hex":
        errors.append("target battle grid is not hex")
    players = [m["player"] for m in report["actor_contract"]["hero_mappings"]]
    if players != ["EZ", "Candy Peace", "Dr.Feed"]:
        errors.append(f"bad player mapping order {players}")
    target_ids = [m["target_v08_actor"] for m in report["actor_contract"]["hero_mappings"]]
    if len(target_ids) != len(set(target_ids)):
        errors.append("duplicate target v08 actor mapping")
    if not report["action_contract"]["all_v042_actions_have_mapping_doc"]:
        errors.append("not all actions have mapping docs")
    support_counts = report["action_contract"]["support_counts"]
    if support_counts.get("missing", 0) < 1:
        errors.append("expected at least one explicit missing action gap")
    if not any(gap.get("player") == "Dr.Feed" for gap in report["loss_report"]["actor_gaps"]):
        errors.append("Dr.Feed native medic gap is not explicit")
    screen = report["adapter_screen"]
    for key in ("screen_id", "stage", "state", "render_contract", "next_decisions"):
        if key not in screen:
            errors.append(f"adapter screen missing {key}")
    if screen.get("stage") != "battle_adapter_review":
        errors.append("adapter screen has wrong stage")
    return errors


def write_outputs(report: Dict[str, Any], root: str | None = None) -> Dict[str, str]:
    repo_root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = {
        "report": os.path.join(repo_root, "game-data", "battle-adapters", "campaign01_v043_battle_adapter_report.json"),
        "screen": os.path.join(repo_root, "game-data", "screen-payloads", "campaign01_v043_battle_adapter_screen.json"),
    }
    for path in paths.values():
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(paths["report"], "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(paths["screen"], "w", encoding="utf-8") as f:
        json.dump(report["adapter_screen"], f, ensure_ascii=False, indent=2)
    return paths


def _squad_from_v042(v042: Dict[str, Any]) -> List[Dict[str, Any]]:
    for screen in v042["screen_payloads"]:
        if screen["stage"] == "camp_loadout":
            return copy.deepcopy(screen["state"]["squad_after_loadout"])
    raise KeyError("camp_loadout screen not found")


def _top_score_components(components: Dict[str, float], limit: int = 5) -> List[Dict[str, Any]]:
    ranked = sorted(components.items(), key=lambda item: (-float(item[1]), item[0]))
    return [{"component": key, "value": value} for key, value in ranked[:limit]]


def main() -> None:
    report = build_adapter_report()
    paths = write_outputs(report)
    print(
        json.dumps(
            {
                "adapter_id": report["adapter_id"],
                "source_run": report["source_run"]["run_id"],
                "target_engine": report["target_battle"]["engine_version"],
                "support_counts": report["action_contract"]["support_counts"],
                "runtime_risk": report["loss_report"]["runtime_risk"],
                "validation_errors": report["validation_errors"],
                "outputs": paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if report["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
