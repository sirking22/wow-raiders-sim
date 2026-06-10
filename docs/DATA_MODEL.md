# Модель данных (из реального прогона MVP-0.4)

Поток: `intents → engine.simulate(seed, state, intents) → full-log + final-state + snapshot → render_prompt_seed`.

## 1. intents[] (слой агента/GM — вход)
```json
{ "activation": 1, "round": 1, "actor": "EZ", "intent": "hex_blast", "target": "SG", "reason": "Control and focus damage." }
```

## 2. activation (TurnLog — одна запись лога)
```json
{
  "activation": 2, "round": 1, "actor": "EL", "start": "C2", "end": "E4",
  "intent": { "intent": "intercept_EZ_threat", "target": "WG", "reason": "..." },
  "events": [ { "event": "bloodied", "actor": "WG", "cell": "F5" } ],
  "move": { "valid": true, "start": "C2", "end": "E4", "path": ["C2","D3","E4"], "cost": 2 },
  "action": {
    "ability": "greatsword+smite", "target": "WG",
    "roll": { "d20": 18, "bonus": 6, "total": 24, "vs_ac": 16, "result": "hit" },
    "damage": { "parts": [ { "expr": "2d6+4", "rolls": [1,6], "fixed": 4, "type": "slashing", "amount": 11 } ], "total": 22, "hp_before": 34, "hp_after": 12 }
  },
  "resources_after": { "spell1": 2, "lay": 20, "protection_reaction": 1, "action": 0, "bonus_action": 1, "reaction": 1, "movement": 4 }
}
```

## 3. snapshot / final-state (выход)
```json
{
  "snapshot_id": "snap_enc_005_v04_final", "seed": "enc_005_v04_reactions",
  "winner": "heroes", "round": 12, "activation_count": 83,
  "initiative_order": ["EZ","EL","SG","WG","XB","HE","RS"],
  "initiative_rolls": [ { "actor": "EZ", "d20": 19, "dex_mod": 2, "total": 21 } ],
  "board": ["8 | .. .. ...", "...", "     A  B  C  D  E  F  G  H"],
  "actors": { "EZ": { "name": "EZ", "team": "heroes", "class": "Warlock", "position": "A1", "hp": 0, "max_hp": 32, "ac": 15, "statuses": ["bloodied","downed"], "resources": { } } },
  "intent_log": [ ], "gm_log": [ ], "log": [ ],
  "render_prompt_seed": "Render final board exactly from coordinates..."
}
```
(`snapshot` = `final-state` без поля `log`.)

## Доска 8×8
- Колонки A–H, ряды 1–8. Клетка = `"E4"`.
- Дистанция — чебышёвская (king-move), путь с `cost`, бюджет movement по клеткам.
- Террейн: cover (cv), blocked (##), unstable_rune (Ru), collapse_risk (Cr), oil (Oi).

## RNG / детерминизм
Сид = строка вида `"{seed}:R{round}:A{activation}:{actor}:{ability}:{target}"` → SHA-256 → `random.Random`. Любой бросок воспроизводим.
