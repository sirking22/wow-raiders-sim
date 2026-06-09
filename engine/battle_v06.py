"""WoW Raiders — боевой движок v0.6 (поверх v0.5): контригра врага.

Цель: дать врагам инструменты против хрупкого тыла героев.
  * Координированный фокус (mark): попадание врага по тыловику (EZ/HE) вешает
    метку на раунд; последующие вражеские удары по меченой цели бьют с +2.
  * Зажигательные боеприпасы: XB (crossbow) и RS (ruin_bolt) при попадании
    могут поджечь (`burning`); рядом с oil шанс выше (4/6 против 2/6).

Детерминизм по seed сохранён. Герои не бафатся — меняется только сторона врага.
"""
from battle_v05 import BattleV05
from battle_v04 import d


class BattleV06(BattleV05):
    VERSION = "v0.6-enemy-counterplay"
    INCENDIARY_ABILITIES = {"crossbow", "ruin_bolt"}
    BACKLINE = {"EZ", "HE"}

    def __init__(self, seed="enc_005_v06"):
        super().__init__(seed)
        self._last_round = self.round
        self.events_summary.setdefault("enemy_ignites", 0)
        self.events_summary.setdefault("focus_marks", 0)

    def _clear_marks(self):
        for a in self.actors.values():
            self.remove_status(a, "marked")

    def attack(self, a, target, ability, stat, dmg_exprs, melee=False, adv=False, extra=None):
        # свора добивает меченую цель: +2 к попаданию == временно −2 AC
        focus = a.team == "enemies" and "marked" in target.statuses
        if focus:
            target.ac -= 2
        try:
            action = super().attack(a, target, ability, stat, dmg_exprs, melee=melee, adv=adv, extra=extra)
        finally:
            if focus:
                target.ac += 2
        if isinstance(action, dict) and action.get("roll", {}).get("result") in ("hit", "crit"):
            if focus:
                action["roll"]["focus_fire"] = True
            if a.team == "enemies" and target.team == "heroes":
                if "marked" not in target.statuses:
                    self.add_status(target, "marked")
                    self.events_summary["focus_marks"] += 1
                if ability in self.INCENDIARY_ABILITIES and target.hp > 0 and "burning" not in target.statuses:
                    thresh = 4 if self._near_oil(target.pos) else 2
                    if d(f"{self.seed}:incendiary:{self.activation}:{a.id}->{target.id}", 6) <= thresh:
                        self.add_status(target, "burning")
                        self.events_summary["enemy_ignites"] += 1
                        self.events_summary["ignites"] += 1
                        action.setdefault("reaction_events", []).append(
                            {"event": "incendiary", "actor": a.id, "target": target.id,
                             "cell": target.pos, "effect": "incendiary round — target is burning"})
        return action

    def resolve(self, aid):
        if self.round != self._last_round:
            self._clear_marks()
            self._last_round = self.round
        super().resolve(aid)

    def snapshot(self):
        snap = super().snapshot()
        snap["snapshot_id"] = "snap_" + self.seed
        snap["engine_version"] = self.VERSION
        return snap


def main():
    import json
    sim = BattleV06()
    snap = sim.run_until_end()
    print(json.dumps({k: snap[k] for k in ["winner", "round", "activation_count", "momentum", "mechanics_summary", "board"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
