"""WoW Raiders v0.7 — пост-боевой конвейер (assembly point).

Реализует бриф Patch v0.6 поверх движка v0.7 (objective ritual):
  бой → статистика → награды → стратегическая карта → решение сквада.

Ключевые инварианты (acceptance из брифа):
  * len(full_timeline) == activation_count  (лог 1:1, вкл. skip/downed/no-action)
  * len(replay_frames) == activation_count + 1
  * нет пропущенных номеров активаций
  * все акторы из реестра, клетки 8x8, без термина 'кровожадность'

Статы выводятся ИЗ РЕАЛЬНОГО ЛОГА (damage.total / hp_before-after / unit_down),
ничего не выдумывается.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from battle_v07 import BattleV07  # noqa: E402

VALID_CELLS = {f"{c}{r}" for c in "ABCDEFGH" for r in range(1, 9)}


def load_vocab():
    return json.loads((ROOT / "rules" / "status-vocabulary-v07.json").read_text("utf-8"))


def status_ru(statuses, vocab):
    out = []
    for s in statuses:
        node = vocab["statuses"].get(s)
        if node:
            out.append(node["ru"])
    return out


def lite_state(b):
    return {
        "actors": {
            aid: {
                "hp": a.hp, "max_hp": a.max_hp, "pos": a.pos, "team": a.team,
                "alive": a.alive, "statuses": list(a.statuses),
            } for aid, a in b.actors.items()
        },
        "ritual": dict(b.ritual),
        "board": b.board(),
    }


def run_with_frames(seed="enc_005_v07", ritual_required=5, max_activations=120):
    """Повторяет run_until_end, но с захватом кадров и достройкой skip-лога."""
    b = BattleV07(seed=seed, ritual_required=ritual_required)
    n = len(b.initiative)
    frames = [{"frame_index": 0, "activation": 0, "round": b.round,
               "actor": None, "state": lite_state(b)}]
    timeline = []
    i = 0
    while b.living("heroes") and b.living("enemies") and not b.ritual["complete"] and i < max_activations:
        aid = b.initiative[i % n]
        if i > 0 and i % n == 0:
            b.round += 1
        pre_log = len(b.log)
        pre_act = b.activation
        b.resolve(aid)
        new_entries = b.log[pre_log:]
        if b.activation > pre_act and not new_entries:
            # мёртвый актор пропустил ход — достраиваем явную запись (1:1 fix)
            timeline.append({
                "activation": b.activation, "round": b.round, "actor": aid,
                "event_type": "skip_dead_actor", "state_diff": {},
                "summary": f"{aid} повержен и пропускает активацию.",
            })
        else:
            for e in new_entries:
                e2 = dict(e)
                e2.setdefault("event_type", "action")
                timeline.append(e2)
        frames.append({"frame_index": len(frames), "activation": b.activation,
                       "round": b.round, "actor": aid, "state": lite_state(b)})
        i += 1
    snap = b.snapshot()
    return b, snap, frames, timeline


def derive_stats(timeline, snap):
    """Статы из реальных событий лога. Ничего не выдумываем."""
    ids = list(snap["actors"].keys())
    st = {aid: {"damage": 0, "healing": 0, "kills": 0, "damage_taken": 0,
                "final_hp": snap["actors"][aid]["hp"],
                "max_hp": snap["actors"][aid]["max_hp"],
                "team": snap["actors"][aid]["team"]} for aid in ids}
    for e in timeline:
        actor = e.get("actor")
        action = e.get("action") or {}
        dmg = action.get("damage") or {}
        total = dmg.get("total", 0) or 0
        target = action.get("target")
        if total and actor in st:
            st[actor]["damage"] += total
        if total and target in st:
            st[target]["damage_taken"] += total
        # лечение: ищем heal-поля в action и events
        heal = action.get("heal") or action.get("healing") or 0
        if heal and actor in st:
            st[actor]["healing"] += heal
        for ev in e.get("events", []) or []:
            if ev.get("heal") and actor in st:
                st[actor]["healing"] += ev["heal"]
            etype = ev.get("event", "")
            if etype in ("unit_down", "unit_killed", "unit_dead_after_death_saves"):
                # убийство кредитуется актору активации, если жертва — чужая команда
                victim = ev.get("actor")
                if actor in st and victim in st and st[victim]["team"] != st[actor]["team"]:
                    st[actor]["kills"] += 1
    return st


def squad_condition(snap):
    heroes = [a for a in snap["actors"].values() if a["team"] == "heroes"]
    downed = sum(1 for a in heroes if "downed" in a["statuses"] or "dead" in a["statuses"])
    alive = sum(1 for a in heroes if a["hp"] > 0 and "dead" not in a["statuses"])
    if alive == 0:
        return "wiped"
    if downed >= 2:
        return "critical"
    if downed == 1:
        return "strained"
    return "stable"


def battle_rating(snap):
    vt = snap.get("victory_type")
    cond = squad_condition(snap)
    if vt == "interrupt_elimination":
        return {"wiped": "D", "critical": "B-", "strained": "B+", "stable": "A"}[cond]
    if vt == "ritual_complete":
        return "F · ритуал завершён (поражение)"
    if vt == "wipe":
        return "F · отряд уничтожен"
    return "— · бой не завершён"


def milestones(frames):
    last = frames[-1]["frame_index"]
    picks = {}
    for pct in (0, 25, 50, 75, 100):
        idx = round(last * pct / 100)
        f = frames[idx]
        picks[f"{pct}%"] = {"frame_index": f["frame_index"], "activation": f["activation"],
                            "round": f["round"], "board": f["state"]["board"],
                            "ritual": f["state"]["ritual"]}
    return picks


def build_reports(seed="enc_005_v07", ritual_required=5):
    vocab = load_vocab()
    b, snap, frames, timeline = run_with_frames(seed, ritual_required)
    stats = derive_stats(timeline, snap)
    cond = squad_condition(snap)
    rating = battle_rating(snap)

    def card(aid):
        a = snap["actors"][aid]
        s = stats[aid]
        return {"id": aid, "name": a["name"], "team": a["team"], "cell": a["position"],
                "hp": a["hp"], "max_hp": a["max_hp"],
                "status_ru": status_ru(a["statuses"], vocab),
                "alive": a["hp"] > 0 and "dead" not in a["statuses"],
                "damage": s["damage"], "healing": s["healing"],
                "kills": s["kills"], "damage_taken": s["damage_taken"],
                "death_saves": a.get("death_saves", {})}

    heroes = [aid for aid in snap["actors"] if snap["actors"][aid]["team"] == "heroes"]
    enemies = [aid for aid in snap["actors"] if snap["actors"][aid]["team"] == "enemies"]
    mvp = max(heroes, key=lambda a: stats[a]["damage"] + stats[a]["kills"] * 25 + stats[a]["healing"])
    enemies_defeated = [aid for aid in enemies if not (snap["actors"][aid]["hp"] > 0)]

    result = {
        "schema": "battle-result/v0.7", "encounter": "enc-005", "engine_version": snap["engine_version"],
        "seed": seed, "snapshot_id": snap["snapshot_id"],
        "winner": snap["winner"], "victory_type": snap["victory_type"], "rating": rating,
        "rounds": snap["round"], "activations": snap["activation_count"],
        "ritual": snap["ritual"], "threat_delta": 1 if snap["winner"] != "heroes" else 0,
        "squad_condition": cond,
        "hero_cards": [card(a) for a in heroes],
        "enemy_cards": [card(a) for a in enemies],
        "enemies_defeated": enemies_defeated,
        "mvp": mvp,
        "loot": [],
        "loot_note": "Лут не моделируется движком v0.7 — пустой список, не выдумываем.",
        "post_battle_actions": ["stabilize_squad", "short_rest", "loot_carefully",
                                "inspect_rune_speaker", "retreat_to_shelter"],
    }

    stats_doc = {
        "schema": "battle-stats/v0.7", "encounter": "enc-005", "seed": seed,
        "source": "derived_from_full_log", "mvp": mvp,
        "rows": [{"id": aid, **{k: stats[aid][k] for k in
                  ("team", "damage", "healing", "kills", "damage_taken", "final_hp", "max_hp")}}
                 for aid in snap["actors"]],
        "mechanics_summary": snap.get("mechanics_summary", {}),
    }

    # Ключевые события: всё, где есть events или ощутимый урон/ритуал
    key_events = []
    for e in timeline:
        evs = e.get("events", []) or []
        action = e.get("action") or {}
        dmg = (action.get("damage") or {}).get("total", 0) or 0
        is_ritual = action.get("ability") == "channel_ritual"
        if evs or dmg >= 10 or is_ritual or e.get("event_type") == "skip_dead_actor":
            key_events.append({"activation": e["activation"], "round": e.get("round"),
                               "actor": e.get("actor"), "event_type": e.get("event_type"),
                               "ability": action.get("ability"), "target": action.get("target"),
                               "damage": dmg, "events": evs,
                               "summary": e.get("summary")})

    strategic = {
        "schema": "strategic-state/v0.7", "state_id": "post_battle_enc_005_v07",
        "location_id": "ruined_obelisk_court", "location_ru": "Разрушенный двор Обелиска",
        "from_snapshot": snap["snapshot_id"], "winner": snap["winner"], "victory_type": snap["victory_type"],
        "squad_condition": cond, "threat_level_delta": result["threat_delta"],
        "ritual": snap["ritual"],
        "reinforcement_risk": "high" if snap["winner"] != "heroes" else "medium",
        "rest_need": "high" if cond in ("critical", "wiped") else "medium",
        "answers": {
            "where_are_we": "Разрушенный двор Обелиска",
            "what_happened": f"Бой завершён: {snap['victory_type']} (победитель: {snap['winner']}).",
            "who_in_what_state": {aid: {"hp": f"{snap['actors'][aid]['hp']}/{snap['actors'][aid]['max_hp']}",
                                        "status": status_ru(snap['actors'][aid]['statuses'], vocab)}
                                  for aid in heroes},
            "risks_grown": ["ритуал завершён — враги усилены" ] if snap["victory_type"] == "ritual_complete" else ["угроза подкреплений"],
            "what_to_do_next": result["post_battle_actions"],
        },
        "gm_questions": [
            "Сначала стабилизируем павших или рискуем быстрым лутом?",
            "Расходуем ли ресурс лечения сейчас?",
            "Осматриваем Rune Speaker / следы рун или уходим в укрытие?",
        ],
    }

    render_contracts = {}
    for screen, src in {"battle_result": "battle-result.json", "battle_stats": "battle-stats.json",
                        "battle_log": "battle-log-key-events.json", "battle_replay": "replay-frames.json",
                        "strategic_map": "post-battle-strategic-state.json"}.items():
        render_contracts[screen] = {
            "screen": screen, "data_source": src, "snapshot_id": snap["snapshot_id"],
            "activation_count": snap["activation_count"],
            "must_reference": ["frame_index OR state_id", "activation_count"],
            "must_show": {
                "battle_result": ["winner", "victory_type", "rating", "rounds", "activations", "squad_condition", "hero_cards"],
                "battle_stats": ["damage", "healing", "kills", "damage_taken", "final_hp", "mvp"],
                "battle_log": ["activation", "actor", "events"],
                "battle_replay": ["0/25/50/75/100% board", "initiative", "activation timeline"],
                "strategic_map": ["location", "squad_condition", "threat", "options", "gm_questions"],
            }[screen],
            "must_not_invent": ["actors", "positions", "hp", "outcomes"],
            "forbidden_terms": ["кровожадность", "bloodthirsty"],
        }

    return {
        "snap": snap, "frames": frames, "timeline": timeline,
        "result": result, "stats": stats_doc, "key_events": key_events,
        "strategic": strategic, "render_contracts": render_contracts,
        "milestones": milestones(frames),
    }


def validate(bundle):
    snap = bundle["snap"]; frames = bundle["frames"]; timeline = bundle["timeline"]
    ac = snap["activation_count"]
    errors = []
    if len(timeline) != ac:
        errors.append(f"timeline {len(timeline)} != activation_count {ac}")
    if len(frames) != ac + 1:
        errors.append(f"frames {len(frames)} != activation_count+1 {ac + 1}")
    acts = [e["activation"] for e in timeline]
    if sorted(acts) != list(range(1, ac + 1)):
        errors.append(f"пропуски/дубли активаций: {acts}")
    for aid, a in snap["actors"].items():
        if a["position"] not in VALID_CELLS:
            errors.append(f"клетка {a['position']} вне 8x8 ({aid})")
    blob = json.dumps(bundle["result"], ensure_ascii=False) + json.dumps(bundle["strategic"], ensure_ascii=False)
    for term in ("кровожадн", "bloodthirsty"):
        if term in blob.lower():
            errors.append(f"запрещённый термин: {term}")
    return errors


def main():
    bundle = build_reports()
    errs = validate(bundle)
    out = ROOT / "game-data"
    (out / "battle-reports").mkdir(parents=True, exist_ok=True)
    (out / "replay").mkdir(parents=True, exist_ok=True)
    (out / "strategic").mkdir(parents=True, exist_ok=True)
    (out / "render-contracts").mkdir(parents=True, exist_ok=True)

    def w(p, obj):
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    w(out / "battle-reports" / "enc-005-v07-result.json", bundle["result"])
    w(out / "battle-reports" / "enc-005-v07-stats.json", bundle["stats"])
    w(out / "battle-reports" / "enc-005-v07-key-events.json", bundle["key_events"])
    w(out / "replay" / "enc-005-v07-replay-frames.json", bundle["frames"])
    w(out / "replay" / "enc-005-v07-replay-milestones.json", bundle["milestones"])
    w(out / "battle-reports" / "enc-005-v07-full-timeline.json", bundle["timeline"])
    w(out / "strategic" / "post-battle-state-enc-005-v07.json", bundle["strategic"])
    for screen, c in bundle["render_contracts"].items():
        w(out / "render-contracts" / f"{screen}-screen-v07.json", c)

    snap = bundle["snap"]
    print(json.dumps({
        "engine_version": snap["engine_version"], "winner": snap["winner"],
        "victory_type": snap["victory_type"], "rating": bundle["result"]["rating"],
        "rounds": snap["round"], "activations": snap["activation_count"],
        "timeline_len": len(bundle["timeline"]), "frames_len": len(bundle["frames"]),
        "mvp": bundle["result"]["mvp"], "validation_errors": errs,
    }, ensure_ascii=False, indent=2))
    if errs:
        sys.exit(1)


if __name__ == "__main__":
    main()
