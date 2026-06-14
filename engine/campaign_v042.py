"""Blackstar Raiders campaign orchestrator v0.42.

v0.42 keeps v0.41's screen pipeline, but replaces ad hoc demo stats with the
calculated rules spine from rules_v042.py.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List

import rules_v042 as rules


SCHEMA_VERSION = "blackstar-raiders.campaign-run.v0.42"
SCREEN_SCHEMA = "blackstar-raiders.screen-payloads.v0.42"
CAMPAIGN_ID = "blackstar_campaign_001"
RUN_ID = "blackstar_campaign_001_run_001_v042"
SEED = "blackstar-v042-demo-001"


SETTING_PROFILE: Dict[str, Any] = {
    "production_mode": "blackstar_raiders_original_safe",
    "reference_target": "hard WH40 latest-edition grimdark planetary raid mood",
    "tone": ["brutal", "gothic", "military", "high-risk", "no-soft-fantasy"],
    "public_asset_rule": "use original names and symbols unless explicitly marked as private fan/reference work",
    "setting_swap_rule": "mechanics stay in rules_v042; names, visuals, factions, and mission dressing can change by setting pack",
}


AI_ROLES: Dict[str, Dict[str, str]] = {
    "ai_director": {
        "job": "pace threat clocks, extraction pressure, noise escalation, and campaign events",
        "writes": "director_clock_log",
    },
    "ai_gm": {
        "job": "turn computed state into player-facing choices and consequences",
        "writes": "gm_options, decision prompts, consequence previews",
    },
    "ai_heroes": {
        "job": "convert player directives into movement, main action, bonus action, and reaction reserve",
        "writes": "hero action plans with score components",
    },
    "ai_enemies": {
        "job": "apply threat pressure, target bias, and objective denial",
        "writes": "enemy action log",
    },
    "engine": {
        "job": "resolve numbers deterministically from rules_v042",
        "writes": "state, logs, screen payloads, progression",
    },
}


PLAYER_SLOTS: List[Dict[str, str]] = [
    {"player": "EZ", "assigned_hero": "sanctioned_prism_psyker"},
    {"player": "Candy Peace", "assigned_hero": "void_chaplain"},
    {"player": "Dr.Feed", "assigned_hero": "plague_surgeon"},
]


PLAYER_DIRECTIVES: Dict[str, Dict[str, Any]] = {
    "EZ": {
        "mobility": 0.65,
        "objective": 0.9,
        "greed": 0.35,
        "survival": 0.45,
        "ability": 0.85,
        "consumable": 0.35,
        "quest": 0.75,
        "ability_bias": "control_priority",
        "character_notes": ["pushes anomaly objectives", "accepts controlled warp risk"],
    },
    "Candy Peace": {
        "mobility": 0.35,
        "objective": 0.7,
        "greed": 0.25,
        "survival": 0.9,
        "ability": 0.45,
        "consumable": 0.45,
        "quest": 0.35,
        "ability_bias": "guard_allies",
        "character_notes": ["holds the line", "keeps Dr.Feed covered"],
    },
    "Dr.Feed": {
        "mobility": 0.3,
        "objective": 0.55,
        "greed": 0.2,
        "survival": 0.95,
        "ability": 0.7,
        "consumable": 0.9,
        "quest": 0.45,
        "ability_bias": "heal_early",
        "character_notes": ["spends supplies before collapse", "keeps damaged heroes operational"],
    },
}


BASE_CAMP: Dict[str, Any] = {
    "id": "blackstar_camp_vesper_reliquary",
    "name": "Vesper Reliquary Camp",
    "tier": 1,
    "resources": {"scrap": 18, "relic_shards": 4, "medicae": 3, "intel": 3},
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
    "rewards": {"relic_shards": 6, "scrap": 12, "intel": 3, "xp": 130},
}


ROUTE_NODES: List[Dict[str, Any]] = [
    {
        "node": "ash_causeway",
        "choice": "fast route through shell-fire",
        "cost": {"extraction_timer": -4, "noise": 1},
        "screen_focus": "tempo",
    },
    {
        "node": "dead_vox_shrine",
        "choice": "scan secondary objective",
        "cost": {"extraction_timer": -5, "doom": 1},
        "reward": {"intel": 1},
        "screen_focus": "quest",
    },
    {
        "node": "black_reliquary_gate",
        "choice": "breach vault perimeter",
        "cost": {"threat": 1, "noise": 1},
        "screen_focus": "combat_setup",
    },
]


def make_screen(
    screens: List[Dict[str, Any]],
    stage: str,
    title: str,
    state: Dict[str, Any],
    ui_panels: List[Dict[str, Any]],
    log_refs: List[str] | None = None,
    next_decisions: List[Dict[str, Any]] | None = None,
    calculation_refs: List[str] | None = None,
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
        "calculation_refs": calculation_refs or ["engine/rules_v042.py"],
        "render_contract": {
            "source_of_truth": ["state", "ui_panels", "log_refs", "calculation_refs"],
            "must_show": sorted(state.keys()),
            "must_not_invent": [
                "stats outside rules_v042 formulas",
                "hero actions not present in action score logs",
                "dead/alive status not in state",
                "player names other than EZ, Candy Peace, Dr.Feed",
                "official WH40 logos or protected names in public assets",
            ],
        },
        "next_decisions": next_decisions or [],
    }
    screens.append(screen)
    return screen


def director_event(timeline: List[Dict[str, Any]], clocks: Dict[str, int], event: str, delta: Dict[str, int], note: str) -> None:
    for key, value in delta.items():
        clocks[key] = max(0, clocks.get(key, 0) + value)
    timeline.append({"type": "director", "event": event, "delta": delta, "clocks": copy.deepcopy(clocks), "note": note})


def build_patch_contract(full_run: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "schema": "blackstar-raiders.patch-intake.v0.42",
        "purpose": "Allow ChatGPT Web, Notion, GitHub, or local agents to propose versioned game changes without editing canon directly.",
        "allowed_patch_targets": [
            "player_directives",
            "hero_assignment_demo_seed",
            "loadout_priority",
            "action_score_weight",
            "screen_copy",
            "research_question",
            "visual_prompt",
        ],
        "required_fields": ["patch_id", "source", "target", "reason", "proposed_change", "acceptance_check"],
        "asset_policy": {
            "heavy_assets": "store in Google Drive or local artifact folder, then reference by manifest",
            "repo_assets": "keep only small JSON/spec/test fixtures in Git",
        },
        "current_run": {"run_id": full_run["run_id"], "schema": full_run["schema"]} if full_run else None,
    }


def simulate_campaign(seed: str = SEED) -> Dict[str, Any]:
    screens: List[Dict[str, Any]] = []
    timeline: List[Dict[str, Any]] = []
    camp = copy.deepcopy(BASE_CAMP)
    clocks = {"threat": 4, "noise": 0, "doom": 2, "extraction_timer": MISSION["extraction_window"]}

    roster = rules.build_roster()
    make_screen(
        screens,
        "hero_selection",
        "Hero Selection",
        {
            "player_slots": [{"player": slot["player"], "status": "unassigned"} for slot in PLAYER_SLOTS],
            "hero_pool": roster,
            "rules_summary": rules.rules_summary(),
            "setting_profile": SETTING_PROFILE,
        },
        [{"id": "reserved_player_slots"}, {"id": "hero_pool_grid"}, {"id": "rules_preview"}, {"id": "mission_sidebar"}],
        next_decisions=[{"id": "assign_squad", "label": "Assign heroes for this run"}],
    )

    squad, post_loadout_resources, loadout_log = rules.assemble_squad(PLAYER_SLOTS, PLAYER_DIRECTIVES, camp["resources"])
    make_screen(
        screens,
        "squad_lock_in",
        "Squad Lock-In",
        {
            "squad": squad,
            "directives": {k: rules.normalize_directive(v) for k, v in PLAYER_DIRECTIVES.items()},
            "ai_roles": AI_ROLES,
        },
        [{"id": "assigned_slots"}, {"id": "directive_cards"}, {"id": "ai_role_matrix"}],
        next_decisions=[{"id": "confirm_directives", "label": "Confirm player directives"}],
    )

    timeline.append({"type": "campaign_start", "campaign": CAMPAIGN_ID, "mission": MISSION["id"], "rules": rules.SCHEMA_VERSION})
    make_screen(
        screens,
        "campaign_briefing",
        "Campaign Briefing",
        {"mission": MISSION, "camp": camp, "director_clocks": clocks, "ai_director": AI_ROLES["ai_director"]},
        [{"id": "mission_objectives"}, {"id": "risk_panel"}, {"id": "reward_panel"}, {"id": "director_clocks"}],
    )

    camp["resources"] = post_loadout_resources
    make_screen(
        screens,
        "camp_loadout",
        "Camp Loadout",
        {"camp": camp, "loadout_log": loadout_log, "squad_after_loadout": [_hero_screen_doc(h) for h in squad]},
        [{"id": "camp_resources"}, {"id": "loadout_budget"}, {"id": "stat_delta_cards"}],
    )

    director_event(timeline, clocks, "drop_in_under_fire", {"noise": 1, "extraction_timer": -3}, "Landing starts hot; the director adds pressure before the first route choice.")
    make_screen(
        screens,
        "drop_in",
        "Drop-In",
        {"zone": "Korvash Prime / ash landing deck", "director_clocks": clocks, "squad": [_hero_screen_doc(h) for h in squad]},
        [{"id": "landing_zone"}, {"id": "clock_panel"}, {"id": "squad_readiness"}],
        log_refs=["timeline:drop_in_under_fire"],
    )

    route_log = []
    make_screen(
        screens,
        "strategic_map_start",
        "Strategic Map",
        {"route_nodes": ROUTE_NODES, "director_clocks": clocks, "camp_resources": camp["resources"]},
        [{"id": "hex_route_map"}, {"id": "route_options"}, {"id": "fog_and_threat"}],
    )
    for idx, node in enumerate(ROUTE_NODES, start=1):
        director_event(timeline, clocks, f"route:{node['node']}", node["cost"], f"AI Director resolves route cost for {node['choice']}.")
        if "reward" in node:
            for key, value in node["reward"].items():
                camp["resources"][key] = camp["resources"].get(key, 0) + value
        route_entry = {"index": idx, "node": node, "clocks_after": copy.deepcopy(clocks), "camp_resources_after": copy.deepcopy(camp["resources"])}
        route_log.append(route_entry)
        make_screen(
            screens,
            "strategic_turn",
            f"Strategic Turn {idx}",
            route_entry,
            [{"id": "hex_route_frame"}, {"id": "director_clock_delta"}, {"id": "gm_route_prompt"}],
            log_refs=[f"timeline:route:{node['node']}"],
        )

    make_screen(
        screens,
        "tactical_encounter_start",
        "Tactical Encounter",
        {
            "encounter": "Reliquary Gate Ambush",
            "rules": {
                "grid": "hex",
                "movement": "derived movement from rules_v042",
                "main_action": 1,
                "bonus_action": 1,
                "reaction": "reserved when survival directive >= 0.7",
            },
            "squad": [_hero_screen_doc(h) for h in squad],
            "enemy_group": rules.ENEMY_GROUP,
        },
        [{"id": "hex_battlefield"}, {"id": "initiative_ladder"}, {"id": "objective_panel"}, {"id": "action_budget_legend"}],
    )

    tactical_rounds, tactical_result = rules.resolve_tactical_encounter(seed, squad, clocks, max_rounds=4)
    for round_doc in tactical_rounds:
        make_screen(
            screens,
            "tactical_round",
            f"Tactical Round {round_doc['round']}",
            round_doc,
            [{"id": "battlefield_frame"}, {"id": "hero_action_scores"}, {"id": "enemy_pressure"}, {"id": "objective_progress"}],
            log_refs=[f"tactical:round:{round_doc['round']}"],
            calculation_refs=["engine/rules_v042.py::resolve_tactical_encounter"],
        )
        timeline.append({"type": "tactical_round", "round": round_doc["round"], "summary": round_doc})

    gm_options = [
        {"id": "extract_now", "label": "Extract now", "consequence": "Bank rewards, preserve survivors, increase camp stability."},
        {"id": "press_on", "label": "Push deeper", "consequence": "More relic chance, more heat, higher injury risk."},
        {"id": "spend_supplies", "label": "Spend supplies", "consequence": "Reduce injury risk before extraction."},
    ]
    make_screen(
        screens,
        "gm_interlude",
        "AI GM Interlude",
        {"tactical_result": tactical_result, "gm_options": gm_options, "ai_gm": AI_ROLES["ai_gm"]},
        [{"id": "gm_consequence_cards"}, {"id": "squad_condition"}, {"id": "loot_preview"}],
        next_decisions=gm_options,
    )

    extract_success = tactical_result["victory"] and len(tactical_result["heroes_alive"]) >= 2
    director_event(timeline, clocks, "extraction_resolution", {"extraction_timer": -6, "threat": 1}, "Extraction beacon resolves after tactical result and noise.")
    make_screen(
        screens,
        "extraction",
        "Extraction",
        {
            "success": extract_success,
            "readiness": tactical_result["extraction_readiness"],
            "heroes_alive": tactical_result["heroes_alive"],
            "director_clocks": clocks,
        },
        [{"id": "extraction_beacon"}, {"id": "survivor_panel"}, {"id": "timer_panel"}, {"id": "failure_conditions"}],
    )

    progression = rules.apply_progression(squad, camp, tactical_result, MISSION["rewards"])
    make_screen(
        screens,
        "run_summary",
        "Run Summary",
        {
            "success": extract_success,
            "mission": MISSION["id"],
            "key_stats": {
                "tactical_rounds": tactical_result["rounds"],
                "objective_progress": tactical_result["objective_progress"],
                "noise": tactical_result["noise"],
                "heroes_alive": len(tactical_result["heroes_alive"]),
                "extraction_readiness": tactical_result["extraction_readiness"],
            },
            "rewards": progression["rewards"],
        },
        [{"id": "result_banner"}, {"id": "stat_cards"}, {"id": "rewards"}, {"id": "highlight_timeline"}],
    )
    make_screen(
        screens,
        "progression",
        "Hero Progression",
        {"heroes": progression["hero_progress"], "progression_rules": "150 xp per level; traits inferred from directives and survival state"},
        [{"id": "hero_xp_cards"}, {"id": "trait_changes"}, {"id": "injuries"}],
    )
    make_screen(
        screens,
        "camp_return",
        "Camp Return",
        {"camp": progression["camp"], "persistent_events": progression["camp"]["persistent_events"]},
        [{"id": "camp_facilities"}, {"id": "resources"}, {"id": "heat_morale"}, {"id": "next_campaign_hooks"}],
        next_decisions=[
            {"id": "upgrade_armory", "label": "Upgrade armory if scrap allows"},
            {"id": "treat_injuries", "label": "Spend medicae to clear injuries"},
            {"id": "change_directives", "label": "Players update directives before next campaign"},
        ],
    )

    full_run = {
        "schema": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "campaign_id": CAMPAIGN_ID,
        "seed": seed,
        "setting": "blackstar_far_future_grimdark_original_safe",
        "setting_profile": SETTING_PROFILE,
        "rules_summary": rules.rules_summary(),
        "ai_roles": AI_ROLES,
        "mission": MISSION,
        "player_slots": PLAYER_SLOTS,
        "player_directives": {k: rules.normalize_directive(v) for k, v in PLAYER_DIRECTIVES.items()},
        "hero_pool": roster,
        "initial_camp": BASE_CAMP,
        "final_camp": progression["camp"],
        "route_log": route_log,
        "timeline": timeline,
        "tactical_rounds": tactical_rounds,
        "tactical_result": tactical_result,
        "screen_payloads": screens,
        "replay_index": [{"time_index": s["time_index"], "screen_id": s["screen_id"], "stage": s["stage"]} for s in screens],
    }
    full_run["patch_contract"] = build_patch_contract(full_run)
    return full_run


def _hero_screen_doc(hero: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "player": hero.get("player"),
        "hero_id": hero["id"],
        "hero": hero["name"],
        "role": hero["role"],
        "attributes": hero["attributes"],
        "derived": hero["derived"],
        "hp": hero.get("hp", hero["derived"]["max_hp"]),
        "max_hp": hero.get("max_hp", hero["derived"]["max_hp"]),
        "loadout": hero.get("loadout", []),
        "directive": hero.get("directive"),
    }


def validate_full_run(full_run: Dict[str, Any]) -> List[str]:
    errors = []
    errors.extend(rules.validate_rules_model())
    screens = full_run["screen_payloads"]
    required_stages = [
        "hero_selection",
        "squad_lock_in",
        "campaign_briefing",
        "camp_loadout",
        "drop_in",
        "strategic_map_start",
        "strategic_turn",
        "tactical_encounter_start",
        "tactical_round",
        "gm_interlude",
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
        required = ("screen_id", "stage", "title", "time_index", "state", "ui_panels", "log_refs", "calculation_refs", "render_contract", "next_decisions")
        for key in required:
            if key not in screen:
                errors.append(f"screen {idx} missing {key}")
        if screen.get("time_index") != idx:
            errors.append(f"screen {idx} has bad time_index {screen.get('time_index')}")
    if stages[0] != "hero_selection":
        errors.append("first screen is not hero_selection")
    if stages[-1] != "camp_return":
        errors.append("last screen is not camp_return")
    if stages.count("tactical_round") < 3:
        errors.append("expected at least 3 tactical rounds")
    if stages.count("strategic_turn") != len(ROUTE_NODES):
        errors.append("strategic turn count does not match route nodes")
    for round_doc in full_run["tactical_rounds"]:
        for hero_state in round_doc["squad_state"]:
            if hero_state["hp"] < 0:
                errors.append(f"negative hp for {hero_state['player']} round {round_doc['round']}")
        for action in round_doc["hero_actions"]:
            if action["budget"]["main"] != 1 or action["budget"]["bonus"] != 1:
                errors.append(f"bad action budget for {action['actor']} round {round_doc['round']}")
            if not action["main_action"]["score_components"]:
                errors.append(f"missing main score components for {action['actor']} round {round_doc['round']}")
    players = [slot["player"] for slot in full_run["player_slots"]]
    if players != ["EZ", "Candy Peace", "Dr.Feed"]:
        errors.append(f"bad player slots {players}")
    first = screens[0]["state"]["player_slots"]
    if any(slot["status"] != "unassigned" for slot in first):
        errors.append("hero selection slots must start unassigned")
    if "WH40" not in full_run["setting_profile"]["reference_target"]:
        errors.append("setting reference target missing WH40")
    if "patch_contract" not in full_run:
        errors.append("missing patch contract")
    if len(full_run["replay_index"]) != len(screens):
        errors.append("replay index length mismatch")
    return errors


def write_outputs(full_run: Dict[str, Any], root: str | None = None) -> Dict[str, str]:
    repo_root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = {
        "rules": os.path.join(repo_root, "game-data", "rules", "rules_v042_summary.json"),
        "directives": os.path.join(repo_root, "game-data", "agent-directives", "campaign01_v042_player_directives.json"),
        "full_run": os.path.join(repo_root, "game-data", "campaign-runs", "campaign01_v042_full_run.json"),
        "screens": os.path.join(repo_root, "game-data", "screen-payloads", "campaign01_v042_screen_payloads.json"),
        "camp": os.path.join(repo_root, "game-data", "camp", "camp_state_after_campaign01_v042.json"),
        "patch_contract": os.path.join(repo_root, "game-data", "patches", "campaign01_v042_patch_contract.json"),
    }
    for path in paths.values():
        os.makedirs(os.path.dirname(path), exist_ok=True)

    _write_json(paths["rules"], full_run["rules_summary"])
    _write_json(paths["directives"], full_run["player_directives"])
    _write_json(paths["full_run"], full_run)
    _write_json(
        paths["screens"],
        {"schema": SCREEN_SCHEMA, "run_id": full_run["run_id"], "screen_count": len(full_run["screen_payloads"]), "screens": full_run["screen_payloads"]},
    )
    _write_json(paths["camp"], full_run["final_camp"])
    _write_json(paths["patch_contract"], full_run["patch_contract"])
    return paths


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


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
                "rules": full_run["rules_summary"]["schema"],
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
