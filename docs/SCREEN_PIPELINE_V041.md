# Screen Pipeline v0.41

## Principle

Screens are generated from state. The order is:

```text
engine state -> log -> screen payload -> render contract -> visual artifact
```

Never reverse this order.

## Campaign Screen Set

| Order | Stage | Purpose |
|---:|---|---|
| 1 | hero_selection | Show empty player slots and hero pool. |
| 2 | squad_lock_in | Show selected heroes for this simulated run. |
| 3 | campaign_briefing | Mission, threat, rewards, extraction window. |
| 4 | camp_loadout | Supplies, budget, gear, directives. |
| 5 | drop_in | Landing state and initial director clocks. |
| 6 | route_map | Strategic route choices and pressure clocks. |
| 7 | tactical_encounter_start | Enemy group, terrain, objectives. |
| 8 | tactical_round | Computed action, bonus action, movement, damage. |
| 9 | post_battle_decision | Loot, injuries, spend/press-on/extract options. |
| 10 | extraction | Extraction status and remaining pressure. |
| 11 | run_summary | Rewards, deaths, MVPs, key moments. |
| 12 | progression | XP, traits, injuries, directive drift. |
| 13 | camp_return | Camp resources, facility changes, persistent hooks. |

## Required Payload Fields

```json
{
  "screen_id": "string",
  "stage": "string",
  "title": "string",
  "time_index": 0,
  "state": {},
  "ui_panels": [],
  "log_refs": [],
  "render_contract": {},
  "next_decisions": []
}
```

## Render Contract

Each screen tells the renderer:

- what to show;
- which state fields are authoritative;
- which labels must be exact;
- what must not be invented.

Large rendered images should be stored outside Git when needed, then referenced
by a manifest with Drive links or local artifact paths.

