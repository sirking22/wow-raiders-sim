"""BattleV09 external roster runtime.

This runtime is the first tactical layer that consumes the v0.42 calculated
campaign roster directly. It does not subclass or replace the legacy v0.8
golden simulator; v0.8 stays preserved as the historical combat baseline.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, Iterable, List, Tuple

import campaign_v042 as campaign
import hexgrid
import rules_v042 as rules
from battle_v04 import COLS


SCHEMA_VERSION = "blackstar-raiders.battle.v0.9"
ENGINE_VERSION = "v0.9-external-roster"
RUN_ID = "campaign01_battle_v09_external_roster"
SEED = "campaign01_v09_external_battle"

WIDTH = 8
HEIGHT = 8
OBJECTIVE_CELL = "E5"
EXTRACTION_CELL = "B2"

HERO_STARTS = {"EZ": "B2", "Candy Peace": "C2", "Dr.Feed": "B1"}
ENEMY_STARTS = {"blight_sergeant": "F6", "rust_gunner": "G5", "relic_thrall_pack": "E6"}

BLOCKED_CELLS = {"D4", "F4"}
COVER_CELLS = {"C3": "ruined_pillar", "D3": "shell_crater", "F5": "broken_aegis"}
HAZARD_CELLS = {"G4": "rad_mire", "E7": "ash_choke"}

ACTION_RANGES = {
    "guard_line": 1,
    "prism_lock": 4,
    "stabilize_ally": 3,
    "breach_fire": 4,
    "precision_shot": 5,
    "secure_exit_lane": 0,
    "scan_relic_signal": 4,
    "raise_shield": 2,
    "reposition": 0,
    "reload_or_vent": 0,
    "field_injector": 2,
}

ENEMY_RANGES = {"blight_sergeant": 2, "rust_gunner": 4, "relic_thrall_pack": 1}
ENEMY_MOVE = {"blight_sergeant": 3, "rust_gunner": 2, "relic_thrall_pack": 3}


def build_battle_run(seed: str = SEED, max_rounds: int = 4, min_rounds: int = 3) -> Dict[str, Any]:
    """Build and resolve a deterministic tactical run from v0.42 campaign data."""

    squad, post_loadout_resources, loadout_log = rules.assemble_squad(
        campaign.PLAYER_SLOTS,
        campaign.PLAYER_DIRECTIVES,
        campaign.BASE_CAMP["resources"],
    )
    clocks = _campaign_clocks_at_battle_start()
    actors = _build_actor_state(squad)
    action_log: List[Dict[str, Any]] = []
    round_log: List[Dict[str, Any]] = []
    frames = [_frame("frame_00_initial", 0, "deployment", actors, clocks, 0, [])]
    objective_progress = 0
    mitigation_pool = 0

    for round_no in range(1, max_rounds + 1):
        round_actions: List[Dict[str, Any]] = []
        mitigation_pool = 0
        round_risk = 0

        for actor in _initiative_order(actors):
            if not _alive(actor):
                continue
            if actor["team"] == "heroes":
                hero_action = _resolve_hero_turn(seed, round_no, actor, actors, clocks, objective_progress)
                objective_progress += hero_action["objective_delta"]
                mitigation_pool += hero_action["mitigation_delta"]
                round_risk += hero_action["risk_delta"]
                clocks["noise"] = max(0, clocks["noise"] + hero_action["noise_delta"])
                public_action = _public_hero_turn(hero_action)
                round_actions.append(public_action)
                action_log.append(public_action)
            else:
                enemy_action = _resolve_enemy_turn(seed, round_no, actor, actors, clocks, mitigation_pool)
                mitigation_pool = enemy_action["mitigation_pool_after"]
                public_action = _public_enemy_turn(enemy_action)
                round_actions.append(public_action)
                action_log.append(public_action)

        _advance_clocks(clocks, round_no, round_risk)
        extraction_readiness = _extraction_readiness(actors, objective_progress, clocks)
        round_doc = {
            "round": round_no,
            "clocks": copy.deepcopy(clocks),
            "objective_progress": objective_progress,
            "extraction_readiness": extraction_readiness,
            "actions": round_actions,
            "squad_state": _team_state(actors, "heroes"),
            "enemy_state": _team_state(actors, "hostiles"),
        }
        round_log.append(round_doc)
        frames.append(
            _frame(
                f"frame_{round_no:02d}_end",
                round_no,
                "round_end",
                actors,
                clocks,
                objective_progress,
                round_actions,
            )
        )

        if round_no >= min_rounds and objective_progress >= 8 and len(_live_team(actors, "heroes")) >= 2:
            break

    result = _result(actors, objective_progress, clocks, len(round_log))
    run = {
        "schema": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "seed": seed,
        "engine_version": ENGINE_VERSION,
        "source_campaign": {
            "schema": campaign.SCHEMA_VERSION,
            "run_id": campaign.RUN_ID,
            "rules_schema": rules.SCHEMA_VERSION,
        },
        "setting_profile": {
            "public_name": "Blackstar Raiders",
            "reference_target": "hard latest-edition grimdark far-future planetary raid mood",
            "public_asset_rule": "Keep names/logos original-safe unless a file is explicitly marked private fan/reference work.",
        },
        "grid": _grid_meta(),
        "mission": campaign.MISSION,
        "camp_resources_after_loadout": post_loadout_resources,
        "loadout_log": loadout_log,
        "actors_initial": _actor_public_list(_build_actor_state(copy.deepcopy(squad))),
        "round_log": round_log,
        "action_log": action_log,
        "frames": frames,
        "result": result,
    }
    run["screen_payloads"] = build_screen_payloads(run)
    run["validation_errors"] = validate_battle_run(run)
    return run


def _campaign_clocks_at_battle_start() -> Dict[str, int]:
    clocks = {"threat": 4, "noise": 0, "doom": 2, "extraction_timer": campaign.MISSION["extraction_window"]}
    _apply_delta(clocks, {"noise": 1, "extraction_timer": -3})
    for node in campaign.ROUTE_NODES:
        _apply_delta(clocks, node["cost"])
    return clocks


def _apply_delta(clocks: Dict[str, int], delta: Dict[str, int]) -> None:
    for key, value in delta.items():
        clocks[key] = max(0, clocks.get(key, 0) + value)


def _build_actor_state(squad: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    actors: Dict[str, Dict[str, Any]] = {}
    for hero in squad:
        actor_id = hero["player"]
        actors[actor_id] = {
            "id": actor_id,
            "player": hero["player"],
            "name": hero["hero_name"],
            "hero_id": hero["hero_id"],
            "team": "heroes",
            "role": hero["role"],
            "class_tags": hero["class_tags"],
            "attributes": hero["attributes"],
            "derived": hero["derived"],
            "directive": hero["directive"],
            "loadout": hero["loadout"],
            "loadout_tags": hero.get("loadout_tags", []),
            "hp": hero["hp"],
            "max_hp": hero["max_hp"],
            "armor": hero["derived"]["armor"],
            "position": HERO_STARTS[hero["player"]],
            "statuses": [],
        }
    for enemy in rules.ENEMY_GROUP:
        actors[enemy["id"]] = {
            "id": enemy["id"],
            "name": enemy["name"],
            "team": "hostiles",
            "role": "hostile",
            "hp": enemy["hp"],
            "max_hp": enemy["hp"],
            "armor": enemy["armor"],
            "threat": enemy["threat"],
            "target_bias": enemy["target_bias"],
            "position": ENEMY_STARTS[enemy["id"]],
            "statuses": [],
        }
    return actors


def _resolve_hero_turn(
    seed: str,
    round_no: int,
    actor: Dict[str, Any],
    actors: Dict[str, Dict[str, Any]],
    clocks: Dict[str, int],
    objective_progress: int,
) -> Dict[str, Any]:
    context = {
        "lowest_ally_hp_ratio": _lowest_ally_hp_ratio(actors),
        "enemy_pressure": sum(e["threat"] for e in _live_team(actors, "hostiles")),
        "extraction_timer": clocks.get("extraction_timer", 99),
        "unclaimed_objective": objective_progress < 8,
    }
    hero_doc = _hero_doc_for_rules(actor)
    directive = actor["directive"]
    main_action = rules.choose_action(seed, hero_doc, directive, rules.MAIN_ACTIONS, context, round_no)
    bonus_action = rules.choose_action(seed, hero_doc, directive, rules.BONUS_ACTIONS, context, round_no)
    movement_budget = min(actor["derived"]["movement"], 2 + int(directive["mobility"] * actor["derived"]["movement"]))
    movement = _move_actor(actor, actors, _hero_target_cell(actor, actors, objective_progress), movement_budget)
    effects: List[Dict[str, Any]] = []
    objective_delta = 0
    mitigation_delta = 0
    noise_delta = 0
    risk_delta = 0

    for action in (main_action, bonus_action):
        resolved = _apply_hero_action(seed, round_no, actor, actors, action)
        effects.extend(resolved["effects"])
        objective_delta += _objective_delta(actor, action, objective_progress)
        mitigation_delta += resolved["mitigation"]
        noise_delta += int(action["effect"].get("noise", 0))
        risk_delta += max(0, int(action["effect"].get("risk", 0)))

    return {
        "type": "hero_turn",
        "round": round_no,
        "actor": actor["id"],
        "player": actor["player"],
        "hero": actor["name"],
        "role": actor["role"],
        "initiative": actor["derived"]["initiative"],
        "budget": {
            "movement": movement_budget,
            "main": main_action["budget"]["main"],
            "bonus": bonus_action["budget"]["bonus"],
            "reaction_reserved": 1 if directive["survival"] >= 0.7 else 0,
        },
        "movement": movement,
        "main_action": _action_public_doc(main_action),
        "bonus_action": _action_public_doc(bonus_action),
        "effects": effects,
        "objective_delta": objective_delta,
        "mitigation_delta": mitigation_delta,
        "noise_delta": noise_delta,
        "risk_delta": risk_delta,
    }


def _resolve_enemy_turn(
    seed: str,
    round_no: int,
    actor: Dict[str, Any],
    actors: Dict[str, Dict[str, Any]],
    clocks: Dict[str, int],
    mitigation_pool: int,
) -> Dict[str, Any]:
    target = _choose_enemy_target(actor, actors)
    if not target:
        return {
            "type": "enemy_turn",
            "round": round_no,
            "actor": actor["id"],
            "target": None,
            "movement": {"from": actor["position"], "to": actor["position"], "path": [actor["position"]], "cost": 0, "budget": 0},
            "attack": None,
            "mitigation_pool_after": mitigation_pool,
        }

    attack_range = ENEMY_RANGES.get(actor["id"], 1)
    movement = {"from": actor["position"], "to": actor["position"], "path": [actor["position"]], "cost": 0, "budget": 0}
    if _distance(actor["position"], target["position"]) > attack_range:
        destination = _adjacent_approach_cell(target["position"], actor["position"], actors)
        movement = _move_actor(actor, actors, destination, ENEMY_MOVE.get(actor["id"], 2))

    attack = None
    if _distance(actor["position"], target["position"]) <= attack_range and _alive(target):
        raw = actor["threat"] + rules.stable_int(seed, f"enemy:{round_no}:{actor['id']}", 1, 6) + clocks.get("threat", 0) // 3
        mitigated = min(raw, mitigation_pool)
        mitigation_pool -= mitigated
        damage = max(0, raw - target["armor"] - mitigated)
        before = target["hp"]
        target["hp"] = max(0, target["hp"] - damage)
        if target["hp"] <= 0 and "downed" not in target["statuses"]:
            target["statuses"].append("downed")
        attack = {
            "target": target["id"],
            "target_role": target["role"],
            "target_bias": actor["target_bias"],
            "raw_threat": raw,
            "mitigated": mitigated,
            "damage": damage,
            "before": before,
            "after": target["hp"],
        }

    return {
        "type": "enemy_turn",
        "round": round_no,
        "actor": actor["id"],
        "name": actor["name"],
        "target": target["id"],
        "movement": movement,
        "attack": attack,
        "mitigation_pool_after": mitigation_pool,
    }


def _apply_hero_action(
    seed: str,
    round_no: int,
    actor: Dict[str, Any],
    actors: Dict[str, Dict[str, Any]],
    action: Dict[str, Any],
) -> Dict[str, Any]:
    effects: List[Dict[str, Any]] = []
    mitigation = 0
    effect = action["effect"]

    if effect.get("mitigation", 0):
        value = effect["mitigation"] + actor["armor"] // 2
        mitigation += value
        effects.append({"type": "mitigation", "action": action["id"], "value": value})

    if effect.get("heal", 0):
        target = _lowest_wounded_ally(actors)
        before = target["hp"]
        value = effect["heal"] + actor["derived"]["healing_power"] + rules.stable_int(seed, f"heal:{round_no}:{actor['id']}:{action['id']}", 0, 3)
        target["hp"] = min(target["max_hp"], target["hp"] + value)
        if target["hp"] > 0 and "downed" in target["statuses"]:
            target["statuses"].remove("downed")
        effects.append({"type": "heal", "action": action["id"], "target": target["id"], "before": before, "after": target["hp"], "value": value})

    if effect.get("damage", 0):
        target_enemy = _target_enemy(actors, actor["position"], ACTION_RANGES.get(action["id"], 4))
        if target_enemy:
            before = target_enemy["hp"]
            raw = effect["damage"] + actor["derived"]["damage_power"] + rules.stable_int(seed, f"dmg:{round_no}:{actor['id']}:{action['id']}", 0, 5)
            damage = max(1, raw - target_enemy["armor"])
            target_enemy["hp"] = max(0, target_enemy["hp"] - damage)
            if target_enemy["hp"] <= 0 and "dead" not in target_enemy["statuses"]:
                target_enemy["statuses"].append("dead")
            effects.append({"type": "damage", "action": action["id"], "target": target_enemy["id"], "before": before, "after": target_enemy["hp"], "value": damage})
        else:
            effects.append({"type": "out_of_range", "action": action["id"], "range": ACTION_RANGES.get(action["id"], 4)})

    if action["id"] == "scan_relic_signal":
        effects.append({"type": "intel_ping", "action": action["id"], "cell": OBJECTIVE_CELL, "value": 1})
    if action["id"] == "secure_exit_lane":
        effects.append({"type": "lane_secured", "action": action["id"], "cell": actor["position"], "value": 1})

    return {"effects": effects, "mitigation": mitigation}


def _objective_delta(actor: Dict[str, Any], action: Dict[str, Any], objective_progress: int) -> int:
    base = int(action["effect"].get("objective", 0))
    if base <= 0:
        return 0
    if action["id"] == "scan_relic_signal":
        return base
    near_objective = _distance(actor["position"], OBJECTIVE_CELL) <= 1
    if near_objective:
        return base + max(0, actor["derived"].get("objective_power", 0) // 6)
    if action["id"] == "secure_exit_lane" and objective_progress >= 5:
        return base
    return max(0, base - 1)


def _move_actor(
    actor: Dict[str, Any],
    actors: Dict[str, Dict[str, Any]],
    target_cell: str,
    budget: int,
) -> Dict[str, Any]:
    start = actor["position"]
    if start == target_cell or budget <= 0:
        return {"from": start, "to": start, "path": [start], "cost": 0, "budget": budget}

    occupied = {a["position"] for a in actors.values() if a["id"] != actor["id"] and _alive(a)}

    def enter_cost(hex_: Tuple[int, int]) -> int | None:
        cell = _hex_to_cell(hex_)
        if cell in BLOCKED_CELLS:
            return None
        if cell in occupied:
            return None
        return 2 if cell in HAZARD_CELLS else 1

    path, total_cost = hexgrid.shortest_path(_cell_to_hex(start), _cell_to_hex(target_cell), WIDTH, HEIGHT, enter_cost)
    if not path:
        return {"from": start, "to": start, "path": [start], "cost": 0, "budget": budget}

    spent = 0
    chosen = path[0]
    chosen_path = [path[0]]
    for next_hex in path[1:]:
        step_cost = enter_cost(next_hex)
        if step_cost is None or spent + step_cost > budget:
            break
        spent += step_cost
        chosen = next_hex
        chosen_path.append(next_hex)

    actor["position"] = _hex_to_cell(chosen)
    return {
        "from": start,
        "to": actor["position"],
        "path": [_hex_to_cell(h) for h in chosen_path],
        "cost": spent,
        "budget": budget,
        "target": target_cell,
        "full_path_cost": total_cost,
    }


def _hero_target_cell(actor: Dict[str, Any], actors: Dict[str, Dict[str, Any]], objective_progress: int) -> str:
    if objective_progress < 8:
        return OBJECTIVE_CELL
    if actor["role"] == "tank":
        enemy = _nearest_enemy(actor["position"], actors)
        if enemy:
            return _adjacent_approach_cell(enemy["position"], actor["position"], actors)
    return EXTRACTION_CELL


def _adjacent_approach_cell(target_cell: str, from_cell: str, actors: Dict[str, Dict[str, Any]]) -> str:
    occupied = {a["position"] for a in actors.values() if _alive(a)}
    candidates = []
    for hex_ in hexgrid.neighbors_in_bounds(_cell_to_hex(target_cell), WIDTH, HEIGHT):
        cell = _hex_to_cell(hex_)
        if cell in BLOCKED_CELLS or cell in occupied:
            continue
        candidates.append(cell)
    if not candidates:
        return from_cell
    candidates.sort(key=lambda cell: (_distance(cell, from_cell), cell))
    return candidates[0]


def _initiative_order(actors: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key(actor: Dict[str, Any]) -> Tuple[int, int, str]:
        if actor["team"] == "heroes":
            return (0, -actor["derived"]["initiative"], actor["id"])
        return (1, -actor["threat"], actor["id"])

    return sorted(actors.values(), key=key)


def _hero_doc_for_rules(actor: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "player": actor["player"],
        "name": actor["name"],
        "role": actor["role"],
        "attributes": actor["attributes"],
        "derived": actor["derived"],
        "class_tags": actor["class_tags"],
        "loadout_tags": actor.get("loadout_tags", []),
        "hp": actor["hp"],
        "max_hp": actor["max_hp"],
    }


def _choose_enemy_target(enemy: Dict[str, Any], actors: Dict[str, Dict[str, Any]]) -> Dict[str, Any] | None:
    live = _live_team(actors, "heroes")
    if not live:
        return None
    if enemy["target_bias"] == "medic":
        medics = [h for h in live if h["role"] == "medic"]
        if medics:
            return medics[0]
    if enemy["target_bias"] == "lowest_armor":
        return min(live, key=lambda h: (h["armor"], h["hp"], h["id"]))
    return max(live, key=lambda h: (h["derived"]["threat"], h["armor"], h["id"]))


def _target_enemy(actors: Dict[str, Dict[str, Any]], from_cell: str, action_range: int) -> Dict[str, Any] | None:
    live = _live_team(actors, "hostiles")
    in_range = [enemy for enemy in live if _distance(from_cell, enemy["position"]) <= action_range]
    if not in_range:
        return None
    return sorted(in_range, key=lambda e: (-e["threat"], e["hp"], e["id"]))[0]


def _nearest_enemy(from_cell: str, actors: Dict[str, Dict[str, Any]]) -> Dict[str, Any] | None:
    live = _live_team(actors, "hostiles")
    if not live:
        return None
    return sorted(live, key=lambda e: (_distance(from_cell, e["position"]), -e["threat"], e["id"]))[0]


def _lowest_wounded_ally(actors: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    live = _live_team(actors, "heroes")
    return min(live, key=lambda h: (h["hp"] / h["max_hp"], h["id"]))


def _lowest_ally_hp_ratio(actors: Dict[str, Dict[str, Any]]) -> float:
    return min((h["hp"] / h["max_hp"] for h in _live_team(actors, "heroes")), default=1.0)


def _advance_clocks(clocks: Dict[str, int], round_no: int, round_risk: int) -> None:
    clocks["extraction_timer"] = max(0, clocks.get("extraction_timer", 0) - 2)
    if round_no % 2 == 0:
        clocks["threat"] = clocks.get("threat", 0) + 1
    if round_risk >= 3:
        clocks["doom"] = clocks.get("doom", 0) + 1


def _result(actors: Dict[str, Dict[str, Any]], objective_progress: int, clocks: Dict[str, int], rounds: int) -> Dict[str, Any]:
    heroes_alive = [a["id"] for a in _live_team(actors, "heroes")]
    hostiles_alive = [a["id"] for a in _live_team(actors, "hostiles")]
    readiness = _extraction_readiness(actors, objective_progress, clocks)
    success = objective_progress >= 8 and len(heroes_alive) >= 2 and readiness >= 60
    return {
        "success": success,
        "victory_type": "extract_ready" if success else "incomplete_contact",
        "rounds": rounds,
        "objective_progress": objective_progress,
        "heroes_alive": heroes_alive,
        "hostiles_alive": hostiles_alive,
        "clocks": copy.deepcopy(clocks),
        "extraction_readiness": readiness,
    }


def _extraction_readiness(actors: Dict[str, Dict[str, Any]], objective_progress: int, clocks: Dict[str, int]) -> int:
    heroes_alive = len(_live_team(actors, "heroes"))
    value = 35 + objective_progress * 7 + heroes_alive * 7 - clocks.get("noise", 0) * 2 - clocks.get("doom", 0) * 3
    return max(0, min(100, value))


def _frame(
    frame_id: str,
    round_no: int,
    phase: str,
    actors: Dict[str, Dict[str, Any]],
    clocks: Dict[str, int],
    objective_progress: int,
    actions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "frame_id": frame_id,
        "round": round_no,
        "phase": phase,
        "grid": _grid_meta(),
        "objective": {"cell": OBJECTIVE_CELL, "progress": objective_progress, "target": 8},
        "extraction": {"cell": EXTRACTION_CELL, "timer": clocks.get("extraction_timer", 0)},
        "clocks": copy.deepcopy(clocks),
        "actors": _actor_public_list(actors),
        "board": _board(actors),
        "actions": copy.deepcopy(actions),
    }


def build_screen_payloads(run: Dict[str, Any]) -> List[Dict[str, Any]]:
    screens = [
        _screen(
            0,
            run,
            "battle_v09_start",
            "BattleV09 Deployment",
            {
                "grid": run["grid"],
                "mission": run["mission"],
                "actors": run["actors_initial"],
                "initial_frame": run["frames"][0],
                "setting_profile": run["setting_profile"],
            },
            ["hex_battlefield", "initiative_ladder", "objective_panel", "extraction_clocks"],
            ["engine/battle_v09.py::build_battle_run", "engine/rules_v042.py::assemble_squad"],
        )
    ]
    for screen_index, (round_doc, frame) in enumerate(zip(run["round_log"], run["frames"][1:]), start=1):
        screens.append(
            _screen(
                screen_index,
                run,
                "battle_v09_round",
                f"BattleV09 Round {round_doc['round']}",
                {"round": round_doc, "frame": frame},
                ["battlefield_frame", "action_stack", "score_components", "hp_clocks"],
                ["engine/battle_v09.py::_resolve_hero_turn", "engine/rules_v042.py::choose_action"],
            )
        )
    screens.append(
        _screen(
            len(screens),
            run,
            "battle_v09_result",
            "BattleV09 Result",
            {"result": run["result"], "final_frame": run["frames"][-1]},
            ["result_banner", "survivor_panel", "objective_summary", "replay_index"],
            ["engine/battle_v09.py::_result"],
        )
    )
    return screens


def _screen(
    index: int,
    run: Dict[str, Any],
    stage: str,
    title: str,
    state: Dict[str, Any],
    ui_panels: List[str],
    calculation_refs: List[str],
) -> Dict[str, Any]:
    return {
        "screen_id": f"{run['run_id']}_screen_{index:02d}_{stage}",
        "stage": stage,
        "title": title,
        "state": state,
        "ui_panels": [{"id": panel} for panel in ui_panels],
        "calculation_refs": calculation_refs,
        "render_contract": {
            "source_of_truth": ["state", "calculation_refs"],
            "must_show": sorted(state.keys()),
            "must_not_invent": [
                "actions absent from action_log",
                "hero names outside EZ, Candy Peace, Dr.Feed",
                "official WH40 logos or protected public asset names",
            ],
        },
    }


def validate_battle_run(run: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if run.get("schema") != SCHEMA_VERSION:
        errors.append("wrong schema")
    if run.get("engine_version") != ENGINE_VERSION:
        errors.append("wrong engine version")

    players = [a["id"] for a in run["actors_initial"] if a["team"] == "heroes"]
    if players != list(rules.PLAYER_NAMES):
        errors.append(f"wrong player order: {players}")

    dr_feed = next((a for a in run["actors_initial"] if a["id"] == "Dr.Feed"), None)
    if not dr_feed or dr_feed.get("role") != "medic":
        errors.append("Dr.Feed must be native medic")

    dr_feed_actions = [a for a in run["action_log"] if a.get("actor") == "Dr.Feed"]
    if not any(a.get("main_action", {}).get("id") == "stabilize_ally" or a.get("bonus_action", {}).get("id") == "field_injector" for a in dr_feed_actions):
        errors.append("Dr.Feed did not perform native support action")
    if not any(effect.get("type") == "heal" for action in dr_feed_actions for effect in action.get("effects", [])):
        errors.append("Dr.Feed did not produce heal effect")

    for action in [a for a in run["action_log"] if a.get("type") == "hero_turn"]:
        if action["budget"]["main"] != 1 or action["budget"]["bonus"] != 1:
            errors.append(f"bad action budget for {action['actor']} round {action['round']}")
        movement = action["movement"]
        if movement["cost"] > movement["budget"]:
            errors.append(f"movement cost over budget for {action['actor']} round {action['round']}")
        actor_initial = next((a for a in run["actors_initial"] if a["id"] == action["actor"]), None)
        if actor_initial and movement["cost"] > actor_initial["derived"]["movement"]:
            errors.append(f"movement exceeds derived stat for {action['actor']} round {action['round']}")
        errors.extend(_validate_path(action["actor"], movement["path"]))
        if not action["main_action"].get("score_components") or not action["bonus_action"].get("score_components"):
            errors.append(f"missing score components for {action['actor']} round {action['round']}")

    for frame in run["frames"]:
        seen_live = set()
        for actor in frame["actors"]:
            if not _cell_in_bounds(actor["position"]):
                errors.append(f"actor out of bounds: {actor['id']} {actor['position']}")
            if actor["hp"] < 0 or actor["hp"] > actor["max_hp"]:
                errors.append(f"bad hp for {actor['id']} in {frame['frame_id']}")
            if actor["hp"] > 0:
                if actor["position"] in seen_live:
                    errors.append(f"duplicate live position {actor['position']} in {frame['frame_id']}")
                seen_live.add(actor["position"])

    result = run.get("result", {})
    for key in ("noise", "threat", "doom", "extraction_timer"):
        if key not in result.get("clocks", {}):
            errors.append(f"missing result clock: {key}")
    if not run.get("screen_payloads"):
        errors.append("missing screen payloads")
    return errors


def _validate_path(actor_id: str, path: List[str]) -> List[str]:
    errors: List[str] = []
    for cell in path:
        if not _cell_in_bounds(cell):
            errors.append(f"path out of bounds for {actor_id}: {cell}")
    for left, right in zip(path, path[1:]):
        if _distance(left, right) != 1:
            errors.append(f"non adjacent path for {actor_id}: {left}->{right}")
    return errors


def write_outputs(run: Dict[str, Any], root: str | None = None) -> Dict[str, str]:
    repo_root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = {
        "run": os.path.join(repo_root, "game-data", "battle-runs", "campaign01_v09_external_battle_run.json"),
        "screens": os.path.join(repo_root, "game-data", "screen-payloads", "campaign01_v09_external_battle_screen_payloads.json"),
    }
    for path in paths.values():
        os.makedirs(os.path.dirname(path), exist_ok=True)
    _write_json(paths["run"], run)
    _write_json(
        paths["screens"],
        {
            "schema": "blackstar-raiders.screen-payloads.battle-v0.9",
            "run_id": run["run_id"],
            "screen_count": len(run["screen_payloads"]),
            "screens": run["screen_payloads"],
        },
    )
    return paths


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _action_public_doc(action: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": action["id"],
        "tags": action["tags"],
        "budget": action["budget"],
        "score": action["score"],
        "score_components": action["score_components"],
        "effect": action["effect"],
    }


def _public_hero_turn(action: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": action["type"],
        "round": action["round"],
        "actor": action["actor"],
        "player": action["player"],
        "hero": action["hero"],
        "role": action["role"],
        "initiative": action["initiative"],
        "budget": action["budget"],
        "movement": action["movement"],
        "main_action": action["main_action"],
        "bonus_action": action["bonus_action"],
        "effects": action["effects"],
        "objective_delta": action["objective_delta"],
        "noise_delta": action["noise_delta"],
        "risk_delta": action["risk_delta"],
    }


def _public_enemy_turn(action: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": action["type"],
        "round": action["round"],
        "actor": action["actor"],
        "name": action.get("name"),
        "target": action["target"],
        "movement": action["movement"],
        "attack": action["attack"],
    }


def _actor_public_list(actors: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    hero_order = {name: idx for idx, name in enumerate(rules.PLAYER_NAMES)}
    enemy_order = {enemy["id"]: idx for idx, enemy in enumerate(rules.ENEMY_GROUP)}

    def key(actor: Dict[str, Any]) -> Tuple[int, int, str]:
        if actor["team"] == "heroes":
            return (0, hero_order.get(actor["id"], 99), actor["id"])
        return (1, enemy_order.get(actor["id"], 99), actor["id"])

    return [_actor_public_doc(actor) for actor in sorted(actors.values(), key=key)]


def _actor_public_doc(actor: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "id": actor["id"],
        "name": actor["name"],
        "team": actor["team"],
        "role": actor["role"],
        "hp": actor["hp"],
        "max_hp": actor["max_hp"],
        "armor": actor["armor"],
        "position": actor["position"],
        "statuses": list(actor.get("statuses", [])),
    }
    if actor["team"] == "heroes":
        out.update(
            {
                "player": actor["player"],
                "hero_id": actor["hero_id"],
                "derived": actor["derived"],
                "loadout": actor["loadout"],
            }
        )
    else:
        out.update({"threat": actor["threat"], "target_bias": actor["target_bias"]})
    return out


def _team_state(actors: Dict[str, Dict[str, Any]], team: str) -> List[Dict[str, Any]]:
    return [_actor_public_doc(actor) for actor in sorted(actors.values(), key=lambda a: a["id"]) if actor["team"] == team]


def _live_team(actors: Dict[str, Dict[str, Any]], team: str) -> List[Dict[str, Any]]:
    return [actor for actor in actors.values() if actor["team"] == team and _alive(actor)]


def _alive(actor: Dict[str, Any]) -> bool:
    return actor["hp"] > 0 and "dead" not in actor.get("statuses", []) and "downed" not in actor.get("statuses", [])


def _board(actors: Dict[str, Dict[str, Any]]) -> List[str]:
    tokens = {}
    for actor in actors.values():
        if actor["hp"] <= 0:
            continue
        tokens[actor["position"]] = {
            "EZ": "EZ",
            "Candy Peace": "CP",
            "Dr.Feed": "DF",
            "blight_sergeant": "BS",
            "rust_gunner": "RG",
            "relic_thrall_pack": "RT",
        }.get(actor["id"], "??")

    out = []
    for row in range(HEIGHT, 0, -1):
        cells = []
        for col in range(1, WIDTH + 1):
            cell = f"{COLS[col - 1]}{row}"
            token = tokens.get(cell)
            if token:
                cells.append(f"{token:>2}")
            elif cell == OBJECTIVE_CELL:
                cells.append("OB")
            elif cell == EXTRACTION_CELL:
                cells.append("EX")
            elif cell in BLOCKED_CELLS:
                cells.append("##")
            elif cell in HAZARD_CELLS:
                cells.append("Hz")
            elif cell in COVER_CELLS:
                cells.append("cv")
            else:
                cells.append("..")
        indent = "  " if ((row - 1) & 1) else ""
        out.append(f"{row} | {indent}" + " ".join(cells))
    out.append("    " + " ".join(f"{c:>2}" for c in COLS))
    return out


def _grid_meta() -> Dict[str, Any]:
    return {
        "type": "hex",
        "layout": "odd-r",
        "width": WIDTH,
        "height": HEIGHT,
        "coordinates": "A1-H8",
        "objective_cell": OBJECTIVE_CELL,
        "extraction_cell": EXTRACTION_CELL,
        "blocked_cells": sorted(BLOCKED_CELLS),
        "cover_cells": COVER_CELLS,
        "hazard_cells": HAZARD_CELLS,
    }


def _distance(left: str, right: str) -> int:
    return hexgrid.distance(_cell_to_hex(left), _cell_to_hex(right))


def _cell_to_hex(cell: str) -> Tuple[int, int]:
    return (COLS.index(cell[0]), int(cell[1:]) - 1)


def _hex_to_cell(hex_: Tuple[int, int]) -> str:
    col, row = hex_
    return f"{COLS[col]}{row + 1}"


def _cell_in_bounds(cell: str) -> bool:
    return hexgrid.in_bounds(_cell_to_hex(cell), WIDTH, HEIGHT)


def main() -> None:
    run = build_battle_run()
    paths = write_outputs(run)
    print(
        json.dumps(
            {
                "run_id": run["run_id"],
                "engine_version": run["engine_version"],
                "result": run["result"],
                "validation_errors": run["validation_errors"],
                "paths": paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
