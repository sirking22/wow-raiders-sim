"""Blackstar Raiders full campaign runtime v0.44.

v0.44 joins the calculated v0.42 campaign spine with the BattleV09 tactical
runtime. The goal is an end-to-end, replayable campaign run where every screen
is derived from state, logs, and calculation references.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List

import battle_v09
import campaign_v042 as base
import rules_v042 as rules


SCHEMA_VERSION = "blackstar-raiders.campaign-run.v0.44"
SCREEN_SCHEMA = "blackstar-raiders.screen-payloads.v0.44"
CAMPAIGN_ID = "blackstar_campaign_001"
RUN_ID = "blackstar_campaign_001_run_001_v044"
SEED = "blackstar-v044-full-loop-001"


def simulate_campaign(seed: str = SEED) -> Dict[str, Any]:
    screens: List[Dict[str, Any]] = []
    timeline: List[Dict[str, Any]] = []
    ai_turn_log: List[Dict[str, Any]] = []
    camp = copy.deepcopy(base.BASE_CAMP)
    clocks = {"threat": 4, "noise": 0, "doom": 2, "extraction_timer": base.MISSION["extraction_window"]}

    roster = rules.build_roster()
    make_screen(
        screens,
        "hero_selection",
        "Hero Selection",
        {
            "player_slots": [{"player": slot["player"], "status": "unassigned"} for slot in base.PLAYER_SLOTS],
            "hero_pool": roster,
            "rules_summary": rules.rules_summary(),
            "setting_profile": _setting_profile(),
        },
        ["reserved_player_slots", "hero_pool_grid", "rules_preview", "mission_sidebar"],
        next_decisions=[{"id": "assign_squad", "label": "Assign heroes for this run"}],
        calculation_refs=["engine/rules_v042.py::build_roster", "engine/rules_v042.py::rules_summary"],
    )

    squad, post_loadout_resources, loadout_log = rules.assemble_squad(
        base.PLAYER_SLOTS,
        base.PLAYER_DIRECTIVES,
        camp["resources"],
    )
    normalized_directives = {k: rules.normalize_directive(v) for k, v in base.PLAYER_DIRECTIVES.items()}

    make_screen(
        screens,
        "squad_lock_in",
        "Squad Lock-In",
        {
            "squad": [_hero_screen_doc(hero) for hero in squad],
            "directives": normalized_directives,
            "ai_roles": base.AI_ROLES,
        },
        ["assigned_slots", "directive_cards", "ai_role_matrix"],
        next_decisions=[{"id": "confirm_directives", "label": "Confirm player directives"}],
        calculation_refs=["engine/rules_v042.py::assemble_squad", "engine/rules_v042.py::normalize_directive"],
    )

    timeline.append({"type": "campaign_start", "campaign": CAMPAIGN_ID, "mission": base.MISSION["id"], "rules": rules.SCHEMA_VERSION})
    ai_turn_log.append({"actor": "ai_director", "stage": "campaign_briefing", "decision": "open with high threat and visible extraction pressure"})
    make_screen(
        screens,
        "campaign_briefing",
        "Campaign Briefing",
        {
            "mission": base.MISSION,
            "camp": camp,
            "director_clocks": copy.deepcopy(clocks),
            "ai_director": base.AI_ROLES["ai_director"],
            "campaign_structure": _campaign_structure(),
        },
        ["mission_objectives", "risk_panel", "reward_panel", "director_clocks", "campaign_structure"],
        calculation_refs=["engine/campaign_v044.py::_campaign_structure"],
    )

    camp["resources"] = post_loadout_resources
    make_screen(
        screens,
        "camp_loadout",
        "Camp Loadout",
        {
            "camp": copy.deepcopy(camp),
            "loadout_log": loadout_log,
            "squad_after_loadout": [_hero_screen_doc(hero) for hero in squad],
        },
        ["camp_resources", "loadout_budget", "stat_delta_cards"],
        calculation_refs=["engine/rules_v042.py::recommend_loadout", "engine/rules_v042.py::apply_loadout"],
    )

    _director_event(timeline, ai_turn_log, clocks, "drop_in_under_fire", {"noise": 1, "extraction_timer": -3}, "Landing starts hot; the director adds pressure before the first route choice.")
    make_screen(
        screens,
        "drop_in",
        "Drop-In",
        {
            "zone": "Korvash Prime / ash landing deck",
            "director_clocks": copy.deepcopy(clocks),
            "squad": [_hero_screen_doc(hero) for hero in squad],
        },
        ["landing_zone", "clock_panel", "squad_readiness"],
        log_refs=["timeline:drop_in_under_fire"],
    )

    route_log: List[Dict[str, Any]] = []
    make_screen(
        screens,
        "strategic_map_start",
        "Strategic Map",
        {
            "route_nodes": base.ROUTE_NODES,
            "director_clocks": copy.deepcopy(clocks),
            "camp_resources": copy.deepcopy(camp["resources"]),
        },
        ["hex_route_map", "route_options", "fog_and_threat"],
        calculation_refs=["engine/campaign_v042.py::ROUTE_NODES"],
    )

    for idx, node in enumerate(base.ROUTE_NODES, start=1):
        _director_event(timeline, ai_turn_log, clocks, f"route:{node['node']}", node["cost"], f"AI Director resolves route cost for {node['choice']}.")
        if "reward" in node:
            for key, value in node["reward"].items():
                camp["resources"][key] = camp["resources"].get(key, 0) + value
        route_entry = {
            "index": idx,
            "node": node,
            "clocks_after": copy.deepcopy(clocks),
            "camp_resources_after": copy.deepcopy(camp["resources"]),
        }
        route_log.append(route_entry)
        make_screen(
            screens,
            "strategic_turn",
            f"Strategic Turn {idx}",
            route_entry,
            ["hex_route_frame", "director_clock_delta", "gm_route_prompt"],
            log_refs=[f"timeline:route:{node['node']}"],
        )

    battle_run = battle_v09.build_battle_run(seed=f"{seed}:battle")
    if battle_run["validation_errors"]:
        timeline.append({"type": "battle_validation_error", "errors": battle_run["validation_errors"]})

    make_screen(
        screens,
        "tactical_encounter_start",
        "Tactical Encounter",
        {
            "encounter": "Reliquary Gate Ambush",
            "battle_run_id": battle_run["run_id"],
            "grid": battle_run["grid"],
            "initial_frame": battle_run["frames"][0],
            "battle_rules": {
                "movement": "path cost <= movement budget <= derived movement",
                "main_action": 1,
                "bonus_action": 1,
                "reaction": "reserved when survival directive >= 0.7",
            },
        },
        ["hex_battlefield", "initiative_ladder", "objective_panel", "action_budget_legend"],
        calculation_refs=["engine/battle_v09.py::build_battle_run"],
    )

    for round_doc, frame in zip(battle_run["round_log"], battle_run["frames"][1:]):
        for action in round_doc["actions"]:
            ai_turn_log.append(_ai_turn_from_battle_action(action))
        make_screen(
            screens,
            "battle_v09_round",
            f"BattleV09 Round {round_doc['round']}",
            {"round": round_doc, "frame": frame},
            ["battlefield_frame", "action_stack", "score_components", "hp_clocks"],
            log_refs=[f"battle:{battle_run['run_id']}:round:{round_doc['round']}"],
            calculation_refs=["engine/battle_v09.py::_resolve_hero_turn", "engine/rules_v042.py::choose_action"],
        )
        timeline.append({"type": "battle_round", "round": round_doc["round"], "battle_run_id": battle_run["run_id"]})

    _apply_battle_state_to_squad(squad, battle_run)
    tactical_result = _tactical_result_from_battle(battle_run)
    highlights = _build_highlights(battle_run)
    balance_audit = _build_balance_audit(battle_run)

    gm_options = [
        {"id": "extract_now", "label": "Extract now", "consequence": "Bank rewards, preserve survivors, increase camp stability.", "selected": True},
        {"id": "press_on", "label": "Push deeper", "consequence": "More relic chance, more heat, higher injury risk.", "selected": False},
        {"id": "spend_supplies", "label": "Spend supplies", "consequence": "Reduce injury risk before extraction.", "selected": False},
    ]
    ai_turn_log.append({"actor": "ai_gm", "stage": "gm_interlude", "decision": "recommend extract_now after battle readiness reached 100"})
    make_screen(
        screens,
        "gm_interlude",
        "AI GM Interlude",
        {
            "battle_result": battle_run["result"],
            "tactical_result": tactical_result,
            "gm_options": gm_options,
            "ai_gm": base.AI_ROLES["ai_gm"],
        },
        ["gm_consequence_cards", "squad_condition", "loot_preview"],
        next_decisions=gm_options,
        calculation_refs=["engine/campaign_v044.py::_tactical_result_from_battle"],
    )

    _director_event(timeline, ai_turn_log, clocks, "extraction_resolution", {"extraction_timer": -6, "threat": 1}, "Extraction beacon resolves after tactical result and noise.")
    extract_success = tactical_result["victory"] and len(tactical_result["heroes_alive"]) >= 2
    make_screen(
        screens,
        "extraction",
        "Extraction",
        {
            "success": extract_success,
            "readiness": tactical_result["extraction_readiness"],
            "heroes_alive": tactical_result["heroes_alive"],
            "director_clocks": copy.deepcopy(clocks),
            "battle_clocks": battle_run["result"]["clocks"],
        },
        ["extraction_beacon", "survivor_panel", "timer_panel", "failure_conditions"],
        calculation_refs=["engine/battle_v09.py::_result"],
    )

    progression = rules.apply_progression(squad, camp, tactical_result, base.MISSION["rewards"])
    continuity_ledger = _build_continuity_ledger(squad, progression, battle_run, route_log, ai_turn_log)

    make_screen(
        screens,
        "run_highlights",
        "Run Highlights",
        {"highlights": highlights, "balance_audit": balance_audit, "battle_result": battle_run["result"]},
        ["highlight_cards", "damage_heal_objective", "balance_flags", "battle_replay_link"],
        calculation_refs=["engine/campaign_v044.py::_build_highlights", "engine/campaign_v044.py::_build_balance_audit"],
    )
    make_screen(
        screens,
        "run_summary",
        "Run Summary",
        {
            "success": extract_success,
            "mission": base.MISSION["id"],
            "key_stats": {
                "battle_rounds": battle_run["result"]["rounds"],
                "objective_progress": tactical_result["objective_progress"],
                "noise": tactical_result["noise"],
                "heroes_alive": len(tactical_result["heroes_alive"]),
                "extraction_readiness": tactical_result["extraction_readiness"],
            },
            "rewards": progression["rewards"],
        },
        ["result_banner", "stat_cards", "rewards", "highlight_timeline"],
    )
    make_screen(
        screens,
        "progression",
        "Hero Progression",
        {
            "heroes": progression["hero_progress"],
            "progression_rules": "150 xp per level; traits inferred from directives and survival state",
            "continuity_ledger_ref": continuity_ledger["ledger_id"],
        },
        ["hero_xp_cards", "trait_changes", "injuries"],
        calculation_refs=["engine/rules_v042.py::apply_progression"],
    )
    make_screen(
        screens,
        "camp_return",
        "Camp Return",
        {
            "camp": progression["camp"],
            "persistent_events": progression["camp"]["persistent_events"],
            "campaign_ledger": continuity_ledger,
        },
        ["camp_facilities", "resources", "heat_morale", "next_campaign_hooks"],
        next_decisions=[
            {"id": "upgrade_armory", "label": "Upgrade armory if scrap allows"},
            {"id": "treat_injuries", "label": "Spend medicae to clear injuries"},
            {"id": "change_directives", "label": "Players update directives before next campaign"},
        ],
    )
    make_screen(
        screens,
        "campaign_continuity",
        "Campaign Continuity",
        {
            "ledger": continuity_ledger,
            "next_run_hooks": [
                "route heat makes future extraction windows shorter",
                "Dr.Feed support identity is now mechanically proven",
                "balance pass should tune enemy lethality before visual production",
            ],
            "patch_contract_preview": build_patch_contract(None),
        },
        ["ledger_delta", "persistent_threads", "next_run_hooks", "patch_intake"],
        calculation_refs=["engine/campaign_v044.py::_build_continuity_ledger", "engine/campaign_v044.py::build_patch_contract"],
    )

    full_run = {
        "schema": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "campaign_id": CAMPAIGN_ID,
        "seed": seed,
        "setting": "blackstar_far_future_grimdark_original_safe",
        "setting_profile": _setting_profile(),
        "rules_summary": rules.rules_summary(),
        "ai_roles": base.AI_ROLES,
        "ai_turn_log": ai_turn_log,
        "mission": base.MISSION,
        "player_slots": base.PLAYER_SLOTS,
        "player_directives": normalized_directives,
        "hero_pool": roster,
        "initial_camp": base.BASE_CAMP,
        "final_camp": progression["camp"],
        "route_log": route_log,
        "timeline": timeline,
        "battle_run": battle_run,
        "tactical_rounds": battle_run["round_log"],
        "tactical_result": tactical_result,
        "highlights": highlights,
        "balance_audit": balance_audit,
        "continuity_ledger": continuity_ledger,
        "screen_payloads": screens,
    }
    full_run["replay_index"] = [
        {"time_index": screen["time_index"], "screen_id": screen["screen_id"], "stage": screen["stage"]}
        for screen in screens
    ]
    full_run["patch_contract"] = build_patch_contract(full_run)
    full_run["validation_errors"] = validate_full_run(full_run)
    return full_run


def make_screen(
    screens: List[Dict[str, Any]],
    stage: str,
    title: str,
    state: Dict[str, Any],
    ui_panels: List[str],
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
        "ui_panels": [{"id": panel} for panel in ui_panels],
        "log_refs": log_refs or [],
        "calculation_refs": calculation_refs or ["engine/campaign_v044.py"],
        "render_contract": {
            "source_of_truth": ["state", "log_refs", "calculation_refs"],
            "must_show": sorted(state.keys()),
            "must_not_invent": [
                "actions absent from battle_run.action_log",
                "stats outside rules_v042 formulas or battle_v09 logs",
                "player names other than EZ, Candy Peace, Dr.Feed",
                "official WH40 logos or protected names in public assets",
            ],
        },
        "next_decisions": next_decisions or [],
    }
    screens.append(screen)
    return screen


def build_patch_contract(full_run: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "schema": "blackstar-raiders.patch-intake.v0.44",
        "purpose": "Allow ChatGPT Web, Notion, GitHub, local files, and Google Drive asset manifests to propose versioned changes without editing canon directly.",
        "accepted_sources": ["ChatGPT Web", "Codex", "Notion", "GitHub PR", "Google Drive manifest", "local file packet"],
        "allowed_patch_targets": [
            "player_directives",
            "hero_assignment_demo_seed",
            "rules_v042_stat_formula",
            "action_score_weight",
            "battle_v09_runtime_rule",
            "campaign_v044_stage_order",
            "screen_copy",
            "setting_pack",
            "visual_prompt",
            "research_question",
        ],
        "required_fields": ["patch_id", "source", "target", "reason", "proposed_change", "acceptance_check"],
        "asset_policy": {
            "heavy_assets": "store in Google Drive or local artifact folder, then reference by manifest",
            "repo_assets": "keep JSON/spec/test fixtures and small text assets in Git",
        },
        "current_run": {"run_id": full_run["run_id"], "schema": full_run["schema"]} if full_run else None,
    }


def validate_full_run(full_run: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    errors.extend(rules.validate_rules_model())
    if full_run.get("schema") != SCHEMA_VERSION:
        errors.append("wrong schema")
    if full_run["battle_run"].get("validation_errors"):
        errors.append("battle run has validation errors")

    screens = full_run["screen_payloads"]
    stages = [screen["stage"] for screen in screens]
    required_stages = [
        "hero_selection",
        "squad_lock_in",
        "campaign_briefing",
        "camp_loadout",
        "drop_in",
        "strategic_map_start",
        "strategic_turn",
        "tactical_encounter_start",
        "battle_v09_round",
        "gm_interlude",
        "extraction",
        "run_highlights",
        "run_summary",
        "progression",
        "camp_return",
        "campaign_continuity",
    ]
    for stage in required_stages:
        if stage not in stages:
            errors.append(f"missing screen stage {stage}")
    if stages[0] != "hero_selection":
        errors.append("first screen is not hero_selection")
    if stages[-1] != "campaign_continuity":
        errors.append("last screen is not campaign_continuity")
    if stages.count("strategic_turn") != len(base.ROUTE_NODES):
        errors.append("strategic turn count does not match route nodes")
    if stages.count("battle_v09_round") != full_run["battle_run"]["result"]["rounds"]:
        errors.append("battle screen count does not match BattleV09 rounds")

    for idx, screen in enumerate(screens):
        required = ("screen_id", "stage", "title", "time_index", "state", "ui_panels", "log_refs", "calculation_refs", "render_contract", "next_decisions")
        for key in required:
            if key not in screen:
                errors.append(f"screen {idx} missing {key}")
        if screen.get("time_index") != idx:
            errors.append(f"screen {idx} has bad time_index {screen.get('time_index')}")
        if not screen.get("calculation_refs"):
            errors.append(f"screen {idx} missing calculation refs")
        if not screen.get("render_contract", {}).get("source_of_truth"):
            errors.append(f"screen {idx} missing source_of_truth")

    players = [slot["player"] for slot in full_run["player_slots"]]
    if players != list(rules.PLAYER_NAMES):
        errors.append(f"bad player slots {players}")
    first_slots = screens[0]["state"]["player_slots"]
    if any(slot["status"] != "unassigned" for slot in first_slots):
        errors.append("hero selection slots must start unassigned")

    dr_feed = next((actor for actor in full_run["battle_run"]["actors_initial"] if actor["id"] == "Dr.Feed"), None)
    if not dr_feed or dr_feed["role"] != "medic":
        errors.append("Dr.Feed must be native medic in integrated battle")
    if full_run["tactical_result"]["heroes_alive"] != ["EZ", "Candy Peace", "Dr.Feed"]:
        errors.append("expected all three heroes alive in demo run")
    if full_run["tactical_result"]["extraction_readiness"] < 60:
        errors.append("extraction readiness below success threshold")

    if len(full_run["replay_index"]) != len(screens):
        errors.append("replay index length mismatch")
    if "patch_contract" not in full_run:
        errors.append("missing patch contract")
    else:
        accepted = set(full_run["patch_contract"]["accepted_sources"])
        for source in ("ChatGPT Web", "Notion", "GitHub PR", "Google Drive manifest"):
            if source not in accepted:
                errors.append(f"patch contract missing source {source}")
    if not full_run.get("continuity_ledger", {}).get("hero_deltas"):
        errors.append("missing hero continuity ledger")
    if not full_run.get("balance_audit", {}).get("next_balance_targets"):
        errors.append("missing balance targets")
    return errors


def write_outputs(full_run: Dict[str, Any], root: str | None = None) -> Dict[str, str]:
    repo_root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = {
        "full_run": os.path.join(repo_root, "game-data", "campaign-runs", "campaign01_v044_full_run.json"),
        "screens": os.path.join(repo_root, "game-data", "screen-payloads", "campaign01_v044_screen_payloads.json"),
        "camp": os.path.join(repo_root, "game-data", "camp", "camp_state_after_campaign01_v044.json"),
        "ledger": os.path.join(repo_root, "game-data", "continuity", "campaign01_v044_continuity_ledger.json"),
        "patch_contract": os.path.join(repo_root, "game-data", "patches", "campaign01_v044_patch_contract.json"),
    }
    for path in paths.values():
        os.makedirs(os.path.dirname(path), exist_ok=True)
    _write_json(paths["full_run"], full_run)
    _write_json(
        paths["screens"],
        {"schema": SCREEN_SCHEMA, "run_id": full_run["run_id"], "screen_count": len(full_run["screen_payloads"]), "screens": full_run["screen_payloads"]},
    )
    _write_json(paths["camp"], full_run["final_camp"])
    _write_json(paths["ledger"], full_run["continuity_ledger"])
    _write_json(paths["patch_contract"], full_run["patch_contract"])
    return paths


def _setting_profile() -> Dict[str, Any]:
    profile = copy.deepcopy(base.SETTING_PROFILE)
    profile["reference_target"] = "hard WH40 latest-edition grimdark planetary raid mood"
    profile["canonical_player_nickname"] = "Dr.Feed"
    profile["public_name"] = "Blackstar Raiders"
    return profile


def _campaign_structure() -> Dict[str, Any]:
    return {
        "loop": [
            "hero_selection",
            "campaign_briefing",
            "camp_loadout",
            "route",
            "battle",
            "gm_interlude",
            "extraction",
            "highlights",
            "progression",
            "camp_return",
            "continuity",
        ],
        "persistent_objects": ["heroes", "camp", "resources", "traits", "injuries", "heat", "persistent_events"],
        "player_input_windows": ["before campaign", "GM interlude", "between campaigns"],
    }


def _director_event(
    timeline: List[Dict[str, Any]],
    ai_turn_log: List[Dict[str, Any]],
    clocks: Dict[str, int],
    event: str,
    delta: Dict[str, int],
    note: str,
) -> None:
    for key, value in delta.items():
        clocks[key] = max(0, clocks.get(key, 0) + value)
    doc = {"type": "director", "event": event, "delta": delta, "clocks": copy.deepcopy(clocks), "note": note}
    timeline.append(doc)
    ai_turn_log.append({"actor": "ai_director", "stage": event, "decision": note, "delta": delta, "clocks_after": copy.deepcopy(clocks)})


def _apply_battle_state_to_squad(squad: List[Dict[str, Any]], battle_run: Dict[str, Any]) -> None:
    final_heroes = {
        actor["id"]: actor
        for actor in battle_run["frames"][-1]["actors"]
        if actor["team"] == "heroes"
    }
    for hero in squad:
        final = final_heroes[hero["player"]]
        hero["hp"] = final["hp"]
        hero["max_hp"] = final["max_hp"]
        hero["injuries"] = list(hero.get("injuries", []))
        hero["traits"] = list(hero.get("traits", []))


def _tactical_result_from_battle(battle_run: Dict[str, Any]) -> Dict[str, Any]:
    result = battle_run["result"]
    enemies_remaining = [
        actor
        for actor in battle_run["frames"][-1]["actors"]
        if actor["team"] == "hostiles" and actor["hp"] > 0
    ]
    return {
        "victory": result["success"],
        "objective_progress": result["objective_progress"],
        "noise": result["clocks"]["noise"],
        "rounds": result["rounds"],
        "heroes_alive": result["heroes_alive"],
        "enemies_remaining": enemies_remaining,
        "extraction_readiness": result["extraction_readiness"],
    }


def _build_highlights(battle_run: Dict[str, Any]) -> Dict[str, Any]:
    by_actor: Dict[str, Dict[str, int]] = {}
    for action in battle_run["action_log"]:
        actor = action.get("actor")
        if not actor:
            continue
        stats = by_actor.setdefault(actor, {"damage": 0, "healing": 0, "objective": 0, "turns": 0})
        stats["turns"] += 1
        stats["objective"] += int(action.get("objective_delta", 0))
        for effect in action.get("effects", []):
            if effect["type"] == "damage":
                stats["damage"] += int(effect["value"])
            if effect["type"] == "heal":
                stats["healing"] += max(0, int(effect["after"]) - int(effect["before"]))
    mvp = sorted(by_actor.items(), key=lambda item: (item[1]["objective"] + item[1]["damage"] + item[1]["healing"], item[0]), reverse=True)[0][0]
    return {
        "by_actor": by_actor,
        "mvp_signal": mvp,
        "battle_result": battle_run["result"]["victory_type"],
        "replay_frames": [frame["frame_id"] for frame in battle_run["frames"]],
    }


def _build_balance_audit(battle_run: Dict[str, Any]) -> Dict[str, Any]:
    final = battle_run["result"]
    return {
        "status": "provisional_balance_trace",
        "checks": [
            "all heroes use equal 30-point attribute budget",
            "all derived stats come from rules_v042.derive_stats",
            "BattleV09 movement cost stays under derived movement",
            "main and bonus action budgets are explicit in every hero turn",
        ],
        "observations": {
            "success": final["success"],
            "hostiles_alive": len(final["hostiles_alive"]),
            "heroes_alive": len(final["heroes_alive"]),
            "extraction_readiness": final["extraction_readiness"],
            "objective_progress": final["objective_progress"],
        },
        "next_balance_targets": [
            "enemy lethality is too low if all hostiles survive but extraction is trivial",
            "objective progress reaches target very quickly; tune objective_power after more runs",
            "stat names need a later feel pass after mechanics prove stable",
        ],
    }


def _build_continuity_ledger(
    squad: List[Dict[str, Any]],
    progression: Dict[str, Any],
    battle_run: Dict[str, Any],
    route_log: List[Dict[str, Any]],
    ai_turn_log: List[Dict[str, Any]],
) -> Dict[str, Any]:
    progress_by_player = {hero["player"]: hero for hero in progression["hero_progress"]}
    hero_deltas = []
    for hero in squad:
        progress = progress_by_player[hero["player"]]
        hero_deltas.append(
            {
                "player": hero["player"],
                "hero": hero["name"],
                "role": hero["role"],
                "level_after": progress["level"],
                "xp_after": progress["xp"],
                "xp_gain": progress["xp_gain"],
                "hp_after": progress["hp"],
                "traits": progress["traits"],
                "injuries": progress["injuries"],
            }
        )
    return {
        "ledger_id": "blackstar_campaign_001_continuity_after_run_001_v044",
        "campaign_id": CAMPAIGN_ID,
        "run_id": RUN_ID,
        "battle_run_id": battle_run["run_id"],
        "route_nodes_resolved": [entry["node"]["node"] for entry in route_log],
        "hero_deltas": hero_deltas,
        "camp_after": progression["camp"],
        "ai_turn_count": len(ai_turn_log),
        "persistent_threads": progression["camp"]["persistent_events"],
    }


def _ai_turn_from_battle_action(action: Dict[str, Any]) -> Dict[str, Any]:
    if action["type"] == "hero_turn":
        return {
            "actor": "ai_heroes",
            "stage": f"battle_round_{action['round']}",
            "player": action["actor"],
            "decision": {
                "move_to": action["movement"]["to"],
                "main_action": action["main_action"]["id"],
                "bonus_action": action["bonus_action"]["id"],
            },
            "score_refs": {
                "main": action["main_action"]["score_components"],
                "bonus": action["bonus_action"]["score_components"],
            },
        }
    return {
        "actor": "ai_enemies",
        "stage": f"battle_round_{action['round']}",
        "enemy": action["actor"],
        "decision": {"target": action["target"], "attack": action["attack"]},
    }


def _hero_screen_doc(hero: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "player": hero.get("player"),
        "hero_id": hero["hero_id"],
        "hero": hero["hero_name"],
        "role": hero["role"],
        "attributes": hero["attributes"],
        "derived": hero["derived"],
        "hp": hero.get("hp", hero["derived"]["max_hp"]),
        "max_hp": hero.get("max_hp", hero["derived"]["max_hp"]),
        "loadout": hero.get("loadout", []),
        "directive": hero.get("directive"),
    }


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    full_run = simulate_campaign()
    paths = write_outputs(full_run)
    print(
        json.dumps(
            {
                "run_id": full_run["run_id"],
                "schema": full_run["schema"],
                "screen_count": len(full_run["screen_payloads"]),
                "battle_result": full_run["battle_run"]["result"],
                "validation_errors": full_run["validation_errors"],
                "paths": paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
