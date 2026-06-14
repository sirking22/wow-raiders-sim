"""Blackstar Raiders v0.52 compact playable/runtime prototype.

This file is the current executable game snapshot, not a moodboard.
It captures the active direction:

- strategic layer: 32x32 open-world hex sector;
- tactical layer: 12x12 hex encounters;
- player party: neutral interspecies salvage/exploration artel;
- mechanics: fog of war, visibility radius, scouting, terrain, events, units;
- source of truth: data/runtime first, visuals second.

The code is intentionally compact so Codex/Notion/future agents can understand
where the game currently is before expanding it into modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from math import floor
from random import Random
from typing import Dict, Iterable, List, Optional, Tuple

Coord = Tuple[int, int]


class TileState(str, Enum):
    UNKNOWN = "unknown"
    VISIBLE = "visible"
    SCANNED = "scanned"
    DISCOVERED = "discovered"


class Terrain(str, Enum):
    BLOCKED = "blocked"
    ASH_WASTE = "ash_waste"
    RUINS = "ruins"
    INDUSTRIAL_HULK = "industrial_hulk"
    CATACOMBS = "catacombs"
    RELIC_SITE = "relic_site"
    SAFE_CAMP = "safe_camp"
    ENEMY_ZONE = "enemy_zone"


class EventKind(str, Enum):
    CALM = "calm"
    RESOURCE = "resource"
    INTEL = "intel"
    HAZARD = "hazard"
    BATTLE = "battle"
    BOSS = "boss"
    MYSTERY = "mystery"


TERRAIN_RULES: Dict[Terrain, Dict[str, int]] = {
    Terrain.BLOCKED: {"move_cost": 999, "risk": 999},
    Terrain.ASH_WASTE: {"move_cost": 2, "risk": 1},
    Terrain.RUINS: {"move_cost": 1, "risk": 2},
    Terrain.INDUSTRIAL_HULK: {"move_cost": 2, "risk": 3},
    Terrain.CATACOMBS: {"move_cost": 2, "risk": 4},
    Terrain.RELIC_SITE: {"move_cost": 1, "risk": 5},
    Terrain.SAFE_CAMP: {"move_cost": 1, "risk": 0},
    Terrain.ENEMY_ZONE: {"move_cost": 2, "risk": 5},
}


@dataclass(frozen=True)
class Attributes:
    force: int
    agility: int
    endurance: int
    will: int
    tech: int
    presence: int

    @property
    def budget(self) -> int:
        return self.force + self.agility + self.endurance + self.will + self.tech + self.presence


@dataclass(frozen=True)
class DerivedStats:
    max_hp: int
    armor: int
    move: int
    initiative: int
    accuracy: int
    resolve: int
    supply_slots: int
    damage_power: int
    healing: int
    objective_power: int
    threat: int
    max_focus: int


def derive_stats(a: Attributes, mods: Optional[Dict[str, int]] = None) -> DerivedStats:
    mods = mods or {}
    return DerivedStats(
        max_hp=18 + a.endurance * 4 + a.force + mods.get("max_hp", 0),
        armor=1 + floor(a.endurance / 3) + mods.get("armor", 0),
        move=max(1, min(8, 3 + floor(a.agility / 2) + mods.get("move", 0))),
        initiative=a.agility + floor(a.will / 2) + mods.get("initiative", 0),
        accuracy=a.will + floor(a.agility / 2) + mods.get("accuracy", 0),
        resolve=a.will + a.presence + mods.get("resolve", 0),
        supply_slots=2 + floor(a.tech / 3) + floor(a.endurance / 4) + mods.get("supply_slots", 0),
        damage_power=a.force + floor(a.will / 2) + mods.get("damage_power", 0),
        healing=floor(a.tech / 2) + floor(a.will / 3) + mods.get("healing", 0),
        objective_power=floor(a.will / 2) + floor(a.tech / 3) + floor(a.presence / 3) + mods.get("objective_power", 0),
        threat=a.force + floor(a.will / 2) + floor(a.presence / 2) + mods.get("threat", 0),
        max_focus=6 + floor(a.will / 2) + mods.get("max_focus", 0),
    )


@dataclass(frozen=True)
class Equipment:
    id: str
    name: str
    stat_mods: Dict[str, int]
    unlocks: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Ability:
    id: str
    name: str
    kind: str
    focus_cost: int
    base_damage: int = 0
    objective_progress: int = 0
    heal_amount: int = 0
    mitigation: int = 0


@dataclass
class Unit:
    id: str
    name: str
    faction: str
    role: str
    attrs: Optional[Attributes]
    stats: DerivedStats
    abilities: List[Ability]
    equipment: Optional[Equipment] = None
    visual_identity: str = ""
    hp: int = 0
    focus: int = 0
    pos: Coord = (0, 0)

    def __post_init__(self) -> None:
        if self.hp == 0:
            self.hp = self.stats.max_hp
        if self.focus == 0:
            self.focus = self.stats.max_focus

    @property
    def alive(self) -> bool:
        return self.hp > 0


HERO_EQUIPMENT = {
    "prism_focus": Equipment(
        id="prism_focus",
        name="Призменный фокус",
        stat_mods={"accuracy": 1, "max_focus": 1, "objective_power": 1},
        unlocks=["prism_lock", "pattern_anchor"],
    ),
    "refractor_field": Equipment(
        id="refractor_field",
        name="Рефракторное поле",
        stat_mods={"armor": 1, "threat": 1},
        unlocks=["guard_line"],
    ),
    "toxin_screen": Equipment(
        id="toxin_screen",
        name="Токсичный экран",
        stat_mods={"armor": 1, "healing": 1},
        unlocks=["field_surgery", "toxin_screen"],
    ),
}


ABILITIES = {
    "pattern_anchor": Ability("pattern_anchor", "Якорь узора", "objective", 2, objective_progress=6),
    "prism_lock": Ability("prism_lock", "Призменный замок", "damage_control", 3, base_damage=5),
    "mind_lance": Ability("mind_lance", "Копьё разума", "damage", 2, base_damage=4),
    "guard_line": Ability("guard_line", "Удержание линии", "mitigation", 1, mitigation=3),
    "shield_advance": Ability("shield_advance", "Щитовой рывок", "move_taunt", 2, base_damage=3),
    "void_smite": Ability("void_smite", "Удар Бездны", "damage", 2, base_damage=6),
    "field_surgery": Ability("field_surgery", "Полевая хирургия", "heal", 3, heal_amount=12),
    "patch_and_move": Ability("patch_and_move", "Заплатать и сдвинуться", "heal_move", 2, heal_amount=7),
    "toxin_screen": Ability("toxin_screen", "Токсичный экран", "debuff", 2, mitigation=2),
    "relic_maul": Ability("relic_maul", "Реликтовый удар", "damage", 0, base_damage=8),
    "suppressive_burst": Ability("suppressive_burst", "Подавляющая очередь", "damage", 0, base_damage=7),
    "skitter_strike": Ability("skitter_strike", "Рывок сервопауков", "damage", 0, base_damage=5),
    "scanner_ping": Ability("scanner_ping", "Сканирующий импульс", "mark", 0),
}


def make_heroes() -> List[Unit]:
    raw = [
        (
            "ez",
            "EZ",
            "Призма-псайкер",
            Attributes(2, 4, 3, 10, 3, 8),
            HERO_EQUIPMENT["prism_focus"],
            [ABILITIES["pattern_anchor"], ABILITIES["prism_lock"], ABILITIES["mind_lance"]],
            "purple prism psyker, slim explorer silhouette, prism focus/staff; must match hero-canon reference",
        ),
        (
            "candy_peace",
            "Candy Peace",
            "Часовенный Бездны / танк",
            Attributes(6, 3, 8, 6, 2, 5),
            HERO_EQUIPMENT["refractor_field"],
            [ABILITIES["guard_line"], ABILITIES["shield_advance"], ABILITIES["void_smite"]],
            "heavy armored tank knight, shield/refraction field, broad silhouette; must match hero-canon reference",
        ),
        (
            "dr_feed",
            "Dr.Feed",
            "Чумной хирург / медик",
            Attributes(2, 4, 5, 6, 8, 5),
            HERO_EQUIPMENT["toxin_screen"],
            [ABILITIES["field_surgery"], ABILITIES["patch_and_move"], ABILITIES["toxin_screen"]],
            "plague surgeon medic, mask, vials, green toxic accent; must match hero-canon reference",
        ),
    ]
    heroes: List[Unit] = []
    for uid, name, role, attrs, eq, abilities, visual in raw:
        heroes.append(
            Unit(
                id=uid,
                name=name,
                faction="blackstar_artel",
                role=role,
                attrs=attrs,
                stats=derive_stats(attrs, eq.stat_mods),
                abilities=abilities,
                equipment=eq,
                visual_identity=visual,
            )
        )
    return heroes


def make_enemy_pack() -> List[Unit]:
    enemy_specs = [
        ("vault_warden", "Хранитель реликвария", "objective_guardian", 58, 4, 4, 4, 7, 7, 5, 9, ABILITIES["relic_maul"]),
        ("suppressor", "Подавитель", "suppression", 42, 2, 5, 8, 10, 8, 4, 8, ABILITIES["suppressive_burst"]),
        ("servo_swarm", "Рой сервопауков", "fast_pressure", 34, 1, 6, 11, 8, 9, 4, 7, ABILITIES["skitter_strike"]),
        ("scanner_acolyte", "Сканирующий адепт", "heat_control", 28, 1, 5, 9, 8, 8, 2, 5, ABILITIES["scanner_ping"]),
    ]
    enemies: List[Unit] = []
    for uid, name, role, hp, armor, move, init, acc, resolve, damage, threat, ability in enemy_specs:
        stats = DerivedStats(
            max_hp=hp,
            armor=armor,
            move=move,
            initiative=init,
            accuracy=acc,
            resolve=resolve,
            supply_slots=0,
            damage_power=damage,
            healing=0,
            objective_power=0,
            threat=threat,
            max_focus=0,
        )
        enemies.append(Unit(uid, name, "hostile", role, None, stats, [ability], visual_identity=f"enemy role: {role}"))
    return enemies


@dataclass
class StrategicTile:
    q: int
    r: int
    terrain: Terrain
    state: TileState = TileState.UNKNOWN
    event_id: Optional[str] = None
    unit_id: Optional[str] = None

    @property
    def coord(self) -> Coord:
        return (self.q, self.r)


@dataclass(frozen=True)
class StrategicEvent:
    id: str
    name: str
    kind: EventKind
    coord: Coord
    risk: int
    reward: List[str]
    tactical_size: Optional[Tuple[int, int]] = None
    terrain_seed: str = ""


@dataclass
class PartyState:
    coord: Coord
    visibility_radius: int = 3
    strategic_move: int = 4
    supplies: int = 3
    fuel: int = 2
    intel: int = 0
    scrap: int = 0
    relic_shards: int = 0
    heat: int = 0


class StrategicSector:
    """32x32 open-world strategic map with fog, terrain and events.

    This is not a route-line board. Movement is on hex tiles.
    Events are points on the map, not a forced linear path.
    """

    width = 32
    height = 32

    def __init__(self, seed: int = 52052) -> None:
        self.rng = Random(seed)
        self.tiles: Dict[Coord, StrategicTile] = {}
        self.events: Dict[str, StrategicEvent] = {}
        self.party = PartyState(coord=(4, 16))
        self._generate_tiles()
        self._place_events()
        self.reveal(self.party.coord, self.party.visibility_radius, TileState.VISIBLE)
        self.discover(self.party.coord)

    def _generate_tiles(self) -> None:
        for q in range(self.width):
            for r in range(self.height):
                if q in (0, self.width - 1) or r in (0, self.height - 1):
                    terrain = Terrain.BLOCKED
                elif r < 10:
                    terrain = self.rng.choices(
                        [Terrain.RUINS, Terrain.INDUSTRIAL_HULK, Terrain.ENEMY_ZONE, Terrain.ASH_WASTE],
                        [30, 30, 25, 15],
                    )[0]
                elif r < 21:
                    terrain = self.rng.choices(
                        [Terrain.RUINS, Terrain.ASH_WASTE, Terrain.INDUSTRIAL_HULK, Terrain.CATACOMBS],
                        [40, 25, 20, 15],
                    )[0]
                else:
                    terrain = self.rng.choices(
                        [Terrain.ASH_WASTE, Terrain.RUINS, Terrain.CATACOMBS, Terrain.SAFE_CAMP],
                        [35, 25, 25, 15],
                    )[0]
                self.tiles[(q, r)] = StrategicTile(q, r, terrain)

    def _add_event(self, event: StrategicEvent, terrain: Terrain) -> None:
        self.events[event.id] = event
        tile = self.tiles[event.coord]
        tile.event_id = event.id
        tile.terrain = terrain

    def _place_events(self) -> None:
        events = [
            StrategicEvent("start_camp", "Посадочная площадка Нулевая свеча", EventKind.CALM, (4, 16), 0, ["rest", "repair"]),
            StrategicEvent("field_bazaar", "Полевой базар добытчиков", EventKind.CALM, (7, 20), 0, ["trade", "supplies"]),
            StrategicEvent("north_broken_cathedral", "Разбитый собор", EventKind.BATTLE, (9, 7), 3, ["relic_shards"], (12, 12), "cathedral_ruin"),
            StrategicEvent("silent_archive", "Архив безмолвия", EventKind.INTEL, (16, 6), 4, ["intel", "relic_clue"], (12, 12), "archive_halls"),
            StrategicEvent("red_coven", "Ковен теней", EventKind.BOSS, (25, 7), 6, ["major_relic"], (12, 12), "ritual_spire"),
            StrategicEvent("collapsed_streets", "Заваленные улицы", EventKind.RESOURCE, (9, 16), 1, ["scrap"]),
            StrategicEvent("bastion", "Опорный бастион", EventKind.BATTLE, (16, 16), 3, ["scrap", "intel"], (12, 12), "bastion_gate"),
            StrategicEvent("supply_vault", "Склады снабжения", EventKind.RESOURCE, (21, 15), 2, ["supplies", "fuel"]),
            StrategicEvent("abandoned_fortress", "Заброшенная крепость", EventKind.BATTLE, (25, 16), 4, ["relic_shards", "scrap"], (12, 12), "fortress_yard"),
            StrategicEvent("toxic_wastes", "Токсичные пустоши", EventKind.HAZARD, (9, 25), 1, ["bio_samples"]),
            StrategicEvent("infected_ruins", "Заражённые руины", EventKind.RESOURCE, (15, 26), 2, ["supplies", "scrap"]),
            StrategicEvent("forgotten_lab", "Забытая лаборатория", EventKind.INTEL, (18, 29), 3, ["tech_unlock", "intel"], (12, 12), "lab_ruin"),
            StrategicEvent("blight_lair", "Логово Скверны", EventKind.BATTLE, (25, 24), 4, ["relic_shards", "mutation_event"], (12, 12), "toxic_den"),
        ]
        terrain_for_kind = {
            EventKind.CALM: Terrain.SAFE_CAMP,
            EventKind.RESOURCE: Terrain.RUINS,
            EventKind.INTEL: Terrain.INDUSTRIAL_HULK,
            EventKind.HAZARD: Terrain.ASH_WASTE,
            EventKind.BATTLE: Terrain.ENEMY_ZONE,
            EventKind.BOSS: Terrain.RELIC_SITE,
            EventKind.MYSTERY: Terrain.CATACOMBS,
        }
        for event in events:
            self._add_event(event, terrain_for_kind[event.kind])

    @staticmethod
    def neighbors(coord: Coord) -> Iterable[Coord]:
        q, r = coord
        dirs_even = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, -1)]
        dirs_odd = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1)]
        for dq, dr in (dirs_odd if q % 2 else dirs_even):
            yield (q + dq, r + dr)

    @classmethod
    def distance(cls, a: Coord, b: Coord) -> int:
        # BFS distance is safer for odd-q offset maps at this prototype stage.
        if a == b:
            return 0
        frontier = [(a, 0)]
        seen = {a}
        while frontier:
            current, d = frontier.pop(0)
            for n in cls.neighbors(current):
                if n == b:
                    return d + 1
                if n not in seen and 0 <= n[0] < cls.width and 0 <= n[1] < cls.height:
                    seen.add(n)
                    frontier.append((n, d + 1))
        return 999

    def reveal(self, center: Coord, radius: int, state: TileState) -> None:
        for coord, tile in self.tiles.items():
            if self.distance(center, coord) <= radius and tile.terrain != Terrain.BLOCKED:
                if tile.state == TileState.UNKNOWN or state in (TileState.SCANNED, TileState.DISCOVERED):
                    tile.state = state

    def discover(self, coord: Coord) -> Optional[StrategicEvent]:
        tile = self.tiles[coord]
        if tile.terrain != Terrain.BLOCKED:
            tile.state = TileState.DISCOVERED
        return self.events.get(tile.event_id or "")

    def scout(self, coord: Coord, radius: int = 4) -> Dict[str, object]:
        cost = 1
        if self.party.intel >= cost:
            self.party.intel -= cost
        else:
            self.party.supplies = max(0, self.party.supplies - 1)
        self.reveal(coord, radius, TileState.SCANNED)
        visible_events = [asdict(e) for e in self.events.values() if self.tiles[e.coord].state != TileState.UNKNOWN]
        return {"action": "scout", "center": coord, "radius": radius, "visible_events": visible_events}

    def can_move_to(self, coord: Coord) -> bool:
        tile = self.tiles.get(coord)
        if tile is None or tile.terrain == Terrain.BLOCKED:
            return False
        if tile.state == TileState.UNKNOWN:
            # You can push into fog only from a visible/discovered neighbor.
            return any(self.tiles.get(n) and self.tiles[n].state != TileState.UNKNOWN for n in self.neighbors(coord))
        return True

    def move_party(self, target: Coord) -> Dict[str, object]:
        if not self.can_move_to(target):
            return {"ok": False, "reason": "blocked_or_unreachable_fog", "target": target}
        distance = self.distance(self.party.coord, target)
        if distance > self.party.strategic_move:
            return {"ok": False, "reason": "target_too_far_this_turn", "distance": distance, "move": self.party.strategic_move}
        tile = self.tiles[target]
        move_cost = TERRAIN_RULES[tile.terrain]["move_cost"]
        self.party.supplies = max(0, self.party.supplies - max(0, move_cost - 1))
        self.party.coord = target
        self.reveal(target, self.party.visibility_radius, TileState.VISIBLE)
        event = self.discover(target)
        risk = TERRAIN_RULES[tile.terrain]["risk"] + self.party.heat
        self.party.heat += 1 if event and event.kind in (EventKind.BATTLE, EventKind.BOSS, EventKind.HAZARD) else 0
        return {
            "ok": True,
            "action": "move_party",
            "target": target,
            "terrain": tile.terrain.value,
            "risk": risk,
            "event": asdict(event) if event else None,
            "party": asdict(self.party),
        }

    def visible_payload(self) -> Dict[str, object]:
        tiles = []
        for tile in self.tiles.values():
            if tile.state != TileState.UNKNOWN:
                tiles.append({
                    "q": tile.q,
                    "r": tile.r,
                    "terrain": tile.terrain.value,
                    "state": tile.state.value,
                    "event_id": tile.event_id,
                    "unit_id": tile.unit_id,
                })
        return {
            "schema": "blackstar-raiders.strategic-visible-payload.v0.52",
            "map": {"type": "hex", "width": self.width, "height": self.height},
            "party": asdict(self.party),
            "visible_tiles": tiles,
            "visible_events": [asdict(e) for e in self.events.values() if self.tiles[e.coord].state != TileState.UNKNOWN],
            "hard_rule": "no route-lines: this is an open-world hex sector with fog of war",
        }


@dataclass
class TacticalEncounter:
    id: str
    size: Tuple[int, int]
    terrain_seed: str
    objective_cell: Coord
    extraction_cell: Coord
    heroes: List[Unit]
    enemies: List[Unit]
    objective_required: int = 10
    objective_progress: int = 0
    action_log: List[Dict[str, object]] = field(default_factory=list)

    def initiative_order(self) -> List[Unit]:
        units = [u for u in self.heroes + self.enemies if u.alive]
        return sorted(units, key=lambda u: u.stats.initiative, reverse=True)

    def use_ability(self, actor: Unit, ability: Ability, target: Optional[Unit] = None) -> Dict[str, object]:
        if actor.focus < ability.focus_cost:
            event = {"actor": actor.name, "ability": ability.name, "ok": False, "reason": "not_enough_focus"}
            self.action_log.append(event)
            return event
        actor.focus -= ability.focus_cost
        event: Dict[str, object] = {"actor": actor.name, "ability": ability.name, "ok": True, "kind": ability.kind}
        if ability.objective_progress:
            progress = ability.objective_progress + actor.stats.objective_power
            self.objective_progress += progress
            event["objective_progress"] = {"added": progress, "total": self.objective_progress, "required": self.objective_required}
        if ability.heal_amount and target:
            before = target.hp
            target.hp = min(target.stats.max_hp, target.hp + ability.heal_amount + actor.stats.healing)
            event["heal"] = {"target": target.name, "before": before, "after": target.hp}
        if ability.base_damage and target:
            roll = 3
            raw = ability.base_damage + actor.stats.damage_power + roll
            final = max(0, raw - target.stats.armor)
            before = target.hp
            target.hp = max(0, target.hp - final)
            event["damage"] = {
                "target": target.name,
                "formula": f"{ability.base_damage} base + {actor.stats.damage_power} damage_power + {roll} roll - {target.stats.armor} armor",
                "raw": raw,
                "final": final,
                "before": before,
                "after": target.hp,
            }
        if ability.mitigation:
            event["mitigation"] = ability.mitigation
        self.action_log.append(event)
        return event

    def run_round_one_script(self) -> Dict[str, object]:
        ez = next(h for h in self.heroes if h.id == "ez")
        candy = next(h for h in self.heroes if h.id == "candy_peace")
        dr = next(h for h in self.heroes if h.id == "dr_feed")
        swarm = next(e for e in self.enemies if e.id == "servo_swarm")
        suppressor = next(e for e in self.enemies if e.id == "suppressor")
        warden = next(e for e in self.enemies if e.id == "vault_warden")
        self.use_ability(swarm, ABILITIES["skitter_strike"], candy)
        self.use_ability(ez, ABILITIES["pattern_anchor"], None)
        self.use_ability(suppressor, ABILITIES["suppressive_burst"], ez)
        self.use_ability(dr, ABILITIES["field_surgery"], ez)
        self.use_ability(candy, ABILITIES["guard_line"], None)
        self.use_ability(warden, ABILITIES["relic_maul"], ez)
        return self.payload()

    def payload(self) -> Dict[str, object]:
        return {
            "schema": "blackstar-raiders.tactical-encounter-payload.v0.52",
            "id": self.id,
            "size": self.size,
            "terrain_seed": self.terrain_seed,
            "objective": {
                "cell": self.objective_cell,
                "progress": self.objective_progress,
                "required": self.objective_required,
                "complete": self.objective_progress >= self.objective_required,
            },
            "extraction_cell": self.extraction_cell,
            "heroes": [unit_payload(u) for u in self.heroes],
            "enemies": [unit_payload(u) for u in self.enemies],
            "action_log": self.action_log,
            "player_facing_rule": "screen numbers must come from this payload, not generated visuals",
        }


def unit_payload(u: Unit) -> Dict[str, object]:
    return {
        "id": u.id,
        "name": u.name,
        "faction": u.faction,
        "role": u.role,
        "hp": u.hp,
        "max_hp": u.stats.max_hp,
        "armor": u.stats.armor,
        "move": u.stats.move,
        "initiative": u.stats.initiative,
        "focus": u.focus,
        "max_focus": u.stats.max_focus,
        "pos": u.pos,
        "equipment": u.equipment.name if u.equipment else None,
        "abilities": [a.name for a in u.abilities],
        "visual_identity": u.visual_identity,
    }


def generate_tactical_encounter(event: StrategicEvent) -> TacticalEncounter:
    heroes = make_heroes()
    enemies = make_enemy_pack()
    start_positions = {
        "ez": (2, 2),
        "candy_peace": (3, 3),
        "dr_feed": (2, 3),
        "vault_warden": (7, 6),
        "suppressor": (8, 5),
        "servo_swarm": (6, 7),
        "scanner_acolyte": (9, 6),
    }
    for unit in heroes + enemies:
        unit.pos = start_positions[unit.id]
    return TacticalEncounter(
        id=f"tactical_{event.id}",
        size=event.tactical_size or (12, 12),
        terrain_seed=event.terrain_seed or "generic_ruin",
        objective_cell=(6, 6),
        extraction_cell=(1, 1),
        heroes=heroes,
        enemies=enemies,
    )


def run_demo() -> Dict[str, object]:
    sector = StrategicSector(seed=52052)
    scout = sector.scout((9, 16), radius=4)
    move = sector.move_party((9, 16))
    # Use a known battle event for tactical demo. Strategic movement to it may take several turns.
    event = sector.events["bastion"]
    encounter = generate_tactical_encounter(event)
    tactical_payload = encounter.run_round_one_script()
    return {
        "schema": "blackstar-raiders.full-demo.v0.52",
        "project": "Blackstar Raiders",
        "strategic_payload": sector.visible_payload(),
        "scout_result": scout,
        "move_result": move,
        "tactical_payload": tactical_payload,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_demo(), ensure_ascii=False, indent=2))
