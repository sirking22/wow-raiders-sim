"""WoW Raiders — боевой движок v0.5 (поверх v0.4).

Новые механики (детерминированные, изолированные seed-пространства):
  * Крит (nat 20): удваивает кости урона.
  * Фланкинг: ближний бой с преимуществом, если рядом с целью есть союзник.
  * Opportunity attack: выход из ближнего без дизенгейджа провоцирует реакцию-удар.
  * Поджог: fire/radiant по цели на/рядом с oil → burning (догорание 1d4/ход, шанс потухнуть).
  * Momentum: командный импульс (0..6); >=3 даёт +1 к попаданию. Растёт от критов/добиваний.

Инвариант: детерминизм по seed сохранён.
"""
from battle_v04 import (
    BattleV04, d, roll_expr, adjacent,
)


class BattleV05(BattleV04):
    VERSION = "v0.5-reactions+"

    MELEE_PROFILE = {
        "EL": ("greatsword_oa", "str", [("2d6+4", "slashing")]),
        "SG": ("maul_oa", "str", [("2d6+4", "bludgeoning")]),
        "WG": ("warglaive_oa", "dex", [("1d10+4", "slashing")]),
        "HE": ("dagger_oa", "dex", [("1d4+4", "piercing")]),
    }

    def __init__(self, seed="enc_005_v05_reactions"):
        super().__init__(seed)
        self.momentum = {"heroes": 0, "enemies": 0}
        self.events_summary = {"crits": 0, "opportunity_attacks": 0, "ignites": 0, "flanks": 0}

    # ---- helpers -------------------------------------------------
    def _flanking(self, a, target):
        return any(self.adjacent(al.pos, target.pos) for al in self.allies_of(a))

    def _oil_cells(self):
        return [c for c, cell in self.cells.items() if cell.hazard == "oil"]

    def _near_oil(self, pos):
        return any(pos == o or self.adjacent(pos, o) for o in self._oil_cells())

    def _bump_momentum(self, team, delta):
        self.momentum[team] = max(0, min(6, self.momentum.get(team, 0) + delta))

    # ---- attack (crit + flank + momentum + ignite) ---------------
    def attack(self, a, target, ability, stat, dmg_exprs, melee=False, adv=False, extra=None):
        if not self.spend(a, {"action": 1}):
            return {"ability": ability, "target": target.id, "error": "no_action"}
        flank = bool(melee and self._flanking(a, target))
        if flank:
            adv = True
            self.events_summary["flanks"] += 1
        seed = f"{self.seed}:R{self.round}:A{self.activation}:{a.id}:{ability}:{target.id}"
        if adv:
            r1 = d(seed + ":a", 20); r2 = d(seed + ":b", 20); r = max(r1, r2)
            roll = {"advantage": [r1, r2], "selected": r}
        else:
            r = d(seed + ":d20", 20); roll = {"d20": r}
        mom = 1 if self.momentum.get(a.team, 0) >= 3 else 0
        bonus = a.mod(stat) + a.prof + mom
        ac = target.ac + self.cover_bonus(target, melee)
        total = r + bonus
        crit = (r == 20)
        hit = r == 20 or (r != 1 and total >= ac)
        hp_before = target.hp
        parts = []; total_dmg = 0
        if hit:
            for expr, dtype in dmg_exprs + (extra or []):
                amount, rolls, fixed = roll_expr(seed + ":" + dtype + ":" + expr, expr)
                parts.append({"expr": expr, "rolls": rolls, "fixed": fixed, "type": dtype, "amount": amount})
                total_dmg += amount
            if crit:
                for expr, dtype in dmg_exprs + (extra or []):
                    amount2, rolls2, bonus2 = roll_expr(seed + ":crit:" + dtype + ":" + expr, expr)
                    dice = amount2 - bonus2
                    parts.append({"expr": expr + "#crit", "rolls": rolls2, "type": dtype, "amount": dice})
                    total_dmg += dice
            dummy_ev = {"events": []}
            reduction = self.protection_reaction(target, a, dummy_ev)
            if reduction:
                parts.append({"type": "protection_reduction", "amount": -min(total_dmg, reduction)})
                total_dmg = max(0, total_dmg - reduction)
            target.hp = max(0, target.hp - total_dmg)
            if hp_before > target.max_hp / 2 and 0 < target.hp <= target.max_hp / 2:
                self.add_status(target, "bloodied")
            fired = any(p["type"] in ("fire", "radiant", "radiant_smite") for p in parts)
            if fired and self._near_oil(target.pos) and "burning" not in target.statuses and target.hp > 0:
                self.add_status(target, "burning")
                dummy_ev["events"].append({"event": "ignite", "actor": a.id, "target": target.id, "cell": target.pos, "effect": "oil ignites — target is burning"})
                self.events_summary["ignites"] += 1
            self.check_down(target)
            if crit:
                self._bump_momentum(a.team, 1)
                self.events_summary["crits"] += 1
            if target.hp == 0:
                self._bump_momentum(a.team, 2)
                self._bump_momentum(target.team, -1)
            action = {"ability": ability, "target": target.id,
                      "roll": {**roll, "bonus": bonus, "total": total, "vs_ac": ac,
                               "result": "crit" if crit else "hit", "momentum_bonus": mom, "flank": flank},
                      "damage": {"parts": parts, "total": total_dmg, "hp_before": hp_before, "hp_after": target.hp}}
            if dummy_ev["events"]:
                action["reaction_events"] = dummy_ev["events"]
            return action
        return {"ability": ability, "target": target.id,
                "roll": {**roll, "bonus": bonus, "total": total, "vs_ac": ac,
                         "result": "fumble" if r == 1 else "miss", "momentum_bonus": mom, "flank": flank},
                "damage": {"parts": parts, "total": 0, "hp_before": hp_before, "hp_after": target.hp}}

    # ---- opportunity attacks on movement -------------------------
    def _opportunity_attack(self, e, target):
        prof = self.MELEE_PROFILE.get(e.id)
        if not prof:
            e.resources["reaction"] = e.resources.get("reaction", 0) + 1  # refund: cannot OA
            return None
        ability, stat, dmg = prof
        self.events_summary["opportunity_attacks"] += 1
        seed = f"{self.seed}:oa:{self.activation}:{e.id}->{target.id}"
        r = d(seed + ":d20", 20)
        bonus = e.mod(stat) + e.prof
        ac = target.ac
        total = r + bonus
        crit = (r == 20)
        hit = r == 20 or (r != 1 and total >= ac)
        hp_before = target.hp; parts = []; tot = 0
        if hit:
            for expr, dtype in dmg:
                amount, rolls, fixed = roll_expr(seed + ":" + expr, expr)
                parts.append({"expr": expr, "rolls": rolls, "type": dtype, "amount": amount}); tot += amount
            if crit:
                amount2, rolls2, bonus2 = roll_expr(seed + ":crit", dmg[0][0])
                parts.append({"expr": dmg[0][0] + "#crit", "rolls": rolls2, "type": dmg[0][1], "amount": amount2 - bonus2})
                tot += amount2 - bonus2
            target.hp = max(0, target.hp - tot)
            self.check_down(target)
            if target.hp == 0:
                self._bump_momentum(e.team, 2); self._bump_momentum(target.team, -1)
        return {"event": "opportunity_attack", "actor": e.id, "target": target.id,
                "roll": {"d20": r, "total": total, "vs_ac": ac, "result": "crit" if crit else ("hit" if hit else "miss")},
                "damage": {"parts": parts, "total": tot, "hp_before": hp_before, "hp_after": target.hp}}

    def move(self, a, dest, max_override=None):
        start = a.pos
        # осторожный отход (retreat/hide/cautious_step) идёт с max_override<=3 = дизенгейдж
        disengaging = max_override is not None and max_override <= 3
        res = super().move(a, dest, max_override)
        if res.get("valid") and not disengaging and a.pos != start:
            oas = []
            for e in self.enemies_of(a):
                if self.adjacent(start, e.pos) and not self.adjacent(a.pos, e.pos) and e.resources.get("reaction", 0) > 0:
                    e.resources["reaction"] -= 1
                    oa = self._opportunity_attack(e, a)
                    if oa:
                        oas.append(oa)
            if oas:
                res["opportunity_attacks"] = oas
        return res

    # ---- burning tick at start of own activation -----------------
    def resolve(self, aid):
        a = self.actors[aid]
        burn_ev = None
        if a.alive and "burning" in a.statuses:
            amount, rolls, _ = roll_expr(f"{self.seed}:burn:{self.activation + 1}:{aid}", "1d4")
            before = a.hp; a.hp = max(0, a.hp - amount)
            burn_ev = {"event": "burning_tick", "actor": aid, "amount": amount, "hp_before": before, "hp_after": a.hp}
            self.check_down(a)
            if d(f"{self.seed}:burnfade:{self.activation + 1}:{aid}", 6) <= 2:
                self.remove_status(a, "burning"); burn_ev["faded"] = True
        super().resolve(aid)
        if burn_ev is not None and self.log:
            self.log[-1].setdefault("events", []).insert(0, burn_ev)

    def snapshot(self):
        snap = super().snapshot()
        snap["snapshot_id"] = "snap_" + self.seed
        snap["engine_version"] = self.VERSION
        snap["momentum"] = self.momentum
        snap["mechanics_summary"] = self.events_summary
        return snap


def main():
    sim = BattleV05()
    snap = sim.run_until_end()
    import json
    print(json.dumps({k: snap[k] for k in ["winner", "round", "activation_count", "momentum", "mechanics_summary", "board"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
