"""Blackstar Raiders rules spine v0.42.

This module owns the calculated stat model used by campaign_v042.py. It is
kept separate from campaign orchestration so future settings can reuse the same
mechanical backbone with different names, visuals, and mission dressing.
"""

from __future__ import annotations

import copy
import hashlib
from typing import Any, Dict, Iterable, List, Tuple


SCHEMA_VERSION = "blackstar-raiders.rules.v0.42"
ATTRIBUTE_BUDGET = 30
ATTRIBUTE_KEYS = ("force", "agility", "endurance", "will", "tech", "presence")
DIRECTIVE_KEYS = ("mobility", "objective", "greed", "survival", "ability", "consumable", "quest")
PLAYER_NAMES = ("EZ", "Candy Peace", "Dr.Feed")


HERO_ARCHETYPES: List[Dict[str, Any]] = [
    {
        "id": "void_chaplain",
        "name": "Void Chaplain",
        "role": "tank",
        "class_tags": ["anchor", "protector", "morale", "frontline"],
        "attributes": {"force": 6, "agility": 3, "endurance": 8, "will": 6, "tech": 2, "presence": 5},
    },
    {
        "id": "ash_scout",
        "name": "Ash Scout",
        "role": "scout",
        "class_tags": ["mobility", "stealth", "route", "quest"],
        "attributes": {"force": 3, "agility": 8, "endurance": 4, "will": 5, "tech": 5, "presence": 5},
    },
    {
        "id": "plague_surgeon",
        "name": "Plague Surgeon",
        "role": "medic",
        "class_tags": ["healing", "toxins", "stabilize", "consumable"],
        "attributes": {"force": 2, "agility": 4, "endurance": 5, "will": 6, "tech": 8, "presence": 5},
    },
    {
        "id": "siege_gunner",
        "name": "Siege Gunner",
        "role": "heavy",
        "class_tags": ["suppression", "breach", "heavy", "noise"],
        "attributes": {"force": 7, "agility": 2, "endurance": 7, "will": 4, "tech": 7, "presence": 3},
    },
    {
        "id": "sanctioned_prism_psyker",
        "name": "Sanctioned Prism Psyker",
        "role": "control",
        "class_tags": ["psyker", "control", "risk", "objective"],
        "attributes": {"force": 2, "agility": 4, "endurance": 3, "will": 10, "tech": 3, "presence": 8},
    },
    {
        "id": "iron_tech_adept",
        "name": "Iron Tech-Adept",
        "role": "support",
        "class_tags": ["repair", "devices", "camp", "consumable"],
        "attributes": {"force": 4, "agility": 3, "endurance": 5, "will": 5, "tech": 10, "presence": 3},
    },
    {
        "id": "deathworld_beastmaster",
        "name": "Deathworld Beastmaster",
        "role": "ranger",
        "class_tags": ["tracking", "beast", "survival", "mobility"],
        "attributes": {"force": 5, "agility": 7, "endurance": 6, "will": 5, "tech": 2, "presence": 5},
    },
    {
        "id": "penitent_duelist",
        "name": "Penitent Duelist",
        "role": "duelist",
        "class_tags": ["melee", "bleed", "zeal", "risk"],
        "attributes": {"force": 7, "agility": 7, "endurance": 5, "will": 6, "tech": 1, "presence": 4},
    },
    {
        "id": "xeno_relic_sniper",
        "name": "Xeno Relic Sniper",
        "role": "sniper",
        "class_tags": ["range", "relics", "precision", "greed"],
        "attributes": {"force": 3, "agility": 8, "endurance": 3, "will": 6, "tech": 6, "presence": 4},
    },
]


LOADOUT_CATALOG: Dict[str, Dict[str, Any]] = {
    "refractor_field": {
        "name": "Refractor Field",
        "tags": ["survival", "guard"],
        "slot_cost": 2,
        "resource_cost": {"scrap": 2},
        "stat_mods": {"armor": 1, "resolve": 1},
    },
    "chain_relic": {
        "name": "Chain Relic",
        "tags": ["melee", "objective"],
        "slot_cost": 1,
        "resource_cost": {"scrap": 1},
        "stat_mods": {"threat": 1},
    },
    "prism_focus": {
        "name": "Prism Focus",
        "tags": ["ability", "control", "objective"],
        "slot_cost": 2,
        "resource_cost": {"intel": 1},
        "stat_mods": {"accuracy": 1, "resolve": 1},
    },
    "relic_scanner": {
        "name": "Relic Scanner",
        "tags": ["quest", "greed", "route"],
        "slot_cost": 1,
        "resource_cost": {"intel": 1},
        "stat_mods": {"objective_power": 1},
    },
    "medicae_injector": {
        "name": "Medicae Injector",
        "tags": ["consumable", "healing", "survival"],
        "slot_cost": 1,
        "resource_cost": {"medicae": 1},
        "stat_mods": {"healing_power": 2},
    },
    "toxin_screen": {
        "name": "Toxin Screen",
        "tags": ["control", "survival"],
        "slot_cost": 1,
        "resource_cost": {"medicae": 1},
        "stat_mods": {"armor": 1},
    },
    "siege_carbine": {
        "name": "Siege Carbine",
        "tags": ["damage", "noise", "breach"],
        "slot_cost": 2,
        "resource_cost": {"scrap": 2},
        "stat_mods": {"damage_power": 2, "threat": 1},
    },
    "smoke_charge": {
        "name": "Smoke Charge",
        "tags": ["mobility", "survival"],
        "slot_cost": 1,
        "resource_cost": {"scrap": 1},
        "stat_mods": {"evasion": 1},
    },
    "field_tools": {
        "name": "Field Tools",
        "tags": ["tech", "camp", "quest"],
        "slot_cost": 1,
        "resource_cost": {"scrap": 1},
        "stat_mods": {"tech_power": 1},
    },
}


ROLE_LOADOUT_PRIORITIES: Dict[str, List[str]] = {
    "tank": ["refractor_field", "chain_relic", "smoke_charge"],
    "control": ["prism_focus", "relic_scanner", "smoke_charge"],
    "medic": ["medicae_injector", "toxin_screen", "relic_scanner"],
    "heavy": ["siege_carbine", "refractor_field", "field_tools"],
    "support": ["field_tools", "relic_scanner", "medicae_injector"],
    "scout": ["relic_scanner", "smoke_charge", "field_tools"],
    "ranger": ["smoke_charge", "relic_scanner", "chain_relic"],
    "duelist": ["chain_relic", "smoke_charge", "refractor_field"],
    "sniper": ["relic_scanner", "prism_focus", "smoke_charge"],
}


MAIN_ACTIONS: List[Dict[str, Any]] = [
    {
        "id": "guard_line",
        "roles": ["tank", "ranger", "support"],
        "tags": ["survival", "guard", "objective"],
        "budget": {"main": 1, "bonus": 0, "reaction": 0},
        "base_score": 5,
        "effect": {"mitigation": 4, "objective": 1, "noise": 0, "risk": -1},
        "scales": {"endurance": 0.7, "presence": 0.3},
    },
    {
        "id": "prism_lock",
        "roles": ["control"],
        "tags": ["ability", "control", "objective", "risk"],
        "budget": {"main": 1, "bonus": 0, "reaction": 0},
        "base_score": 6,
        "effect": {"damage": 8, "objective": 2, "noise": 1, "risk": 2},
        "scales": {"will": 1.0, "presence": 0.4},
    },
    {
        "id": "stabilize_ally",
        "roles": ["medic", "support"],
        "tags": ["survival", "consumable", "healing"],
        "budget": {"main": 1, "bonus": 0, "reaction": 0},
        "base_score": 5,
        "effect": {"heal": 7, "objective": 1, "noise": 0, "risk": -2},
        "scales": {"tech": 0.8, "will": 0.3},
    },
    {
        "id": "breach_fire",
        "roles": ["heavy", "sniper", "duelist"],
        "tags": ["damage", "greed", "breach", "noise"],
        "budget": {"main": 1, "bonus": 0, "reaction": 0},
        "base_score": 5,
        "effect": {"damage": 10, "objective": 1, "noise": 2, "risk": 1},
        "scales": {"force": 0.7, "tech": 0.5},
    },
    {
        "id": "precision_shot",
        "roles": ["sniper", "scout", "ranger"],
        "tags": ["damage", "objective", "precision"],
        "budget": {"main": 1, "bonus": 0, "reaction": 0},
        "base_score": 5,
        "effect": {"damage": 9, "objective": 1, "noise": 1, "risk": 0},
        "scales": {"agility": 0.6, "will": 0.6},
    },
    {
        "id": "secure_exit_lane",
        "roles": ["tank", "scout", "control", "medic", "support", "ranger", "duelist", "sniper", "heavy"],
        "tags": ["mobility", "objective", "survival"],
        "budget": {"main": 1, "bonus": 0, "reaction": 0},
        "base_score": 4,
        "effect": {"damage": 0, "objective": 2, "noise": 0, "risk": -1},
        "scales": {"agility": 0.5, "will": 0.2},
    },
]


BONUS_ACTIONS: List[Dict[str, Any]] = [
    {
        "id": "scan_relic_signal",
        "roles": ["control", "scout", "support", "sniper", "medic"],
        "tags": ["quest", "objective", "greed"],
        "budget": {"main": 0, "bonus": 1, "reaction": 0},
        "base_score": 4,
        "effect": {"objective": 1, "intel": 1, "noise": 0, "risk": 0},
        "scales": {"tech": 0.4, "will": 0.3},
    },
    {
        "id": "raise_shield",
        "roles": ["tank", "support", "medic"],
        "tags": ["survival", "guard"],
        "budget": {"main": 0, "bonus": 1, "reaction": 0},
        "base_score": 4,
        "effect": {"mitigation": 2, "objective": 0, "noise": 0, "risk": -1},
        "scales": {"endurance": 0.4},
    },
    {
        "id": "reposition",
        "roles": ["tank", "control", "medic", "heavy", "support", "scout", "ranger", "duelist", "sniper"],
        "tags": ["mobility", "survival"],
        "budget": {"main": 0, "bonus": 1, "reaction": 0},
        "base_score": 3,
        "effect": {"evasion": 1, "objective": 0, "noise": 0, "risk": -1},
        "scales": {"agility": 0.5},
    },
    {
        "id": "reload_or_vent",
        "roles": ["heavy", "sniper", "control", "support"],
        "tags": ["ability", "damage"],
        "budget": {"main": 0, "bonus": 1, "reaction": 0},
        "base_score": 3,
        "effect": {"damage_next": 2, "objective": 0, "noise": -1, "risk": 0},
        "scales": {"tech": 0.3},
    },
    {
        "id": "field_injector",
        "roles": ["medic", "support", "tank"],
        "tags": ["consumable", "survival", "healing"],
        "budget": {"main": 0, "bonus": 1, "reaction": 0},
        "base_score": 3,
        "effect": {"heal": 3, "objective": 0, "noise": 0, "risk": -1},
        "scales": {"tech": 0.4},
    },
]


ENEMY_GROUP: List[Dict[str, Any]] = [
    {"id": "blight_sergeant", "name": "Blight Sergeant", "hp": 48, "armor": 3, "threat": 5, "target_bias": "medic"},
    {"id": "rust_gunner", "name": "Rust Gunner", "hp": 34, "armor": 2, "threat": 4, "target_bias": "lowest_armor"},
    {"id": "relic_thrall_pack", "name": "Relic Thrall Pack", "hp": 58, "armor": 1, "threat": 3, "target_bias": "frontline"},
]


def stable_int(seed: str, key: str, low: int, high: int) -> int:
    digest = hashlib.sha256(f"{seed}:{key}".encode("utf-8")).hexdigest()
    return low + (int(digest[:12], 16) % (high - low + 1))


def _attrs_total(attrs: Dict[str, int]) -> int:
    return sum(attrs.get(k, 0) for k in ATTRIBUTE_KEYS)


def derive_stats(attrs: Dict[str, int], loadout_mods: Dict[str, int] | None = None) -> Dict[str, int]:
    mods = loadout_mods or {}
    stats = {
        "max_hp": 18 + attrs["endurance"] * 4 + attrs["force"],
        "armor": 1 + attrs["endurance"] // 3,
        "movement": 3 + attrs["agility"] // 2,
        "initiative": attrs["agility"] + attrs["will"] // 2,
        "accuracy": attrs["will"] + attrs["agility"] // 2,
        "resolve": attrs["will"] + attrs["presence"],
        "supply_slots": 2 + attrs["tech"] // 3 + attrs["endurance"] // 4,
        "carry_capacity": 6 + attrs["force"] + attrs["endurance"] // 2,
        "damage_power": attrs["force"] + attrs["will"] // 2,
        "healing_power": attrs["tech"] // 2 + attrs["will"] // 3,
        "objective_power": attrs["will"] // 2 + attrs["tech"] // 3 + attrs["presence"] // 3,
        "tech_power": attrs["tech"],
        "evasion": attrs["agility"] // 3,
        "threat": attrs["force"] + attrs["will"] // 2 + attrs["presence"] // 2,
    }
    for key, value in mods.items():
        stats[key] = stats.get(key, 0) + value
    stats["max_hp"] = max(1, stats["max_hp"])
    stats["armor"] = max(0, stats["armor"])
    stats["movement"] = max(1, min(8, stats["movement"]))
    stats["supply_slots"] = max(1, stats["supply_slots"])
    return stats


def build_roster() -> List[Dict[str, Any]]:
    roster = []
    for base in HERO_ARCHETYPES:
        hero = copy.deepcopy(base)
        hero["attribute_budget"] = _attrs_total(hero["attributes"])
        hero["derived"] = derive_stats(hero["attributes"])
        roster.append(hero)
    return roster


def hero_by_id(hero_id: str) -> Dict[str, Any]:
    for hero in build_roster():
        if hero["id"] == hero_id:
            return hero
    raise KeyError(hero_id)


def normalize_directive(raw: Dict[str, Any]) -> Dict[str, Any]:
    directive = {key: float(raw.get(key, 0.5)) for key in DIRECTIVE_KEYS}
    for key, value in directive.items():
        directive[key] = max(0.0, min(1.0, round(value, 3)))
    directive["ability_bias"] = raw.get("ability_bias", "balanced")
    directive["character_notes"] = list(raw.get("character_notes", []))
    return directive


def can_afford(resources: Dict[str, int], item: Dict[str, Any]) -> bool:
    return all(resources.get(key, 0) >= value for key, value in item["resource_cost"].items())


def pay_cost(resources: Dict[str, int], item: Dict[str, Any]) -> None:
    for key, value in item["resource_cost"].items():
        resources[key] = resources.get(key, 0) - value


def recommend_loadout(hero: Dict[str, Any], directive: Dict[str, Any], camp_resources: Dict[str, int]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    resources = copy.deepcopy(camp_resources)
    chosen: List[Dict[str, Any]] = []
    slots_used = 0
    slot_limit = hero["derived"]["supply_slots"]
    candidates = ROLE_LOADOUT_PRIORITIES.get(hero["role"], []) + list(LOADOUT_CATALOG)

    seen = set()
    for item_id in candidates:
        if item_id in seen:
            continue
        seen.add(item_id)
        item = copy.deepcopy(LOADOUT_CATALOG[item_id])
        tag_score = sum(directive.get(tag, 0.0) for tag in item["tags"] if tag in DIRECTIVE_KEYS)
        role_fit = 1.0 if item_id in ROLE_LOADOUT_PRIORITIES.get(hero["role"], []) else 0.0
        item["_score"] = round(role_fit * 2 + tag_score, 3)
        if slots_used + item["slot_cost"] > slot_limit:
            continue
        if not can_afford(resources, item):
            continue
        if item["_score"] < 0.8 and chosen:
            continue
        pay_cost(resources, item)
        slots_used += item["slot_cost"]
        chosen.append(item)
        if len(chosen) >= 3:
            break

    return chosen, resources


def apply_loadout(hero: Dict[str, Any], loadout: List[Dict[str, Any]]) -> Dict[str, Any]:
    mods: Dict[str, int] = {}
    tags: List[str] = []
    slots_used = 0
    for item in loadout:
        slots_used += item["slot_cost"]
        tags.extend(item["tags"])
        for key, value in item["stat_mods"].items():
            mods[key] = mods.get(key, 0) + value
    out = copy.deepcopy(hero)
    out["loadout"] = [{"id": item_id(item), "name": item["name"], "tags": item["tags"], "slot_cost": item["slot_cost"]} for item in loadout]
    out["loadout_tags"] = sorted(set(tags))
    out["loadout_slots_used"] = slots_used
    out["derived"] = derive_stats(out["attributes"], mods)
    out["hp"] = out["derived"]["max_hp"]
    out["max_hp"] = out["derived"]["max_hp"]
    out["xp"] = out.get("xp", 0)
    out["level"] = out.get("level", 1)
    out["traits"] = list(out.get("traits", []))
    out["injuries"] = list(out.get("injuries", []))
    return out


def item_id(item: Dict[str, Any]) -> str:
    for key, value in LOADOUT_CATALOG.items():
        if value["name"] == item["name"]:
            return key
    return item["name"].lower().replace(" ", "_")


def assemble_squad(
    slots: Iterable[Dict[str, str]],
    directives: Dict[str, Dict[str, Any]],
    camp_resources: Dict[str, int],
) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[Dict[str, Any]]]:
    resources = copy.deepcopy(camp_resources)
    squad: List[Dict[str, Any]] = []
    loadout_log: List[Dict[str, Any]] = []
    for slot in slots:
        hero = hero_by_id(slot["assigned_hero"])
        directive = normalize_directive(directives[slot["player"]])
        loadout, resources = recommend_loadout(hero, directive, resources)
        with_loadout = apply_loadout(hero, loadout)
        with_loadout["player"] = slot["player"]
        with_loadout["hero_id"] = with_loadout["id"]
        with_loadout["hero_name"] = with_loadout["name"]
        with_loadout["directive"] = directive
        squad.append(with_loadout)
        loadout_log.append(
            {
                "player": slot["player"],
                "hero": with_loadout["name"],
                "slots_used": with_loadout["loadout_slots_used"],
                "slot_limit": hero["derived"]["supply_slots"],
                "items": with_loadout["loadout"],
            }
        )
    return squad, resources, loadout_log


def _action_score(hero: Dict[str, Any], directive: Dict[str, Any], action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    if hero["role"] not in action["roles"]:
        return {"score": -999.0, "components": {"blocked_role": True}}
    attrs = hero["attributes"]
    derived = hero["derived"]
    components: Dict[str, float] = {"base": float(action["base_score"]), "role_fit": 2.0}
    for tag in action["tags"]:
        if tag in DIRECTIVE_KEYS:
            components[f"directive:{tag}"] = round(directive[tag] * 3, 3)
        if tag in hero.get("class_tags", []):
            components[f"class_tag:{tag}"] = 1.0
        if tag in hero.get("loadout_tags", []):
            components[f"loadout_tag:{tag}"] = 1.0
    for attr, mult in action["scales"].items():
        components[f"attr:{attr}"] = round(attrs[attr] * mult / 3, 3)

    if action["effect"].get("heal", 0) and context.get("lowest_ally_hp_ratio", 1.0) <= 0.65:
        components["wounded_ally_urgency"] = round((1.0 - context["lowest_ally_hp_ratio"]) * 6, 3)
    if action["id"] == "secure_exit_lane" and context.get("extraction_timer", 99) <= 12:
        components["extraction_urgency"] = 3.0
    if action["effect"].get("damage", 0) and context.get("enemy_pressure", 0) >= 6:
        components["enemy_pressure"] = 2.0
    if action["id"] == "scan_relic_signal" and context.get("unclaimed_objective", True):
        components["objective_unclaimed"] = 2.0

    components["initiative_bias"] = round(derived["initiative"] / 20, 3)
    score = round(sum(components.values()), 3)
    return {"score": score, "components": components}


def choose_action(
    seed: str,
    hero: Dict[str, Any],
    directive: Dict[str, Any],
    actions: List[Dict[str, Any]],
    context: Dict[str, Any],
    round_no: int,
) -> Dict[str, Any]:
    scored = []
    for action in actions:
        score_doc = _action_score(hero, directive, action, context)
        jitter = stable_int(seed, f"choice:{round_no}:{hero['player']}:{action['id']}", 0, 99) / 1000
        scored.append((score_doc["score"] + jitter, action["id"], action, score_doc))
    scored.sort(key=lambda item: (-item[0], item[1]))
    _, _, action, score_doc = scored[0]
    chosen = copy.deepcopy(action)
    chosen["score"] = round(score_doc["score"], 3)
    chosen["score_components"] = score_doc["components"]
    return chosen


def _lowest_ally_hp_ratio(squad: List[Dict[str, Any]]) -> float:
    return min((h["hp"] / h["max_hp"] for h in squad if h["max_hp"] > 0), default=1.0)


def _enemy_pressure(enemies: List[Dict[str, Any]]) -> int:
    return sum(e["threat"] for e in enemies if e["hp"] > 0)


def _target_enemy(enemies: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    live = [e for e in enemies if e["hp"] > 0]
    if not live:
        return None
    live.sort(key=lambda e: (-e["threat"], e["hp"], e["id"]))
    return live[0]


def resolve_tactical_encounter(
    seed: str,
    squad: List[Dict[str, Any]],
    clocks: Dict[str, int],
    max_rounds: int = 4,
    min_rounds: int = 3,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    enemies = copy.deepcopy(ENEMY_GROUP)
    rounds: List[Dict[str, Any]] = []
    objective_progress = 0
    noise = clocks.get("noise", 0)
    mitigation_pool = 0

    for round_no in range(1, max_rounds + 1):
        context = {
            "lowest_ally_hp_ratio": _lowest_ally_hp_ratio(squad),
            "enemy_pressure": _enemy_pressure(enemies),
            "extraction_timer": clocks.get("extraction_timer", 99),
            "unclaimed_objective": objective_progress < 6,
        }
        hero_actions = []
        mitigation_pool = 0

        for hero in sorted(squad, key=lambda h: (-h["derived"]["initiative"], h["player"])):
            if hero["hp"] <= 0:
                continue
            directive = hero["directive"]
            main_action = choose_action(seed, hero, directive, MAIN_ACTIONS, context, round_no)
            bonus_action = choose_action(seed, hero, directive, BONUS_ACTIONS, context, round_no)
            budget = {
                "movement": min(hero["derived"]["movement"], 2 + int(directive["mobility"] * hero["derived"]["movement"])),
                "main": main_action["budget"]["main"],
                "bonus": bonus_action["budget"]["bonus"],
                "reaction_reserved": 1 if directive["survival"] >= 0.7 else 0,
            }
            effects: List[Dict[str, Any]] = []

            for action in (main_action, bonus_action):
                effect = action["effect"]
                if effect.get("mitigation", 0):
                    mitigation = effect["mitigation"] + hero["derived"]["armor"] // 2
                    mitigation_pool += mitigation
                    effects.append({"type": "mitigation", "action": action["id"], "value": mitigation})
                if effect.get("heal", 0):
                    target = min(squad, key=lambda h: h["hp"] / h["max_hp"])
                    before = target["hp"]
                    heal = effect["heal"] + hero["derived"]["healing_power"] + stable_int(seed, f"heal:{round_no}:{hero['player']}:{action['id']}", 0, 3)
                    target["hp"] = min(target["max_hp"], target["hp"] + heal)
                    effects.append({"type": "heal", "action": action["id"], "target": target["player"], "before": before, "after": target["hp"], "value": heal})
                if effect.get("damage", 0):
                    target_enemy = _target_enemy(enemies)
                    if target_enemy:
                        before = target_enemy["hp"]
                        raw = effect["damage"] + hero["derived"]["damage_power"] + stable_int(seed, f"dmg:{round_no}:{hero['player']}:{action['id']}", 0, 5)
                        damage = max(1, raw - target_enemy["armor"])
                        target_enemy["hp"] = max(0, target_enemy["hp"] - damage)
                        effects.append({"type": "damage", "action": action["id"], "target": target_enemy["id"], "before": before, "after": target_enemy["hp"], "value": damage})
                objective_progress += int(effect.get("objective", 0))
                noise = max(0, noise + int(effect.get("noise", 0)))

            hero_actions.append(
                {
                    "actor": hero["player"],
                    "hero": hero["name"],
                    "initiative": hero["derived"]["initiative"],
                    "budget": budget,
                    "main_action": _action_public_doc(main_action),
                    "bonus_action": _action_public_doc(bonus_action),
                    "effects": effects,
                }
            )

        enemy_actions = []
        for enemy in [e for e in enemies if e["hp"] > 0]:
            target = _choose_enemy_target(enemy, squad)
            if not target:
                continue
            raw = enemy["threat"] + stable_int(seed, f"enemy:{round_no}:{enemy['id']}", 1, 6)
            mitigated = min(raw, mitigation_pool)
            mitigation_pool -= mitigated
            damage = max(0, raw - target["derived"]["armor"] - mitigated)
            before = target["hp"]
            target["hp"] = max(0, target["hp"] - damage)
            enemy_actions.append(
                {
                    "actor": enemy["id"],
                    "target": target["player"],
                    "raw_threat": raw,
                    "mitigated": mitigated,
                    "damage": damage,
                    "before": before,
                    "after": target["hp"],
                }
            )

        rounds.append(
            {
                "round": round_no,
                "context": context,
                "hero_actions": hero_actions,
                "enemy_actions": enemy_actions,
                "enemy_state": copy.deepcopy(enemies),
                "squad_state": [_hero_state(h) for h in squad],
                "objective_progress": objective_progress,
                "noise": noise,
            }
        )

        if round_no >= min_rounds and objective_progress >= 7 and sum(1 for h in squad if h["hp"] > 0) >= 2:
            break

    heroes_alive = [h["player"] for h in squad if h["hp"] > 0]
    victory = objective_progress >= 7 and len(heroes_alive) >= 2
    result = {
        "victory": victory,
        "objective_progress": objective_progress,
        "noise": noise,
        "rounds": len(rounds),
        "heroes_alive": heroes_alive,
        "enemies_remaining": [e for e in enemies if e["hp"] > 0],
        "extraction_readiness": min(100, 40 + objective_progress * 8 + len(heroes_alive) * 6 - noise * 2),
    }
    return rounds, result


def _action_public_doc(action: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": action["id"],
        "tags": action["tags"],
        "budget": action["budget"],
        "score": action["score"],
        "score_components": action["score_components"],
        "effect": action["effect"],
    }


def _choose_enemy_target(enemy: Dict[str, Any], squad: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    live = [h for h in squad if h["hp"] > 0]
    if not live:
        return None
    if enemy["target_bias"] == "medic":
        medics = [h for h in live if h["role"] == "medic"]
        if medics:
            return medics[0]
    if enemy["target_bias"] == "lowest_armor":
        return min(live, key=lambda h: (h["derived"]["armor"], h["hp"], h["player"]))
    return max(live, key=lambda h: (h["derived"]["threat"], h["derived"]["armor"], h["player"]))


def _hero_state(hero: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "player": hero["player"],
        "hero": hero["name"],
        "role": hero["role"],
        "hp": hero["hp"],
        "max_hp": hero["max_hp"],
        "armor": hero["derived"]["armor"],
        "movement": hero["derived"]["movement"],
        "initiative": hero["derived"]["initiative"],
        "resolve": hero["derived"]["resolve"],
    }


def apply_progression(squad: List[Dict[str, Any]], camp: Dict[str, Any], tactical_result: Dict[str, Any], mission_rewards: Dict[str, int]) -> Dict[str, Any]:
    rewards = copy.deepcopy(mission_rewards)
    if not tactical_result["victory"]:
        rewards = {k: max(0, v // 2) for k, v in rewards.items()}
    for key, value in rewards.items():
        if key != "xp":
            camp["resources"][key] = camp["resources"].get(key, 0) + value

    camp["heat"] += 2 + max(0, tactical_result["noise"] // 3)
    camp["morale"] += 1 if tactical_result["victory"] else -1
    if tactical_result["extraction_readiness"] >= 80:
        camp["morale"] += 1
    if camp["resources"].get("scrap", 0) >= 25:
        camp["facilities"]["armory_rack"]["level"] = max(2, camp["facilities"]["armory_rack"]["level"])
    if camp["resources"].get("intel", 0) >= 5:
        camp["facilities"]["strategium_table"]["level"] = max(1, camp["facilities"]["strategium_table"]["level"])
    camp["persistent_events"].append(
        {
            "id": "black_reliquary_claimed" if tactical_result["victory"] else "reliquary_run_failed",
            "result": "victory" if tactical_result["victory"] else "failure",
            "heat_after": camp["heat"],
        }
    )

    hero_progress = []
    for hero in squad:
        xp_gain = rewards.get("xp", 0) + (25 if hero["hp"] > 0 else 0) + tactical_result["objective_progress"] * 2
        hero["xp"] = hero.get("xp", 0) + xp_gain
        while hero["xp"] >= 150:
            hero["level"] = hero.get("level", 1) + 1
            hero["xp"] -= 150
        trait = _progress_trait(hero)
        if trait and trait not in hero["traits"]:
            hero["traits"].append(trait)
        if hero["hp"] <= hero["max_hp"] // 3 and "stress_fracture" not in hero["injuries"]:
            hero["injuries"].append("stress_fracture")
        hero_progress.append(
            {
                "player": hero["player"],
                "hero": hero["name"],
                "level": hero["level"],
                "xp": hero["xp"],
                "xp_gain": xp_gain,
                "hp": hero["hp"],
                "max_hp": hero["max_hp"],
                "traits": hero["traits"],
                "injuries": hero["injuries"],
            }
        )
    return {"rewards": rewards, "camp": camp, "hero_progress": hero_progress}


def _progress_trait(hero: Dict[str, Any]) -> str | None:
    directive = hero["directive"]
    if directive["objective"] >= 0.8:
        return "objective_driven"
    if directive["survival"] >= 0.8:
        return "hard_to_kill"
    if directive["greed"] >= 0.7:
        return "relic_hungry"
    if directive["mobility"] >= 0.7:
        return "fast_entry"
    return "field_hardened" if hero["hp"] > hero["max_hp"] // 2 else "scarred_survivor"


def rules_summary() -> Dict[str, Any]:
    return {
        "schema": SCHEMA_VERSION,
        "attribute_budget": ATTRIBUTE_BUDGET,
        "attribute_keys": list(ATTRIBUTE_KEYS),
        "directive_keys": list(DIRECTIVE_KEYS),
        "hero_count": len(HERO_ARCHETYPES),
        "loadout_count": len(LOADOUT_CATALOG),
        "main_action_count": len(MAIN_ACTIONS),
        "bonus_action_count": len(BONUS_ACTIONS),
        "stat_formulas": {
            "max_hp": "18 + endurance*4 + force",
            "armor": "1 + floor(endurance/3) + loadout mods",
            "movement": "3 + floor(agility/2), capped 1..8",
            "initiative": "agility + floor(will/2)",
            "accuracy": "will + floor(agility/2) + loadout mods",
            "resolve": "will + presence + loadout mods",
            "supply_slots": "2 + floor(tech/3) + floor(endurance/4)",
        },
    }


def validate_rules_model() -> List[str]:
    errors: List[str] = []
    ids = set()
    for hero in build_roster():
        if hero["id"] in ids:
            errors.append(f"duplicate hero id {hero['id']}")
        ids.add(hero["id"])
        missing = [key for key in ATTRIBUTE_KEYS if key not in hero["attributes"]]
        if missing:
            errors.append(f"{hero['id']} missing attributes {missing}")
        if hero["attribute_budget"] != ATTRIBUTE_BUDGET:
            errors.append(f"{hero['id']} budget {hero['attribute_budget']} != {ATTRIBUTE_BUDGET}")
        if hero["derived"]["max_hp"] < 25:
            errors.append(f"{hero['id']} max_hp too low")
        if not (1 <= hero["derived"]["movement"] <= 8):
            errors.append(f"{hero['id']} movement out of range")
    for action in MAIN_ACTIONS:
        if action["budget"]["main"] != 1 or action["budget"]["bonus"] != 0:
            errors.append(f"main action {action['id']} has bad budget")
    for action in BONUS_ACTIONS:
        if action["budget"]["bonus"] != 1 or action["budget"]["main"] != 0:
            errors.append(f"bonus action {action['id']} has bad budget")
    roles = {hero["role"] for hero in HERO_ARCHETYPES}
    main_roles = {role for action in MAIN_ACTIONS for role in action["roles"]}
    bonus_roles = {role for action in BONUS_ACTIONS for role in action["roles"]}
    for role in sorted(roles):
        if role not in main_roles:
            errors.append(f"role {role} has no main action")
        if role not in bonus_roles:
            errors.append(f"role {role} has no bonus action")
        if role not in ROLE_LOADOUT_PRIORITIES:
            errors.append(f"role {role} has no loadout priorities")
    return errors
