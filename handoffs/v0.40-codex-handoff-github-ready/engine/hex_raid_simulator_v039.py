#!/usr/bin/env python3
# WoW Raiders v0.39 — balance + AI patch over v0.38
# Goal: keep deterministic hex simulation, but fix hero AI objective handling and overtuned enemy pressure.

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import argparse, copy, json, random
from pathlib import Path

HEX_DIRS = [(1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1)]

def hex_distance(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    aq, ar = a; bq, br = b
    ax, az = aq, ar; ay = -ax - az
    bx, bz = bq, br; by = -bx - bz
    return max(abs(ax-bx), abs(ay-by), abs(az-bz))

def step_towards(a: Tuple[int,int], b: Tuple[int,int], blocked: set, bounds: Tuple[int,int]) -> Tuple[int,int]:
    if a == b:
        return a
    W,H = bounds
    candidates = []
    for dq,dr in HEX_DIRS:
        n = (a[0]+dq, a[1]+dr)
        if n in blocked:
            continue
        if n[0] < 0 or n[1] < 0 or n[0] >= W or n[1] >= H:
            continue
        candidates.append(n)
    if not candidates:
        return a
    candidates.sort(key=lambda p: (hex_distance(p,b), p[0], p[1]))
    return candidates[0]

@dataclass
class Unit:
    id: str
    name: str
    side: str
    role: str
    max_hp: int
    hp: int
    armor: int
    speed: int
    focus: int
    pos: Tuple[int,int]
    alive: bool = True
    status: str = "normal"
    tags: Tuple[str,...] = ()

    def hp_str(self):
        return f"{max(0,self.hp)}/{self.max_hp}"

def ability(action_id, label, target, range_, base, tags=None, kind="damage"):
    return {"id": action_id, "label": label, "target": target, "range": range_, "base": base, "tags": tags or [], "kind": kind}

# v0.39 BALANCE CHANGES:
# - CandyPeace damage up, commander mark now useful on channelers.
# - Dr.Feed healing up and chooses preventive heal earlier.
# - EZ objective work buffed, but AI first handles channelers when they are blocking progress.
HERO_ABILITIES = {
    "CP": [
        ability("duelist_burst", "Дуэльная очередь", "enemy", 5, 34, ["elite_killer", "ranged"]),
        ability("command_mark", "Командная метка", "enemy", 6, 0, ["mark", "support"], kind="mark"),
        ability("covering_fire", "Подавляющий огонь", "enemy", 5, 20, ["ranged", "control"]),
        ability("guard_feed", "Прикрыть медика", "ally", 3, 0, ["guard"], kind="guard"),
    ],
    "DF": [
        ability("medicae_patch", "Медицинский протокол", "ally", 4, 36, ["heal"], kind="heal"),
        ability("stabilize", "Стабилизация", "ally", 1, 42, ["revive"], kind="revive"),
        ability("corrosive_round", "Коррозийный выстрел", "enemy", 4, 22, ["armor_break", "ranged"]),
    ],
    "EZ": [
        ability("void_bolt", "Пустотный разряд", "enemy", 6, 30, ["ranged", "void"]),
        ability("ward_break", "Слом печати", "objective", 5, 1, ["objective"], kind="objective"),
        ability("fear_hex", "Печать страха", "enemy", 4, 0, ["control"], kind="fear"),
    ]
}

# v0.39 BALANCE CHANGES:
# - enemy damage slightly down
# - channelers can delay objective, but not erase all progress
ENEMY_ABILITIES = {
    "champion": [
        ability("black_glaive", "Чёрная глефа", "hero", 1, 20, ["melee"]),
        ability("rally_cult", "Зов культа", "enemy", 4, 0, ["buff"], kind="buff"),
    ],
    "acolyte": [
        ability("ritual_channel", "Канал ритуала", "objective", 6, 1, ["objective"], kind="enemy_objective"),
        ability("bone_spark", "Костяная искра", "hero", 5, 11, ["ranged"]),
    ],
    "enforcer": [
        ability("chain_axe", "Цепной топор", "hero", 1, 15, ["melee"]),
        ability("advance_guard", "Жёсткий рывок", "hero", 1, 10, ["melee"]),
    ],
    "cultist": [
        ability("autogun", "Автоган", "hero", 4, 9, ["ranged"]),
        ability("rush_knife", "Ритуальный нож", "hero", 1, 8, ["melee"]),
    ]
}

def make_heroes():
    return {
        "CP": Unit("CP", "CandyPeace", "heroes", "командир / дуэлист", 178, 178, 6, 3, 64, (1,5), tags=("hero","commander")),
        "DF": Unit("DF", "Dr.Feed", "heroes", "медик / саппорт", 145, 145, 5, 3, 85, (1,7), tags=("hero","medic")),
        "EZ": Unit("EZ", "EZ", "heroes", "стрелок / оккультный контроль", 132, 132, 4, 3, 70, (1,9), tags=("hero","occult")),
    }

def make_encounter_1():
    return {
        "encounter_id": "R01E01_HALL_OF_PENITENTS",
        "title": "Зал кающихся",
        # v0.39 objective required lowered from 4 to 3; this is first room, not boss room.
        "objective": {"id": "clear_hall", "label": "Зачистить зал", "progress": 0, "required": 3},
        "bounds": (10, 10),
        "blocked": [(4,4),(5,4),(4,5)],
        "enemies": {
            "CU1": Unit("CU1", "Культист-стрелок", "enemies", "cultist", 48, 48, 2, 2, 0, (7,3), tags=("cultist",)),
            "CU2": Unit("CU2", "Культист-фанатик", "enemies", "cultist", 48, 48, 2, 2, 0, (8,6), tags=("cultist",)),
            "EN1": Unit("EN1", "Цепной палач", "enemies", "enforcer", 68, 68, 4, 2, 0, (6,5), tags=("enforcer",)),
            "AC1": Unit("AC1", "Аколит культа", "enemies", "acolyte", 64, 64, 2, 2, 0, (8,8), tags=("acolyte","channeler")),
        },
        "max_rounds": 8,
    }

def make_encounter_2():
    return {
        "encounter_id": "R01E02_RELIQUARY_OF_ASH",
        "title": "Реликварий пепла",
        "objective": {"id": "break_ward", "label": "Сломать реликварную печать", "progress": 0, "required": 3},
        "bounds": (11, 11),
        "blocked": [(5,5),(5,6),(6,5)],
        "enemies": {
            "CH1": Unit("CH1", "Чемпион культа", "enemies", "champion", 108, 108, 6, 2, 0, (8,4), tags=("champion","elite")),
            "AC2": Unit("AC2", "Аколит реликвария", "enemies", "acolyte", 76, 76, 3, 2, 0, (9,6), tags=("acolyte","channeler")),
            "EN2": Unit("EN2", "Культовый палач", "enemies", "enforcer", 65, 65, 4, 2, 0, (7,7), tags=("enforcer",)),
            "CU3": Unit("CU3", "Красный проповедник", "enemies", "cultist", 58, 58, 2, 2, 0, (6,8), tags=("cultist","ranged")),
            "CU4": Unit("CU4", "Жнец в капюшоне", "enemies", "cultist", 52, 52, 2, 2, 0, (9,9), tags=("cultist",)),
        },
        "max_rounds": 9,
    }

class Simulator:
    def __init__(self, seed="campaign03_raid01_ritual_assembly_v039"):
        self.rng = random.Random(seed)
        self.seed = seed
        self.audit = []
        self.turn_log = []
        self.guard_target = None
        self.hero_stats = {hid: {"damage_dealt":0,"damage_taken":0,"healing_done":0,"kills":0,"downs":0,"objective_actions":0,"actions":0,"guards":0} for hid in ["CP","DF","EZ"]}

    def log_delta(self, encounter_id, round_no, activation, kind, source, target, before, after, reason):
        delta = after - before if isinstance(before, int) and isinstance(after, int) else None
        item = {"encounter_id": encounter_id, "round": round_no, "activation": activation, "kind": kind, "source": source, "target": target, "before": before, "after": after, "delta": delta, "reason": reason}
        self.audit.append(item)
        return item

    def units_state(self, units):
        return {k: {"id":u.id,"name":u.name,"side":u.side,"role":u.role,"hp":u.hp_str(),"armor":u.armor,"focus":u.focus,"pos":list(u.pos),"alive":u.alive,"status":u.status} for k,u in units.items()}

    def alive(self, units, side=None):
        return [u for u in units.values() if u.alive and (side is None or u.side == side)]

    def channelers_alive(self, units):
        return [u for u in self.alive(units, "enemies") if "channeler" in u.tags]

    def choose_hero_action(self, hero, units, objective, marked):
        enemies = self.alive(units, "enemies")
        allies = self.alive(units, "heroes")
        actions = []

        # v0.39 tactical director: if channelers are alive, objective-control heroes focus them before raw objective spam.
        channelers = self.channelers_alive(units)

        if hero.id == "DF":
            downed = [u for u in units.values() if u.side=="heroes" and not u.alive and hex_distance(hero.pos,u.pos)<=1]
            if downed:
                actions.append((120, HERO_ABILITIES["DF"][1], downed[0].id, ["приоритет: поднять союзника"]))
            injured = [u for u in allies if u.hp/u.max_hp < 0.72 and hex_distance(hero.pos,u.pos) <= 4]
            if injured:
                injured.sort(key=lambda u: u.hp/u.max_hp)
                actions.append((96, HERO_ABILITIES["DF"][0], injured[0].id, ["раннее лечение: союзник ниже 72% HP"]))

        if hero.id == "CP":
            # guard medic if Dr.Feed is being pressured
            df = units.get("DF")
            if df and df.alive and df.hp/df.max_hp < 0.68 and hex_distance(hero.pos, df.pos) <= 3:
                actions.append((92, HERO_ABILITIES["CP"][3], "DF", ["Dr.Feed под давлением, включить прикрытие"]))
            elite_or_channeler = [e for e in enemies if "elite" in e.tags or "channeler" in e.tags]
            if elite_or_channeler:
                elite_or_channeler.sort(key=lambda u: (0 if "channeler" in u.tags else 1, u.hp))
                actions.append((88, HERO_ABILITIES["CP"][0], elite_or_channeler[0].id, ["приоритет: элита/ченнелер"]))

        if hero.id == "EZ":
            if channelers:
                channelers.sort(key=lambda u: u.hp)
                # If channeler exists and objective not secured, target channeler unless objective one point from completion.
                if objective["progress"] < objective["required"] - 1:
                    actions.append((94, HERO_ABILITIES["EZ"][0], channelers[0].id, ["директор: сначала убрать ченнелера"]))
            if objective["progress"] < objective["required"]:
                actions.append((88 + objective["progress"]*8, HERO_ABILITIES["EZ"][1], objective["id"], ["специалист по печати"]))

        for ab in HERO_ABILITIES[hero.id]:
            if ab["kind"] != "damage":
                continue
            in_range = [e for e in enemies if hex_distance(hero.pos, e.pos) <= ab["range"]]
            if in_range:
                def score_enemy(e):
                    s = 55
                    if "channeler" in e.tags: s += 28
                    if "elite" in e.tags: s += 12
                    if e.id in marked: s += 10
                    s += (1 - e.hp/e.max_hp)*24
                    return s
                in_range.sort(key=lambda e: (-score_enemy(e), e.hp, e.id))
                actions.append((score_enemy(in_range[0]), ab, in_range[0].id, ["лучшая цель в радиусе"]))

        if not actions:
            if enemies:
                enemies.sort(key=lambda e: hex_distance(hero.pos,e.pos))
                return {"type":"move","label":"Смена позиции","target":enemies[0].id,"score":40,"reason":["нет действия в радиусе"]}
            return {"type":"wait","label":"Ожидание","target":None,"score":10,"reason":["нет целей"]}

        actions.sort(key=lambda x: (-x[0], x[1]["id"]))
        score, ab, target, reason = actions[0]
        return {"type":"ability","ability":ab,"label":ab["label"],"target":target,"score":round(score,2),"reason":reason}

    def choose_enemy_action(self, enemy, units, objective):
        heroes = self.alive(units, "heroes")
        if not heroes:
            return {"type":"wait","label":"Ожидание","target":None,"score":0,"reason":["нет героев"]}

        # v0.39: channelers channel every other round implicitly via status/pressure; they cannot endlessly erase progress.
        if "channeler" in enemy.tags and objective["progress"] < objective["required"] and objective["progress"] > 0:
            return {"type":"ability","ability":ENEMY_ABILITIES["acolyte"][0],"label":"Канал ритуала","target":objective["id"],"score":76,"reason":["мешает прогрессу цели, но не сбрасывает её в ноль"]}

        def score_hero(h):
            s = 40
            # v0.39: less tunnel vision on medic
            if h.id == "DF": s += 4
            if h.hp/h.max_hp < 0.45: s += 16
            s -= hex_distance(enemy.pos,h.pos)*3
            return s

        heroes.sort(key=lambda h: (-score_hero(h), h.hp, h.id))
        target = heroes[0]
        role = "champion" if "champion" in enemy.tags else "acolyte" if "acolyte" in enemy.tags else "enforcer" if "enforcer" in enemy.tags else "cultist"
        for ab in ENEMY_ABILITIES[role]:
            if ab["kind"] == "damage" and hex_distance(enemy.pos, target.pos) <= ab["range"]:
                return {"type":"ability","ability":ab,"label":ab["label"],"target":target.id,"score":round(score_hero(target),2),"reason":["лучшая цель среди героев"]}
        return {"type":"move","label":"Сближение","target":target.id,"score":35,"reason":["вне радиуса"]}

    def apply_action(self, encounter_id, round_no, activation, actor, action, units, objective, marked, bounds):
        deltas = []
        before_state = {"objective": copy.deepcopy(objective), "units": self.units_state(units)}

        if action["type"] == "move":
            target = units[action["target"]]
            occupied = {u.pos for u in units.values() if u.alive and u.id != actor.id}
            old = actor.pos
            blocked = set(occupied)
            for _ in range(actor.speed):
                actor.pos = step_towards(actor.pos, target.pos, blocked, bounds)
                if hex_distance(actor.pos, target.pos) <= 1:
                    break
            deltas.append(self.log_delta(encounter_id, round_no, activation, "position", actor.id, actor.id, list(old), list(actor.pos), action["label"]))

        elif action["type"] == "ability":
            ab = action["ability"]
            if ab["kind"] == "damage":
                target = units[action["target"]]
                before = target.hp
                dmg = max(1, ab["base"] + self.rng.randint(-3, 4) + (10 if target.id in marked else 0) - target.armor)
                # Guard mitigation if Dr.Feed is guarded
                if target.id == self.guard_target:
                    dmg = max(1, int(dmg * 0.55))
                target.hp = max(0, target.hp - dmg)
                if actor.side == "heroes":
                    self.hero_stats[actor.id]["damage_dealt"] += before - target.hp
                    self.hero_stats[actor.id]["actions"] += 1
                if target.side == "heroes":
                    self.hero_stats[target.id]["damage_taken"] += before - target.hp
                if target.hp <= 0 and target.alive:
                    target.alive = False
                    target.status = "downed" if target.side == "heroes" else "dead"
                    if actor.side=="heroes" and target.side=="enemies":
                        self.hero_stats[actor.id]["kills"] += 1
                    if target.side=="heroes":
                        self.hero_stats[target.id]["downs"] += 1
                deltas.append(self.log_delta(encounter_id, round_no, activation, "hp", actor.id, target.id, before, target.hp, action["label"]))

            elif ab["kind"] == "heal":
                target = units[action["target"]]
                before = target.hp
                target.hp = min(target.max_hp, target.hp + ab["base"] + self.rng.randint(-2,4))
                self.hero_stats[actor.id]["healing_done"] += target.hp - before
                self.hero_stats[actor.id]["actions"] += 1
                deltas.append(self.log_delta(encounter_id, round_no, activation, "hp", actor.id, target.id, before, target.hp, action["label"]))

            elif ab["kind"] == "revive":
                target = units[action["target"]]
                before = {"alive":target.alive, "hp":target.hp}
                target.alive = True
                target.status = "stabilized"
                target.hp = min(target.max_hp, ab["base"])
                self.hero_stats[actor.id]["healing_done"] += target.hp - before["hp"]
                self.hero_stats[actor.id]["actions"] += 1
                deltas.append(self.log_delta(encounter_id, round_no, activation, "revive", actor.id, target.id, before, {"alive":target.alive,"hp":target.hp}, action["label"]))

            elif ab["kind"] == "objective":
                before = objective["progress"]
                objective["progress"] = min(objective["required"], objective["progress"] + ab["base"])
                self.hero_stats[actor.id]["objective_actions"] += 1
                self.hero_stats[actor.id]["actions"] += 1
                deltas.append(self.log_delta(encounter_id, round_no, activation, "objective", actor.id, objective["id"], before, objective["progress"], action["label"]))

            elif ab["kind"] == "enemy_objective":
                before = objective["progress"]
                # v0.39: enemy channel delays by 1, but cannot drop below progress 1 once heroes started securing room.
                objective["progress"] = max(1, objective["progress"] - ab["base"])
                deltas.append(self.log_delta(encounter_id, round_no, activation, "objective_pressure", actor.id, objective["id"], before, objective["progress"], action["label"]))

            elif ab["kind"] == "mark":
                target = units[action["target"]]
                before = target.status
                marked.add(target.id)
                target.status = "marked"
                self.hero_stats[actor.id]["actions"] += 1
                deltas.append(self.log_delta(encounter_id, round_no, activation, "status", actor.id, target.id, before, target.status, action["label"]))

            elif ab["kind"] == "fear":
                target = units[action["target"]]
                before = target.status
                target.status = "feared"
                self.hero_stats[actor.id]["actions"] += 1
                deltas.append(self.log_delta(encounter_id, round_no, activation, "status", actor.id, target.id, before, target.status, action["label"]))

            elif ab["kind"] == "guard":
                before = self.guard_target
                self.guard_target = action["target"]
                self.hero_stats[actor.id]["guards"] += 1
                self.hero_stats[actor.id]["actions"] += 1
                deltas.append(self.log_delta(encounter_id, round_no, activation, "guard", actor.id, action["target"], before, self.guard_target, action["label"]))

            elif ab["kind"] == "buff":
                deltas.append(self.log_delta(encounter_id, round_no, activation, "buff", actor.id, actor.id, "none", "rally", action["label"]))

        after_state = {"objective": copy.deepcopy(objective), "units": self.units_state(units)}
        self.turn_log.append({
            "encounter_id": encounter_id, "round": round_no, "activation": activation,
            "actor": actor.id, "actor_name": actor.name, "side": actor.side,
            "chosen_action": {
                "label": action.get("label"),
                "type": action.get("type"),
                "target": action.get("target"),
                "score": action.get("score"),
                "reason": action.get("reason"),
            },
            "state_delta": deltas,
            "state_before": before_state,
            "state_after": after_state
        })

    def run_encounter(self, encounter, heroes):
        units = {hid: copy.deepcopy(h) for hid,h in heroes.items()}
        units.update({eid: copy.deepcopy(e) for eid,e in encounter["enemies"].items()})
        objective = copy.deepcopy(encounter["objective"])
        marked = set()
        self.guard_target = None
        start_audit = len(self.audit)
        start_turn = len(self.turn_log)
        activation = 0
        outcome = "unresolved"
        for r in range(1, encounter["max_rounds"]+1):
            order = sorted([u for u in units.values() if u.alive], key=lambda u: (0 if u.side=="heroes" else 1, u.id))
            for actor in order:
                if not actor.alive:
                    continue
                if objective["progress"] >= objective["required"]:
                    outcome = "victory"; break
                if not self.alive(units,"heroes"):
                    outcome = "wipe"; break
                action = self.choose_hero_action(actor, units, objective, marked) if actor.side=="heroes" else self.choose_enemy_action(actor, units, objective)
                activation += 1
                self.apply_action(encounter["encounter_id"], r, activation, actor, action, units, objective, marked, encounter["bounds"])
                if objective["progress"] >= objective["required"]:
                    outcome = "victory"; break
                if not self.alive(units,"heroes"):
                    outcome = "wipe"; break
            if outcome in ("victory","wipe"):
                break
        if outcome == "unresolved":
            outcome = "partial" if objective["progress"] > 0 else "failed"
        for hid in heroes:
            heroes[hid].hp = units[hid].hp
            heroes[hid].alive = units[hid].alive
            heroes[hid].status = units[hid].status
            heroes[hid].pos = units[hid].pos
        return {
            "encounter_id": encounter["encounter_id"],
            "title": encounter["title"],
            "outcome": outcome,
            "rounds_used": max([t["round"] for t in self.turn_log[start_turn:]] or [0]),
            "activations": len(self.turn_log[start_turn:]),
            "objective": f'{objective["progress"]}/{objective["required"]}',
            "heroes": {hid: heroes[hid].hp_str() for hid in heroes},
            "heroes_alive": f'{len([h for h in heroes.values() if h.alive])}/3',
            "enemies_defeated": [u.name for u in units.values() if u.side=="enemies" and not u.alive],
            "enemies_remaining": [u.name for u in units.values() if u.side=="enemies" and u.alive],
            "turn_log_start": start_turn,
            "turn_log_end": len(self.turn_log),
            "audit_start": start_audit,
            "audit_end": len(self.audit)
        }

def run_full_raid(seed="campaign03_raid01_ritual_assembly_v039"):
    sim = Simulator(seed)
    heroes = make_heroes()
    resources = {"requisition":80, "medkits":2, "ammo_crates":3, "intel":0, "black_shard":0, "cult_seals":0}
    events = [
        {"id":"ST01","type":"strategic_step","title":"Путь к Ритуальному собору","outcome":"route_selected","details":"Прямой маршрут: вход в руины → зал кающихся → реликварий пепла → лифт эвакуации."}
    ]

    enc1 = make_encounter_1()
    r1 = sim.run_encounter(enc1, heroes)
    events.append({"id":"ENC01","type":"tactical_battle","title":enc1["title"],"result":r1})
    if r1["outcome"] == "victory":
        resources["cult_seals"] += 1; resources["intel"] += 1; resources["requisition"] += 35

    lowest = min(heroes.values(), key=lambda h: h.hp/h.max_hp)
    if resources["medkits"] > 0 and lowest.hp/lowest.max_hp < 0.78:
        before = lowest.hp
        lowest.hp = min(lowest.max_hp, lowest.hp + 48)
        resources["medkits"] -= 1
        sim.log_delta("ST02_RECOVERY",0,0,"hp","DF",lowest.id,before,lowest.hp,"Полевой мед-набор между боями")
        events.append({"id":"ST02","type":"strategic_step","title":"Крипта свечей","outcome":"recovery_and_intel","details":f"Dr.Feed тратит мед-набор на {lowest.name}: {before}->{lowest.hp} HP."})
    else:
        events.append({"id":"ST02","type":"strategic_step","title":"Крипта свечей","outcome":"intel_found","details":"Сквад обнаруживает карту реликвария без траты мед-набора."})

    heroes["CP"].pos=(1,5); heroes["DF"].pos=(1,7); heroes["EZ"].pos=(1,9)
    enc2 = make_encounter_2()
    r2 = sim.run_encounter(enc2, heroes)
    events.append({"id":"ENC02","type":"tactical_battle","title":enc2["title"],"result":r2})
    if r2["outcome"] == "victory":
        resources["black_shard"] += 1; resources["cult_seals"] += 2; resources["requisition"] += 50; resources["intel"] += 1

    all_alive = all(h.alive for h in heroes.values())
    events.append({"id":"EXT01","type":"extraction","title":"Лифт эвакуации","outcome":"successful_extraction" if all_alive else "extraction_with_casualties","details":"Рейд завершён выходом через лифт эвакуации."})

    xp = {}
    for hid,h in heroes.items():
        gain = (210 if r1["outcome"]=="victory" else 90) + (320 if r2["outcome"]=="victory" else 120) + (60 if all_alive else 0)
        xp[hid] = {"gained":gain, "level":7, "xp_after":f"{1200+gain}/2500"}
    return {
        "schema_version":"wow-raiders.raid-run.v0.39",
        "seed":seed,
        "campaign_id":"campaign03_raid01_ritual_assembly",
        "title":"Кампания 03 · Рейд 01 · Ритуальный собор",
        "status":events[-1]["outcome"],
        "balance_patch": "v0.39_objective_and_medic_ai",
        "heroes": {hid: {"name":h.name,"hp":h.hp_str(),"alive":h.alive,"status":h.status,"level":7,"xp":xp[hid]["xp_after"],"role":h.role} for hid,h in heroes.items()},
        "resources": resources,
        "events": events,
        "encounter_results": [r1, r2],
        "hero_stats": sim.hero_stats,
        "turn_log": sim.turn_log,
        "audit_log": sim.audit,
        "qa_basis": {"hex_distance_used":True,"positions_tracked":True,"hp_from_audit":True,"objective_from_audit":True,"image_outputs_are_not_truth":True}
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", default="campaign03_raid01_ritual_assembly_v039")
    args = ap.parse_args()
    result = run_full_raid(args.seed)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status":result["status"],"turns":len(result["turn_log"]),"audit":len(result["audit_log"]),"encounters":[e["outcome"] for e in result["encounter_results"]]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
