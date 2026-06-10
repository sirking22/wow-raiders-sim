"""WoW Raiders - Strategic Map turn engine (v0.7).

Deterministic, turn-computed strategic layer on a Heroes-style hex region.
Source of truth = strategic state / log / frames; visuals render from snapshots
only. Mirrors the tactical battle engine contract:
  - seeded RNG (session + turn)
  - one log entry per turn (1:1 with turn count)
  - one snapshot frame per turn, plus an initial frame (len == turns + 1)
  - final result + render-contract
  - acceptance validator (no invented hexes / actors, all hexes in bounds)

The strategic layer does NOT resolve battles itself. When the squad meets an
enemy it emits an `encounter_triggered` event that hands off to the tactical
hex battle engine via a battle_seed (e.g. enc_005_v07).
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hexgrid as hx

WIDTH, HEIGHT = 8, 6
SIGHT = 2
SQUAD_MOVE = 6  # movement points per turn

# enter cost per terrain; None = impassable
TERRAIN_COST = {"plains": 2, "road": 1, "forest": 3, "hazard": 4, "mountain": None}


def build_region():
    """Region 'Сумеречные руины' as an 8x6 odd-r hex map."""
    terrain = {}
    for row in range(HEIGHT):
        for col in range(WIDTH):
            terrain[(col, row)] = "plains"
    for h in [(1, 5), (1, 4), (2, 3), (3, 2), (3, 1), (3, 0)]:
        terrain[h] = "road"
    for h in [(0, 3), (2, 4), (4, 3), (5, 2), (2, 2), (5, 4)]:
        terrain[h] = "forest"
    for h in [(6, 0), (7, 1), (0, 0), (7, 4)]:
        terrain[h] = "mountain"
    for h in [(4, 1), (2, 1)]:
        terrain[h] = "hazard"
    return terrain


REGION = {
    "id": "twilight_ruins_region_v0",
    "name": "Сумеречные руины (региональная карта)",
    "start": (1, 5),
    "objective": {"hex": (3, 0), "id": "ruined_obelisk_court", "name": "Алтарь сумерек"},
    "pois": {
        (5, 4): {"id": "poi_cache", "name": "Тайник разведчиков", "type": "resource"},
        (4, 2): {"id": "poi_shrine", "name": "Разрушенный алтарик", "type": "lore"},
    },
    "enemies": {
        (3, 2): {"id": "patrol_twilight", "name": "Сумеречный дозор", "battle_seed": "enc_005_v07"},
    },
    # number of strategic turns the enemy ritual needs to complete
    "ritual_required_turns": 7,
}


def _serialize_hex(h):
    """JSON-safe label for a hex: 'c{col}r{row}'."""
    return "c%dr%d" % (h[0], h[1])


class StrategicMap:
    def __init__(self, seed="twilight_ruins_001", region=None):
        self.seed = seed
        self.region = region or REGION
        self.terrain = build_region()
        self.turn = 0
        self.squad = {
            "id": "squad_raiders",
            "hex": self.region["start"],
            "move_points": SQUAD_MOVE,
            "members": ["EZ", "EL", "HE"],
            "condition": "intact",
        }
        self.objective = dict(self.region["objective"])
        self.pois = {k: dict(v, claimed=False) for k, v in self.region["pois"].items()}
        self.enemies = {k: dict(v, alive=True, engaged=False) for k, v in self.region["enemies"].items()}
        self.ritual = {"progress": 0, "required": self.region["ritual_required_turns"], "complete": False}
        self.revealed = set()
        self.state = "in_progress"
        self.log = []
        self.frames = []
        self._reveal(self.squad["hex"])
        self.frames.append(self.snapshot())  # initial frame 0

    # ---- helpers ----
    def _enter_cost(self, h):
        return TERRAIN_COST[self.terrain[h]]

    def _reveal(self, center):
        newly = []
        for h in hx.hexes_in_range(center, SIGHT):
            if hx.in_bounds(h, WIDTH, HEIGHT) and h not in self.revealed:
                self.revealed.add(h)
                newly.append(h)
        return sorted(newly)

    def _threat_level(self):
        base = self.ritual["progress"] / max(1, self.ritual["required"])
        engaged = sum(1 for e in self.enemies.values() if e["engaged"] and e["alive"])
        score = round(base * 4 + engaged, 2)
        if self.ritual["complete"]:
            return {"score": score, "band": "critical"}
        if score >= 3:
            return {"score": score, "band": "high"}
        if score >= 1.5:
            return {"score": score, "band": "elevated"}
        return {"score": score, "band": "low"}

    def snapshot(self):
        return {
            "turn": self.turn,
            "squad_hex": _serialize_hex(self.squad["hex"]),
            "squad_condition": self.squad["condition"],
            "objective_hex": _serialize_hex(self.objective["hex"]),
            "objective_reached": self.squad["hex"] == self.objective["hex"],
            "ritual": dict(self.ritual),
            "threat": self._threat_level(),
            "revealed_count": len(self.revealed),
            "enemies": {
                e["id"]: {"hex": _serialize_hex(h), "alive": e["alive"], "engaged": e["engaged"]}
                for h, e in self.enemies.items()
            },
            "pois": {p["id"]: {"hex": _serialize_hex(h), "claimed": p["claimed"]} for h, p in self.pois.items()},
            "state": self.state,
        }

    # ---- turn resolution ----
    def resolve_turn(self, intent):
        self.turn += 1
        rng = random.Random("%s:%d" % (self.seed, self.turn))  # noqa: F841 (reserved for stochastic events)
        entry = {"turn": self.turn, "intent": intent, "events": [], "move": {}}

        target = self._intent_target(intent)
        path, _cost = hx.shortest_path(self.squad["hex"], target, WIDTH, HEIGHT, self._enter_cost)
        moved = [self.squad["hex"]]
        spent = 0
        if path:
            for nxt in path[1:]:
                c = self._enter_cost(nxt)
                if spent + c > self.squad["move_points"]:
                    break
                spent += c
                moved.append(nxt)
        self.squad["hex"] = moved[-1]
        entry["move"] = {
            "from": _serialize_hex(moved[0]),
            "path": [_serialize_hex(h) for h in moved],
            "cost": spent,
            "target": _serialize_hex(target),
            "reached_target": moved[-1] == target,
        }

        entry["revealed"] = [_serialize_hex(h) for h in self._reveal(moved[-1])]

        # encounter check: standing on, or adjacent to, a live enemy
        for ehex, e in self.enemies.items():
            if e["alive"] and (moved[-1] == ehex or hx.distance(moved[-1], ehex) == 1):
                if not e["engaged"]:
                    e["engaged"] = True
                    entry["events"].append({
                        "type": "encounter_triggered",
                        "enemy": e["id"],
                        "at": _serialize_hex(ehex),
                        "battle_seed": e["battle_seed"],
                        "note": "hand off to tactical hex battle engine",
                    })
                    self.squad["condition"] = "battle_pending"

        # POI claim
        for phex, p in self.pois.items():
            if moved[-1] == phex and not p["claimed"]:
                p["claimed"] = True
                entry["events"].append({"type": "poi_claimed", "poi": p["id"], "poi_type": p["type"]})

        # ritual timer advances every turn until disrupted/complete
        if not self.ritual["complete"]:
            self.ritual["progress"] += 1
            if self.ritual["progress"] >= self.ritual["required"]:
                self.ritual["complete"] = True
                entry["events"].append({"type": "ritual_complete", "note": "enemies completed the twilight ritual"})

        # objective resolution
        if moved[-1] == self.objective["hex"]:
            if not self.ritual["complete"]:
                entry["events"].append({"type": "objective_reached", "note": "squad may attempt to disrupt the ritual"})
                self.state = "objective_reached_in_time"
            else:
                entry["events"].append({"type": "objective_reached_too_late", "note": "ritual already complete"})
                self.state = "objective_reached_too_late"
        elif self.ritual["complete"] and self.state == "in_progress":
            self.state = "ritual_won_by_enemies"

        entry["threat"] = self._threat_level()
        self.log.append(entry)
        self.frames.append(self.snapshot())
        return entry

    def _intent_target(self, intent):
        action = intent.get("action", "advance_objective")
        if action == "move_to":
            return tuple(intent["target"])
        if action == "claim_poi":
            for phex, p in self.pois.items():
                if p["id"] == intent.get("poi"):
                    return phex
        return self.objective["hex"]  # advance_objective default

    def terminal(self):
        return self.state in ("objective_reached_in_time", "objective_reached_too_late", "ritual_won_by_enemies")

    def run(self, intents, max_turns=12):
        i = 0
        while not self.terminal() and self.turn < max_turns:
            intent = intents[i] if i < len(intents) else {"action": "advance_objective"}
            self.resolve_turn(intent)
            i += 1
        return self.log


# ---- canonical scenario + artifact generation ----
CANON_INTENTS = [
    {"action": "advance_objective"},
    {"action": "advance_objective"},
    {"action": "advance_objective"},
    {"action": "advance_objective"},
    {"action": "advance_objective"},
]


def _post_battle_options(sm):
    opts = []
    if any(e["engaged"] and e["alive"] for e in sm.enemies.values()):
        opts.append({"id": "resolve_encounter", "label": "Разрешить бой с дозором (тактический гекс-движок)"})
    if sm.state == "objective_reached_in_time":
        opts.append({"id": "disrupt_ritual", "label": "Прервать ритуал у алтаря"})
    if sm.ritual["complete"]:
        opts.append({"id": "retreat", "label": "Отступить и перегруппироваться"})
        opts.append({"id": "counter_ritual", "label": "Контр-ритуал / зачистка двора"})
    if not opts:
        opts.append({"id": "advance", "label": "Продолжить продвижение"})
    return opts


def validate(sm):
    errors = []
    if len(sm.log) != sm.turn:
        errors.append("log length %d != turns %d" % (len(sm.log), sm.turn))
    if len(sm.frames) != sm.turn + 1:
        errors.append("frames %d != turns+1 %d" % (len(sm.frames), sm.turn + 1))
    known_ids = {"squad_raiders"} | {e["id"] for e in sm.enemies.values()} | {p["id"] for p in sm.pois.values()}
    for entry in sm.log:
        # every path hex must be in bounds and each step a real neighbour
        path = entry["move"]["path"]
        coords = []
        for label in path:
            col = int(label.split("r")[0][1:])
            row = int(label.split("r")[1])
            if not hx.in_bounds((col, row), WIDTH, HEIGHT):
                errors.append("turn %d hex %s out of bounds" % (entry["turn"], label))
            coords.append((col, row))
        for a, b in zip(coords, coords[1:]):
            if b not in hx.neighbors(a):
                errors.append("turn %d non-adjacent step %s->%s" % (entry["turn"], a, b))
        for ev in entry["events"]:
            ref = ev.get("enemy") or ev.get("poi")
            if ref and ref not in known_ids:
                errors.append("turn %d invented actor %s" % (entry["turn"], ref))
    return errors


def build_strategic(seed="twilight_ruins_001"):
    sm = StrategicMap(seed=seed)
    sm.run(CANON_INTENTS)
    errors = validate(sm)

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game-data", "strategic")
    os.makedirs(out, exist_ok=True)

    log_doc = {
        "schema": "wow-raiders/strategic-log@0.7",
        "region": {"id": REGION["id"], "name": REGION["name"], "width": WIDTH, "height": HEIGHT},
        "seed": seed,
        "turns": sm.turn,
        "final_state": sm.state,
        "log": sm.log,
    }
    result_doc = {
        "schema": "wow-raiders/strategic-result@0.7",
        "seed": seed,
        "turns": sm.turn,
        "final_state": sm.state,
        "squad_final_hex": _serialize_hex(sm.squad["hex"]),
        "squad_condition": sm.squad["condition"],
        "ritual": sm.ritual,
        "threat": sm._threat_level(),
        "objective": {"id": sm.objective["id"], "name": sm.objective["name"], "hex": _serialize_hex(sm.objective["hex"]), "reached": sm.squad["hex"] == sm.objective["hex"]},
        "encounters": [
            {"enemy": e["id"], "engaged": e["engaged"], "battle_seed": e["battle_seed"]}
            for e in sm.enemies.values()
        ],
        "pois": [{"id": p["id"], "claimed": p["claimed"]} for p in sm.pois.values()],
        "post_battle_options": _post_battle_options(sm),
        "gm_questions": [
            "Прорываемся к алтарю с боем или ищем обход?",
            "Принимаем бой с дозором сейчас или отступаем перегруппироваться?",
        ],
        "validation_errors": errors,
    }
    frames_doc = {
        "schema": "wow-raiders/strategic-frames@0.7",
        "seed": seed,
        "frame_count": len(sm.frames),
        "frames": sm.frames,
    }
    render_contract = {
        "schema": "wow-raiders/render-contract@0.7",
        "screen": "strategic_map",
        "grid": {"type": "hex", "layout": "odd-r", "width": WIDTH, "height": HEIGHT},
        "source_of_truth": "strategic-frames + strategic-log; visual must render a specific turn frame",
        "must_show": [
            "squad token at squad_hex",
            "objective marker at objective_hex",
            "revealed hexes vs fog of war",
            "engaged enemies",
            "threat band",
            "ritual progress N/required",
        ],
        "must_not_invent": [
            "hexes outside %dx%d bounds" % (WIDTH, HEIGHT),
            "actors not present in the frame",
            "squad position not equal to frame squad_hex",
        ],
        "answers": [
            "где мы (squad_hex)",
            "что произошло (log events этого хода)",
            "кто в каком состоянии (squad_condition, enemies)",
            "какие риски выросли (threat band, ritual progress)",
            "что делать дальше (post_battle_options / gm_questions)",
        ],
    }

    json.dump(log_doc, open(os.path.join(out, "strat-twilight-001-log.json"), "w"), ensure_ascii=False, indent=2)
    json.dump(result_doc, open(os.path.join(out, "strat-twilight-001-result.json"), "w"), ensure_ascii=False, indent=2)
    json.dump(frames_doc, open(os.path.join(out, "strat-twilight-001-frames.json"), "w"), ensure_ascii=False, indent=2)
    json.dump(render_contract, open(os.path.join(out, "strat-twilight-001-render-contract.json"), "w"), ensure_ascii=False, indent=2)
    return sm, result_doc


def main():
    sm, result = build_strategic()
    summary = {
        "turns": result["turns"],
        "final_state": result["final_state"],
        "squad_final_hex": result["squad_final_hex"],
        "squad_condition": result["squad_condition"],
        "ritual": result["ritual"],
        "threat": result["threat"],
        "objective_reached": result["objective"]["reached"],
        "encounters": result["encounters"],
        "frames_len": len(sm.frames),
        "log_len": len(sm.log),
        "validation_errors": result["validation_errors"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
