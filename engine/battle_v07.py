"""WoW Raiders — боевой движок v0.7 (поверх v0.6): objective «interrupt ritual».

Новое по сравнению с v0.6:
  * RS (Rune Speaker) канализирует ритуал (часовой механизм / alarm clock).
    Если ритуал набирает `required` чистых каналов — враги побеждают (ritual_complete),
    даже если герои живы.
  * Герои «прерывают» ритуал четырьмя рычагами (без бафа hero-AI):
      - убить RS → клок останавливается (RS не жив — не каналит);
      - ранить RS до <50% HP → канал срывается этот ход (ritual_disrupted_bloodied);
      - ранить других врагов (<55% HP) → RS лечит вместо канала (клок стоит);
      - поджечь RS (`burning`) → канал срывается этот ход.
  * snapshot теперь отдаёт чистые счётчики death_saves `{success, fail}` (резолв тех-долга §16.1)
    и `victory_type` (interrupt_elimination / ritual_complete / wipe / unfinished).

Детерминизм по seed сохранён. v0.4 golden не трогаем — v0.7 имеет свою канон-фикстуру.
"""
from battle_v06 import BattleV06


class BattleV07(BattleV06):
    VERSION = "v0.7-objective-ritual"

    def __init__(self, seed="enc_005_v07", ritual_required=5):
        super().__init__(seed)
        self.ritual = {"progress": 0, "required": ritual_required, "complete": False,
                       "channeler": "RS", "disrupted": 0}
        self.events_summary.setdefault("ritual_channels", 0)
        self.events_summary.setdefault("ritual_disrupts", 0)

    def _rs_should_heal(self):
        rs = self.actors.get("RS")
        if not rs or not rs.alive:
            return False
        wounded = [e for e in self.living("enemies")
                   if e.id != "RS" and e.hp < e.max_hp * 0.55]
        return bool(wounded) and rs.resources.get("spell1", 0) > 0

    def resolve(self, aid):
        if aid == "RS":
            rs = self.actors["RS"]
            if rs.alive and "burning" not in rs.statuses and not self.ritual["complete"] and not self._rs_should_heal():
                # сохраняем поведение v0.6: сброс меток при смене раунда
                if self.round != self._last_round:
                    self._clear_marks()
                    self._last_round = self.round
                self.activation += 1
                self.reset_turn(rs)
                bloodied = rs.hp < rs.max_hp * 0.5
                intent = {"intent": "channel_ritual", "target": "self",
                          "reason": "Rune Speaker channels the ritual — heroes must interrupt."}
                self.intent_log.append({"activation": self.activation, "round": self.round, "actor": "RS", **intent})
                ev = {"activation": self.activation, "round": self.round, "actor": "RS", "start": rs.pos,
                      "intent": intent, "events": []}
                if bloodied:
                    self.ritual["disrupted"] += 1
                    self.events_summary["ritual_disrupts"] += 1
                    ev["action"] = {"ability": "channel_ritual", "result": "disrupted_bloodied",
                                    "ritual_progress": self.ritual["progress"], "required": self.ritual["required"]}
                    ev["events"].append({"event": "ritual_disrupted_bloodied", "actor": "RS", "cell": rs.pos,
                                         "effect": "RS ранен — канал ритуала сорван этот ход."})
                else:
                    self.ritual["progress"] += 1
                    self.events_summary["ritual_channels"] += 1
                    ev["action"] = {"ability": "channel_ritual", "result": "channel",
                                    "ritual_progress": self.ritual["progress"], "required": self.ritual["required"]}
                    if self.ritual["progress"] >= self.ritual["required"]:
                        self.ritual["complete"] = True
                        ev["events"].append({"event": "ritual_complete", "actor": "RS", "cell": rs.pos,
                                             "effect": "Ритуал завершён — враги побеждают."})
                    else:
                        ev["events"].append({"event": "ritual_channel", "actor": "RS",
                                             "progress": self.ritual["progress"], "required": self.ritual["required"],
                                             "effect": "Часовой механизм ритуала продвинулся."})
                ev["end"] = rs.pos
                ev["resources_after"] = dict(rs.resources)
                self.log.append(ev)
                return
        super().resolve(aid)

    def run_until_end(self, max_activations=120):
        i = 0
        while self.living("heroes") and self.living("enemies") and not self.ritual["complete"] and i < max_activations:
            aid = self.initiative[i % len(self.initiative)]
            if i > 0 and i % len(self.initiative) == 0:
                self.round += 1
            self.resolve(aid)
            i += 1
        return self.snapshot()

    def snapshot(self):
        snap = super().snapshot()
        snap["snapshot_id"] = "snap_" + self.seed
        snap["engine_version"] = self.VERSION
        snap["ritual"] = dict(self.ritual)
        heroes_alive = bool(self.living("heroes"))
        enemies_alive = bool(self.living("enemies"))
        if self.ritual["complete"]:
            snap["winner"] = "enemies"; snap["victory_type"] = "ritual_complete"
        elif heroes_alive and not enemies_alive:
            snap["winner"] = "heroes"; snap["victory_type"] = "interrupt_elimination"
        elif enemies_alive and not heroes_alive:
            snap["winner"] = "enemies"; snap["victory_type"] = "wipe"
        else:
            snap["winner"] = "unfinished"; snap["victory_type"] = None
        for aid, a in self.actors.items():
            snap["actors"][aid]["death_saves"] = {
                "success": a.statuses.count("death_save_success"),
                "fail": a.statuses.count("death_save_fail"),
            }
        return snap


def main():
    import json
    snap = BattleV07().run_until_end()
    print(json.dumps({k: snap[k] for k in ["winner", "victory_type", "ritual", "round",
                                            "activation_count", "mechanics_summary", "board"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
