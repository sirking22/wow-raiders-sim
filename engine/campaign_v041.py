"""Blackstar Raiders campaign orchestrator v0.41.

This module does not replace battle_v08.py or strategic_v07.py. It adds the
first full-run layer above them: player directives, AI director/GM/hero roles,
screen payloads, timeline, rewards, hero progression, and camp return.

Run:
    python engine/campaign_v041.py
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from typing import Any, Dict, List, Tuple


SCHEMA_VERSION = "blackstar-raiders.campaign-run.v0.41"
CAMPAIGN_ID = "blackstar_campaign_001"
RUN_ID = "blackstar_campaign_001_run_001_v041"
SEED = "blackstar-v041-demo-001"


HERO_POOL: List[Dict[str, Any]] = [
    {
        "id": "void_chaplain",
        "name": "Void Chaplain",
        "role": "tank",
        "class_tags": ["anchor", "protector", "morale"],
        "stats": {"hp": 42, "armor": 5, "mobility": 3, "focus": 3, "tech": 1},
    },
    {
        "id": "ash_scout",
        "name": "Ash Scout",
        "role": "scout",
        "class_tags": ["mobility", "stealth", "route"],
        "stats": {"hp": 28, "armor": 2, "mobility": 6, "focus": 4, "tech": 2},
    },
    {
        "id": "plague_surgeon",
        "name": "Plague Surgeon",
        "role": "medic",
        "class_tags": ["healing", "toxins", "stabilize"],
        "stats": {"hp": 32, "armor": 3, "mobility": 3, "focus": 5, "tech": 4},
    },
    {
        "id": "siege_gunner",
        "name": "Siege Gunner",
        "role": "engineer",
        "class_tags": ["suppression", "breach", "heavy"],
        "stats": {"hp": 38, "armor": 4, "mobility": 2, "focus": 3, "tech": 4},
    },
    {
        "id": "sanctioned_prism_psyker",
        "name": "Sanctioned Prism Psyker",
        "role": "control",
        "class_tags": ["psyker", "control", "risk"],
        "stats": {"hp": 27, "armor": 2, "mobility": 4, "focus": 7, "tech": 1},
    },
    {
        "id": "iron_tech_adept",
        "name": "Iron Tech-Adept",
        "role": "support",
        "class_tags": ["repair", "devices", "camp"],
        "stats": {"hp": 30, "armor": 3, "mobility": 3, "focus": 4, "tech": 7},
    },
    {
        "id": "deathworld_beastmaster",
        "name": "Deathworld Beastmaster",
        "role": "ranger",
        "class_tags": ["tracking", "beast", "survival"],
        "stats": {"hp": 34, "armor": 3, "mobility": 5, "focus": 3, "tech": 1},
    },
    {
        "id": "penitent_duelist",
        "name": "Penitent Duelist",
        "role": "duelist",
        "class_tags": ["melee", "bleed", "zeal"],
        "stats": {"hp": 33, "armor": 3, "mobility": 5, "focus": 4, "tech": 1},
    },
    {
        "id": "xeno_relic_sniper",
        "name": "Xeno Relic Sniper",
        "role": "sniper",
        "class_tags": ["range", "relics", "precision"],
        "stats": {"hp": 26, "armor": 2, "mobility": 4, "focus": 6, "tech": 3},
    },
]


PLAYER_SLOTS = [
    {"player": "EZ", "assigned_hero": "sanctioned_prism_psyker"},
    {"player": "Candy Peace", "assigned_hero": "void_chaplain"},
    {"player": "Dr.Feed", "assigned_hero": "plague_surgeon"},
]


PLAYER_DIRECTIVES: Dict[str, Dict[str, Any]] = {
    "EZ": {
        "mobility": 0.65,
        "objective": 0.85,
        "greed": 0.35,
        "survival": 0.45,
        "ability_bias": "control_priority",
        "character_notes": ["seeks anomalies", "pushes objective tempo"],
    },
    "Candy Peace": {
        "mobility": 0.35,
        "objective": 0.65,
        "greed": 0.30,
        "survival": 0.80,
        "ability_bias": "guard_allies",
        "character_notes": ["holds line", "protects medic"],
    },
    "Dr.Feed": {
        "mobility": 0.30,
        "objective": 0.55,
        "greed": 0.25,
        "survival": 0.90,
        "ability_bias": "heal_early",
        "character_notes": ["keeps squad alive", "spends supplies before collapse"],
    },
}


BASE_CAMP: Dict[str, Any] = {
    "id": "blackstar_camp_vesper_reliquary",
    "name": "Vesper Reliquary Camp",
    "tier": 1,
    "resources": {"scrap": 18, "relic_shards": 4, "medicae": 3, "intel": 2},
    "facilities": {
        "triage_bay": {"level": 1, "effect": "post-run injury mitigation"},
        "armory_rack": {"level": 1, "effect": "basic loadout budget"},
        "strategium_table": {"level": 0, "effect": "route intel locked"},
    },
    "heat": 1,
    "morale": 6,
    "persistent_events": [],
}


MISSION: Dict[str, Any] = {
    "id": "blightfall_relic_extraction",
    "name": "Blightfall Relic Extraction",
    "planet": "Korvash Prime",
    "primary_objective": "recover black reliquary core",
    "secondary_objectives": ["scan dead vox shrine", "extract at least two heroes alive"],
    "extraction_window": 30,
    "threat_band": "extreme",
    "rewards": {"relic_shards": 6, "scrap": 10, "intel": 3, "xp": 120},
}


SETTING_PROFILE: Dict[str, Any] = {
    "production_mode": "blackstar_raiders_original_safe",
    "reference_target": "hard WH40 latest-edition grimdark planetary raid mood",
    "tone": ["brutal", "gothic", "military", "high-risk", "no-soft-fantasy"],
    "public_asset_rule": "use original names and symbols unless explicitly marked as private fan/reference work",
}


def stable_int(seed: str, key: str, low: int, high: int) -> int:
    digest = hashlib.sha256(f"{seed}:{key}".encode("utf-8")).hexdigest()
    span = high - low + 1
    return low + (int(digest[:12], 16) % span)


def hero_by_id(hero_id: str) -> Dict[str, Any]:
    for hero in HERO_POOL:
        if hero["id"] == hero_id:
            return hero
    raise KeyError(hero_id)


def build_squad() -> List[Dict[str, Any]]:
    squad = []
    for slot in PLAYER_SLOTS:
        base = copy.deepcopy(hero_by_id(slot["assigned_hero"]))
        stats = base["stats"]
        squad.append(
            {
                "player": slot["player"],
                "hero_id": base["id"],
                "hero_name": base["name"],
                "role": base["role"],
                "class_tags": base["class_tags"],
                "stats": stats,
                "hp": stats["hp"],
                "max_hp": stats["hp"],
                "xp": 0,
                "level": 1,
                "injuries": [],
                "traits": [],
                "directive": copy.deepcopy(PLAYER_DIRECTIVES[slot["player"]]),
                "loadout": [],
            }
        )
    return squad


def make_screen(
    screens: List[Dict[str, Any]],
    stage: str,
    title: str,
    state: Dict[str, Any],
    ui_panels: List[Dict[str, Any]],
    log_refs: List[str] | None = None,
    next_decisions: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    idx = len(screens)
    screen = {
        "screen_id": f"{RUN_ID}_screen_{idx:02d}_{stage}",
        "stage": stage,
        "title": title,
        "time_index": idx,
        "state": state,
        "ui_panels": ui_panels,
        "log_refs": log_refs or [],
        "render_contract": {
            "source_of_truth": ["state", "ui_panels", "log_refs"],
            "must_show": sorted(state.keys()),
            "must_not_invent": [
                "hero stats outside state",
                "dead/alive status not in state",
                "loot not present in state",
                "player names other than EZ, Candy Peace, Dr.Feed",
            ],
        },
        "next_decisions": next_decisions or [],
    }
    screens.append(screen)
    return screen


def director_event(timeline: List[Dict[str, Any]], clocks: Dict[str, int], event: str, delta: Dict[str, int]) -> None:
    for key, value in delta.items():
        clocks[key] = max(0, clocks.get(key, 0) + value)
    timeline.append({"type": "director", "event": event, "clocks": copy.deepcopy(clocks)})


def choose_hero_action(hero: Dict[str, Any], enemies: List[Dict[str, Any]], round_no: int) -> Dict[str, Any]:
    directive = hero["directive"]
    wounded_ally = directive["ability_bias"] == "heal_early" and hero["role"] == "medic"
    if wounded_ally:
        return {"main": "stabilize_ally", "bonus": "tox_screen", "target": "lowest_ally"}
    if directive["objective"] >= 0.8 and hero["role"] == "control":
        return {"main": "prism_lock", "bonus": "scan_relic_signal", "target": "highest_threat"}
    if directive["survival"] >= 0.75 and hero["role"] == "tank":
        return {"main": "guard_line", "bonus": "raise_shield", "target": "squad"}
    if round_no >= 3:
        return {"main": "secure_exit_lane", "bonus": "reload_or_reposition", "target": "extraction"}
    live = [e for e in enemies if e["hp"] > 0]
    return {"main": "focused_attack", "bonus": "reposition", "target": live[0]["id"] if live else "none"}


def resolve_tactical_encounter(seed: str, squad: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    enemies = [
        {"id": "blight_sergeant", "name": "Blight Sergeant", "hp": 36, "threat": 4, "target_bias": "medic"},
        {"id": "rust_gunner", "name": "Rust Gunner", "hp": 28, "threat": 3, "target_bias": "lowest_armor"},
        {"id": "relic_thrall_pack", "name": "Relic Thrall Pack", "hp": 42, "threat": 2, "target_bias": "frontline"},
    ]
    rounds: List[Dict[str, Any]] = []
    objective_progress = 0
    ammo_noise = 0

    for round_no in range(1, 4):
        entries = []
        for hero in squad:
            action = choose_hero_action(hero, enemies, round_no)
            movement = min(6, 2 + hero["stats"]["mobility"])
            live_enemies = [e for e in enemies if e["hp"] > 0]
            target = next((e for e in live_enemies if e["id"] == action["target"]), live_enemies[0] if live_enemies else None)
            roll = stable_int(seed, f"r{round_no}:{hero['player']}:{action['main']}", 1, 20)
            damage = 0
            effects = []
            if action["main"] == "stabilize_ally":
                ally = min(squad, key=lambda h: h["hp"] / h["max_hp"])
                heal = 5 + stable_int(seed, f"heal:{round_no}:{hero['player']}", 1, 6)
                before = ally["hp"]
                ally["hp"] = min(ally["max_hp"], ally["hp"] + heal)
                effects.append({"type": "heal", "target": ally["player"], "before": before, "after": ally["hp"]})
                objective_progress += 1
            elif action["main"] == "guard_line":
                effects.append({"type": "guard", "target": "squad", "mitigation": 3})
                objective_progress += 1
            elif action["main"] == "prism_lock":
                if target:
                    damage = 6 + hero["stats"]["focus"] + (roll // 5)
                    before = target["hp"]
                    target["hp"] = max(0, target["hp"] - damage)
                    effects.append({"type": "control_damage", "target": target["id"], "before": before, "after": target["hp"]})
                objective_progress += 2
                ammo_noise += 1
            elif action["main"] == "secure_exit_lane":
                objective_progress += 2
                effects.append({"type": "exit_lane", "progress": objective_progress})
            elif target:
                damage = 4 + hero["stats"]["focus"] + stable_int(seed, f"dmg:{round_no}:{hero['player']}", 1, 8)
                before = target["hp"]
                target["hp"] = max(0, target["hp"] - damage)
                effects.append({"type": "damage", "target": target["id"], "before": before, "after": target["hp"]})
                ammo_noise += 1

            entries.append(
                {
                    "actor": hero["player"],
                    "hero": hero["hero_name"],
                    "movement_points_used": movement,
                    "main_action": action["main"],
                    "bonus_action": action["bonus"],
                    "target": action["target"],
                    "roll": roll,
                    "damage": damage,
                    "effects": effects,
                }
            )

        enemy_entries = []
        for enemy in enemies:
            if enemy["hp"] <= 0:
                continue
            if enemy["target_bias"] == "medic":
                target_hero = next(h for h in squad if h["role"] == "medic")
            elif enemy["target_bias"] == "lowest_armor":
                target_hero = min(squad, key=lambda h: h["stats"]["armor"])
            else:
                target_hero = max(squad, key=lambda h: h["stats"]["armor"])
            incoming = max(1, enemy["threat"] + stable_int(seed, f"enemy:{round_no}:{enemy['id']}", 1, 6) - target_hero["stats"]["armor"])
            if any(e["main_action"] == "guard_line" for e in entries):
                incoming = max(0, incoming - 3)
            before = target_hero["hp"]
            target_hero["hp"] = max(0, target_hero["hp"] - incoming)
            enemy_entries.append(
                {
                    "actor": enemy["id"],
                    "target": target_hero["player"],
                    "damage": incoming,
                    "before": before,
                    "after": target_hero["hp"],
                }
            )

        rounds.append(
            {
                "round": round_no,
                "hero_actions": entries,
                "enemy_actions": enemy_entries,
                "enemy_state": copy.deepcopy(enemies),
                "squad_state": [
                    {"player": h["player"], "hero": h["hero_name"], "hp": h["hp"], "max_hp": h["max_hp"]}
                    for h in squad
                ],
                "objective_progress": objective_progress,
                "noise": ammo_noise,
            }
        )

    victory = objective_progress >= 5 and sum(1 for h in squad if h["hp"] > 0) >= 2
    return rounds, {
        "victory": victory,
        "objective_progress": objective_progress,
        "noise": ammo_noise,
        "enemies_remaining": [e for e in enemies if e["hp"] > 0],
        "heroes_alive": [h["player"] for h in squad if h["hp"] > 0],
    }


def apply_progression(squad: List[Dict[str, Any]], camp: Dict[str, Any], tactical_result: Dict[str, Any]) -> Dict[str, Any]:
    rewards = copy.deepcopy(MISSION["rewards"])
    if not tactical_result["victory"]:
        rewards = {k: max(0, v // 2) for k, v in rewards.items()}
    for key, value in rewards.items():
        if key == "xp":
            continue
        camp["resources"][key] = camp["resources"].get(key, 0) + value

    camp["heat"] += 2 if tactical_result["noise"] >= 3 else 1
    camp["morale"] += 1 if tactical_result["victory"] else -1
    camp["persistent_events"].append(
        {
            "id": "black_reliquary_claimed" if tactical_result["victory"] else "blightfall_failed_push",
            "campaign": CAMPAIGN_ID,
            "run": RUN_ID,
        }
    )
    if camp["resources"].get("scrap", 0) >= 25:
        camp["facilities"]["armory_rack"]["level"] = max(camp["facilities"]["armory_rack"]["level"], 2)

    hero_progress = []
    for hero in squad:
        xp_gain = rewards["xp"] + (20 if hero["hp"] > 0 else 0)
        hero["xp"] += xp_gain
        if hero["xp"] >= 120:
            hero["level"] += 1
            hero["xp"] -= 120
            trait = "field_hardened" if hero["hp"] > hero["max_hp"] // 2 else "scarred_survivor"
            if trait not in hero["traits"]:
                hero["traits"].append(trait)
        if hero["hp"] <= hero["max_hp"] // 3:
            hero["injuries"].append("stress_fracture")
        hero_progress.append(
            {
                "player": hero["player"],
                "hero": hero["hero_name"],
                "level": hero["level"],
                "xp": hero["xp"],
                "hp": hero["hp"],
                "max_hp": hero["max_hp"],
                "traits": hero["traits"],
                "injuries": hero["injuries"],
            }
        )
    return {"rewards": rewards, "hero_progress": hero_progress, "camp": camp}


def simulate_campaign(seed: str = SEED) -> Dict[str, Any]:
    screens: List[Dict[str, Any]] = []
    timeline: List[Dict[str, Any]] = []
    camp = copy.deepcopy(BASE_CAMP)
    clocks = {"threat": 3, "noise": 0, "doom": 2, "extraction_timer": MISSION["extraction_window"]}

    make_screen(
        screens,
        "hero_selection",
        "Hero Selection",
        {
            "player_slots": [{"player": slot["player"], "status": "unassigned"} for slot in PLAYER_SLOTS],
            "hero_pool": HERO_POOL,
            "setting_profile": SETTING_PROFILE,
        },
        [{"id": "slot_row"}, {"id": "hero_pool_grid"}, {"id": "mission_sidebar"}],
        next_decisions=[{"id": "assign_squad", "label": "Assign heroes for this run"}],
    )

    squad = build_squad()
    make_screen(
        screens,
        "squad_lock_in",
        "Squad Lock-In",
        {"squad": squad, "directives": PLAYER_DIRECTIVES},
        [{"id": "assigned_slots"}, {"id": "directive_cards"}],
        next_decisions=[{"id": "confirm_directives", "label": "Confirm player directives"}],
    )

    timeline.append({"type": "campaign_start", "campaign": CAMPAIGN_ID, "mission": MISSION["id"]})
    make_screen(
        screens,
        "campaign_briefing",
        "Campaign Briefing",
        {"mission": MISSION, "camp": camp, "director_clocks": clocks},
        [{"id": "mission_objectives"}, {"id": "risk_panel"}, {"id": "reward_panel"}],
    )

    for hero in squad:
        if hero["role"] == "medic":
            hero["loadout"] = ["medicae injector", "toxin screen", "field sutures"]
            camp["resources"]["medicae"] -= 1
        elif hero["role"] == "tank":
            hero["loadout"] = ["void shield", "chain relic", "smoke charge"]
            camp["resources"]["scrap"] -= 2
        else:
            hero["loadout"] = ["prism focus", "relic scanner", "stimm dose"]
            camp["resources"]["intel"] -= 1
    make_screen(
        screens,
        "camp_loadout",
        "Camp Loadout",
        {"camp": camp, "squad_loadouts": [{"player": h["player"], "loadout": h["loadout"]} for h in squad]},
        [{"id": "camp_resources"}, {"id": "loadout_grid"}],
    )

    director_event(timeline, clocks, "drop_in_under_fire", {"noise": 1, "extraction_timer": -3})
    make_screen(
        screens,
        "drop_in",
        "Drop-In",
        {"zone": "Korvash Prime / ash landing deck", "director_clocks": clocks, "squad": squad},
        [{"id": "landing_zone"}, {"id": "clock_panel"}],
        log_refs=["timeline:drop_in_under_fire"],
    )

    route_nodes = [
        {"node": "ash_causeway", "choice": "fast route", "cost": {"extraction_timer": -4, "noise": 1}},
        {"node": "dead_vox_shrine", "choice": "scan secondary", "cost": {"extraction_timer": -5, "doom": 1}, "reward": {"intel": 1}},
        {"node": "black_reliquary_gate", "choice": "breach vault", "cost": {"threat": 1, "noise": 1}},
    ]
    for idx, node in enumerate(route_nodes, start=1):
        director_event(timeline, clocks, f"route:{node['node']}:{node['choice']}", node["cost"])
        if "reward" in node:
            for key, value in node["reward"].items():
                camp["resources"][key] = camp["resources"].get(key, 0) + value
        make_screen(
            screens,
            "route_map",
            f"Route Map {idx}",
            {"node": node, "director_clocks": copy.deepcopy(clocks), "camp_resources": copy.deepcopy(camp["resources"])},
            [{"id": "hex_route_map"}, {"id": "director_clocks"}, {"id": "choice_log"}],
            log_refs=[f"timeline:route:{node['node']}"],
        )

    make_screen(
        screens,
        "tactical_encounter_start",
        "Tactical Encounter",
        {
            "encounter": "Reliquary Gate Ambush",
            "rules": {"movement": 6, "main_action": 1, "bonus_action": 1, "reaction": 1},
            "squad": squad,
        },
        [{"id": "hex_battlefield"}, {"id": "initiative"}, {"id": "objective_panel"}],
    )

    rounds, tactical_result = resolve_tactical_encounter(seed, squad)
    for round_doc in rounds:
        make_screen(
            screens,
            "tactical_round",
            f"Tactical Round {round_doc['round']}",
            round_doc,
            [{"id": "battlefield_frame"}, {"id": "action_log"}, {"id": "hp_bars"}, {"id": "objective_progress"}],
            log_refs=[f"tactical:round:{round_doc['round']}"],
        )
        timeline.append({"type": "tactical_round", "round": round_doc["round"], "summary": round_doc})

    make_screen(
        screens,
        "post_battle_decision",
        "Post-Battle Decision",
        {"tactical_result": tactical_result, "squad": squad, "director_clocks": clocks},
        [{"id": "loot_panel"}, {"id": "injury_panel"}, {"id": "gm_options"}],
        next_decisions=[
            {"id": "extract_now", "label": "Extract now with secured relic"},
            {"id": "press_on", "label": "Push deeper for more loot"},
            {"id": "spend_supplies", "label": "Spend supplies to stabilize squad"},
        ],
    )

    extract_success = tactical_result["victory"] and len(tactical_result["heroes_alive"]) >= 2
    director_event(timeline, clocks, "extraction_resolution", {"extraction_timer": -6, "threat": 1})
    make_screen(
        screens,
        "extraction",
        "Extraction",
        {"success": extract_success, "heroes_alive": tactical_result["heroes_alive"], "director_clocks": clocks},
        [{"id": "extraction_beacon"}, {"id": "survivor_panel"}, {"id": "timer_panel"}],
    )

    progression = apply_progression(squad, camp, tactical_result)
    make_screen(
        screens,
        "run_summary",
        "Run Summary",
        {
            "success": extract_success,
            "mission": MISSION["id"],
            "key_stats": {
                "tactical_rounds": len(rounds),
                "objective_progress": tactical_result["objective_progress"],
                "noise": tactical_result["noise"],
                "heroes_alive": len(tactical_result["heroes_alive"]),
            },
            "rewards": progression["rewards"],
        },
        [{"id": "result_banner"}, {"id": "stat_cards"}, {"id": "rewards"}],
    )
    make_screen(
        screens,
        "progression",
        "Hero Progression",
        {"heroes": progression["hero_progress"]},
        [{"id": "hero_xp_cards"}, {"id": "trait_changes"}, {"id": "injuries"}],
    )
    make_screen(
        screens,
        "camp_return",
        "Camp Return",
        {"camp": progression["camp"], "persistent_events": progression["camp"]["persistent_events"]},
        [{"id": "camp_facilities"}, {"id": "resources"}, {"id": "next_campaign_hooks"}],
        next_decisions=[
            {"id": "upgrade_armory", "label": "Upgrade armory if scrap allows"},
            {"id": "treat_injuries", "label": "Spend medicae to clear injuries"},
            {"id": "change_directives", "label": "Players update hero directives before next campaign"},
        ],
    )

    full_run = {
        "schema": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "campaign_id": CAMPAIGN_ID,
        "seed": seed,
        "setting": "blackstar_far_future_grimdark_original_safe",
        "mission": MISSION,
        "player_slots": PLAYER_SLOTS,
        "player_directives": PLAYER_DIRECTIVES,
        "setting_profile": SETTING_PROFILE,
        "hero_pool": HERO_POOL,
        "initial_camp": BASE_CAMP,
        "final_camp": progression["camp"],
        "timeline": timeline,
        "tactical_rounds": rounds,
        "tactical_result": tactical_result,
        "screen_payloads": screens,
        "replay_index": [{"time_index": s["time_index"], "screen_id": s["screen_id"], "stage": s["stage"]} for s in screens],
    }
    return full_run


def write_outputs(full_run: Dict[str, Any], root: str | None = None) -> Dict[str, str]:
    repo_root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = {
        "directives": os.path.join(repo_root, "game-data", "agent-directives", "campaign01_v041_player_directives.json"),
        "full_run": os.path.join(repo_root, "game-data", "campaign-runs", "campaign01_v041_full_run.json"),
        "screens": os.path.join(repo_root, "game-data", "screen-payloads", "campaign01_v041_screen_payloads.json"),
        "camp": os.path.join(repo_root, "game-data", "camp", "camp_state_after_campaign01_v041.json"),
    }
    for path in paths.values():
        os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(paths["directives"], "w", encoding="utf-8") as f:
        json.dump(full_run["player_directives"], f, ensure_ascii=False, indent=2)
    with open(paths["full_run"], "w", encoding="utf-8") as f:
        json.dump(full_run, f, ensure_ascii=False, indent=2)
    with open(paths["screens"], "w", encoding="utf-8") as f:
        json.dump(
            {
                "schema": "blackstar-raiders.screen-payloads.v0.41",
                "run_id": full_run["run_id"],
                "screen_count": len(full_run["screen_payloads"]),
                "screens": full_run["screen_payloads"],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    with open(paths["camp"], "w", encoding="utf-8") as f:
        json.dump(full_run["final_camp"], f, ensure_ascii=False, indent=2)
    return paths


def validate_full_run(full_run: Dict[str, Any]) -> List[str]:
    errors = []
    screens = full_run["screen_payloads"]
    required_stages = [
        "hero_selection",
        "squad_lock_in",
        "campaign_briefing",
        "camp_loadout",
        "drop_in",
        "route_map",
        "tactical_encounter_start",
        "tactical_round",
        "post_battle_decision",
        "extraction",
        "run_summary",
        "progression",
        "camp_return",
    ]
    stages = [s["stage"] for s in screens]
    for stage in required_stages:
        if stage not in stages:
            errors.append(f"missing screen stage {stage}")
    for idx, screen in enumerate(screens):
        for key in ("screen_id", "stage", "title", "time_index", "state", "ui_panels", "log_refs", "render_contract", "next_decisions"):
            if key not in screen:
                errors.append(f"screen {idx} missing {key}")
        if screen.get("time_index") != idx:
            errors.append(f"screen {idx} has bad time_index {screen.get('time_index')}")
    for round_doc in full_run["tactical_rounds"]:
        for hero_state in round_doc["squad_state"]:
            if hero_state["hp"] < 0:
                errors.append(f"negative hp for {hero_state['player']} round {round_doc['round']}")
    if full_run["final_camp"]["resources"]["scrap"] < full_run["initial_camp"]["resources"]["scrap"]:
        errors.append("camp scrap did not progress")
    players = [slot["player"] for slot in full_run["player_slots"]]
    if players != ["EZ", "Candy Peace", "Dr.Feed"]:
        errors.append(f"bad player slots {players}")
    if len(full_run["replay_index"]) != len(screens):
        errors.append("replay index length mismatch")
    return errors


def main() -> None:
    full_run = simulate_campaign()
    errors = validate_full_run(full_run)
    paths = write_outputs(full_run)
    print(
        json.dumps(
            {
                "run_id": full_run["run_id"],
                "screen_count": len(full_run["screen_payloads"]),
                "tactical_rounds": len(full_run["tactical_rounds"]),
                "victory": full_run["tactical_result"]["victory"],
                "heroes_alive": full_run["tactical_result"]["heroes_alive"],
                "camp_tier": full_run["final_camp"]["tier"],
                "validation_errors": errors,
                "outputs": paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
