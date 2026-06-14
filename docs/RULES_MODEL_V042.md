# Rules Model v0.42

Status: implemented foundation.

## Purpose

v0.42 replaces hand-tuned demo stats with a calculated rules spine. The goal is
not final balance. The goal is that every hero card, combat screen, AI action,
loadout, and progression change can point back to formulas and logs.

Source:

```text
engine/rules_v042.py
engine/campaign_v042.py
```

## Attribute Budget

Every hero archetype uses the same 30-point attribute budget:

```text
force
agility
endurance
will
tech
presence
```

This keeps hero cards comparable. A hero can be strange, but not free.

## Derived Stats

Core formulas:

```text
max_hp       = 18 + endurance*4 + force
armor        = 1 + floor(endurance/3) + loadout mods
movement     = 3 + floor(agility/2), capped 1..8
initiative   = agility + floor(will/2)
accuracy     = will + floor(agility/2) + loadout mods
resolve      = will + presence + loadout mods
supply_slots = 2 + floor(tech/3) + floor(endurance/4)
```

The campaign UI should display derived stats, but the source of truth is the
formula plus the hero attributes and loadout mods.

## Player Directives

Players do not micromanage every turn. They tune behavior weights:

```text
mobility
objective
greed
survival
ability
consumable
quest
```

The hero AI uses these weights to choose movement emphasis, main actions, bonus
actions, and reaction reserve.

## Action Budget

Each tactical round gives a hero:

```text
movement from derived movement
1 main action
1 bonus action
0/1 reaction reserve, based on survival directive
```

Every chosen action stores score components, so the screen can explain why the
AI hero acted that way.

## Loadout Budget

Loadout is constrained by:

- hero `supply_slots`;
- camp resources;
- role priorities;
- directive fit.

The camp loses resources before the drop. The run earns resources after
extraction. This makes the camp loop mechanical instead of decorative.

## AI Roles

| Role | Responsibility |
|---|---|
| AI Director | threat clocks, noise, doom, extraction timer |
| AI GM | consequence prompts and post-fight options |
| AI Heroes | action scoring from directives and stats |
| AI Enemies | target pressure and objective denial |
| Engine | deterministic resolution and screen payloads |

## Patch Intake

v0.42 includes a patch contract for future ChatGPT Web / Notion / GitHub work.
Allowed patch targets are narrow: directives, demo assignments, loadout priority,
action score weights, screen copy, research questions, visual prompts.

Heavy images or videos should not be committed directly. Store them in Google
Drive or a local artifact folder and reference them from a manifest.

## Checks

```powershell
& '<bundled-python>' .\tests\test_rules_v042.py
& '<bundled-python>' .\tests\test_campaign_v042.py
```
