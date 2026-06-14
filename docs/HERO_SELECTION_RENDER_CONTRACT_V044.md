# Hero Selection Render Contract v0.44

Status: draft contract for data-grounded visualization
Owner layer: v0.44 screen payload / pre-render pipeline
Target screen: `blackstar_campaign_001_run_001_v044_screen_00_hero_selection`

## 0. Why this exists

This document prevents the visual layer from drifting away from the simulation.

The hero-selection screen may look cinematic, gothic, and grimdark, but every visible player name, hero name, role, stat number, slot state, and warning must come from a known source.

The correct pipeline is:

```text
campaign input
-> runtime state
-> logs/calculations
-> screen payload
-> render contract
-> pre-render structure
-> final visual artifact
```

The final image is not the source of truth. It is only a presentation of the source of truth.

## 1. Source files

Primary source:

```text
game-data/screen-payloads/campaign01_v044_screen_payloads.json
```

Primary screen:

```text
screens[0]
stage: hero_selection
title: Hero Selection
time_index: 0
```

Relevant sibling source for mission facts:

```text
screens[2]
stage: campaign_briefing
mission.id: blightfall_relic_extraction
mission.name: Blightfall Relic Extraction
mission.planet: Korvash Prime
mission.extraction_window: 30
mission.threat_band: extreme
```

Important gap: `screens[0].state` has a `mission_sidebar` UI panel, but it does not currently embed the mission object. Therefore the hero-selection render may either:

1. show only facts present in `screens[0].state`, or
2. show mission facts only if the pre-render layer explicitly resolves a `mission_ref` to `screens[2].state.mission`, or to a future shared mission packet.

It must not invent mission facts from the image reference alone.

## 2. Locked screen identity

```json
{
  "screen_id": "blackstar_campaign_001_run_001_v044_screen_00_hero_selection",
  "stage": "hero_selection",
  "title": "Hero Selection",
  "time_index": 0,
  "run_id": "blackstar_campaign_001_run_001_v044"
}
```

## 3. Locked player slots

The upper-center reserved slots must show exactly these players and assignment states:

| Slot | Player | Status |
|---:|---|---|
| 1 | EZ | unassigned |
| 2 | Candy Peace | unassigned |
| 3 | Dr.Feed | unassigned |

Derived UI status:

```json
{
  "assigned_count": 0,
  "required_count": 3,
  "label": "0 / 3 assigned"
}
```

Do not render these as selected heroes on screen 00. They are unassigned at this time index.

## 4. Locked hero pool

The bottom hero roster must contain exactly 9 heroes.

Each hero has `attribute_budget: 30`.

| # | ID | Name | Role | Tags | Attributes F/A/E/W/T/P | HP | Armor | Move | Init | Acc | Resolve | Damage | Heal | Obj | Tech | Threat |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | void_chaplain | Void Chaplain | tank | anchor, protector, morale, frontline | 6/3/8/6/2/5 | 56 | 3 | 4 | 6 | 7 | 11 | 9 | 3 | 4 | 2 | 11 |
| 2 | ash_scout | Ash Scout | scout | mobility, stealth, route, quest | 3/8/4/5/5/5 | 37 | 2 | 7 | 10 | 9 | 10 | 5 | 3 | 4 | 5 | 7 |
| 3 | plague_surgeon | Plague Surgeon | medic | healing, toxins, stabilize, consumable | 2/4/5/6/8/5 | 40 | 2 | 5 | 7 | 8 | 11 | 5 | 6 | 6 | 8 | 7 |
| 4 | siege_gunner | Siege Gunner | heavy | suppression, breach, heavy, noise | 7/2/7/4/7/3 | 53 | 3 | 4 | 4 | 5 | 7 | 9 | 4 | 5 | 7 | 10 |
| 5 | sanctioned_prism_psyker | Sanctioned Prism Psyker | control | psyker, control, risk, objective | 2/4/3/10/3/8 | 32 | 2 | 5 | 9 | 12 | 18 | 7 | 4 | 8 | 3 | 11 |
| 6 | iron_tech_adept | Iron Tech-Adept | support | repair, devices, camp, consumable | 4/3/5/5/10/3 | 42 | 2 | 4 | 5 | 6 | 8 | 6 | 6 | 6 | 10 | 7 |
| 7 | deathworld_beastmaster | Deathworld Beastmaster | ranger | tracking, beast, survival, mobility | 5/7/6/5/2/5 | 47 | 3 | 6 | 9 | 8 | 10 | 7 | 2 | 3 | 2 | 9 |
| 8 | penitent_duelist | Penitent Duelist | duelist | melee, bleed, zeal, risk | 7/7/5/6/1/4 | 45 | 2 | 6 | 10 | 9 | 10 | 10 | 2 | 4 | 1 | 12 |
| 9 | xeno_relic_sniper | Xeno Relic Sniper | sniper | range, relics, precision, greed | 3/8/3/6/6/4 | 33 | 2 | 7 | 11 | 10 | 10 | 6 | 5 | 6 | 6 | 8 |

Recommended visible card stats for the first pre-render pass:

```text
HP = derived.max_hp
ARM = derived.armor
MOV = derived.movement
ACC = derived.accuracy
DMG = derived.damage_power
THR = derived.threat
```

If the card cannot fit 6 numeric stats, use this compact set:

```text
HP / ARM / MOV / ACC
```

If the final image uses stat bars, the source number must remain accessible in the pre-render structure and artifact manifest.

## 5. Locked rules preview

The screen may show a compact rules preview, but must not alter formulas.

Relevant formula anchors:

```text
max_hp = 18 + endurance*4 + force
armor = 1 + floor(endurance/3) + loadout mods
movement = 3 + floor(agility/2), capped 1..8
initiative = agility + floor(will/2)
accuracy = will + floor(agility/2) + loadout mods
resolve = will + presence + loadout mods
supply_slots = 2 + floor(tech/3) + floor(endurance/4)
```

Rules summary locks:

```json
{
  "schema": "blackstar-raiders.rules.v0.42",
  "attribute_budget": 30,
  "hero_count": 9,
  "loadout_count": 9,
  "main_action_count": 6,
  "bonus_action_count": 5
}
```

## 6. Locked setting profile

The screen uses the original-safe Blackstar Raiders setting profile:

```json
{
  "production_mode": "blackstar_raiders_original_safe",
  "reference_target": "hard WH40 latest-edition grimdark planetary raid mood",
  "tone": ["brutal", "gothic", "military", "high-risk", "no-soft-fantasy"],
  "public_asset_rule": "use original names and symbols unless explicitly marked as private fan/reference work",
  "canonical_player_nickname": "Dr.Feed",
  "public_name": "Blackstar Raiders"
}
```

Visual direction may be gothic, cathedral-industrial, brutal, militaristic, and grimdark.

Public assets must not use official WH40 logos, protected faction names, or exact official insignia.

## 7. Required UI zones

Screen 00 declares these UI panels:

```json
[
  {"id": "reserved_player_slots"},
  {"id": "hero_pool_grid"},
  {"id": "rules_preview"},
  {"id": "mission_sidebar"}
]
```

Recommended layout based on the supplied reference:

```text
TOP CENTER
- title: HERO SELECTION
- three reserved player slots: EZ, Candy Peace, Dr.Feed
- each slot status: UNASSIGNED

LEFT SIDEBAR
- mission/risk panel
- only show mission facts if resolved from a mission_ref or shared mission state

RIGHT SIDEBAR
- squad status: 0 / 3 assigned
- squad bonuses: no active bonus unless sourced elsewhere
- mission intel only if sourced

BOTTOM GRID
- 9 hero cards
- each card: index, hero name, role, tags/icon hints, compact stats

BOTTOM ACTION BAR
- READY UP disabled/inactive while 0 / 3 assigned
```

## 8. Must show

The render contract says the visual must show:

```json
[
  "hero_pool",
  "player_slots",
  "rules_summary",
  "setting_profile"
]
```

## 9. Must not invent

The screen payload forbids inventing:

```json
[
  "actions absent from battle_run.action_log",
  "stats outside rules_v042 formulas or battle_v09 logs",
  "player names other than EZ, Candy Peace, Dr.Feed",
  "official WH40 logos or protected names in public assets"
]
```

Additional visual-specific bans:

- Do not mark any player slot as selected on screen 00.
- Do not change hero count from 9.
- Do not change `attribute_budget: 30`.
- Do not rename `Dr.Feed` to `Dr Feed`, `Dr. Feed`, or another variant.
- Do not show battle kills, injuries, rewards, or extraction outcome on hero selection.
- Do not show official franchise marks in public/exported assets.
- Do not invent unreadable pseudo-numbers when exact numeric labels are required.

## 10. Pre-render structure target

A first pre-render JSON/SVG prototype should expose this structure:

```json
{
  "screen_id": "blackstar_campaign_001_run_001_v044_screen_00_hero_selection",
  "stage": "hero_selection",
  "layout": {
    "canvas": {"aspect_ratio": "16:9"},
    "zones": [
      {"id": "title_banner", "kind": "title", "locked_text": "HERO SELECTION"},
      {"id": "reserved_player_slots", "kind": "slot_row", "count": 3},
      {"id": "mission_sidebar", "kind": "sidebar", "source_required": true},
      {"id": "squad_status", "kind": "sidebar", "locked_text": "0 / 3 ASSIGNED"},
      {"id": "hero_pool_grid", "kind": "card_grid", "count": 9},
      {"id": "ready_up", "kind": "button", "state": "disabled"}
    ]
  },
  "validation": {
    "hero_count": 9,
    "assigned_count": 0,
    "required_count": 3,
    "player_names": ["EZ", "Candy Peace", "Dr.Feed"]
  }
}
```

## 11. Final visual prompt constraints

The final prompt may use the supplied reference only for composition and art direction.

Prompt must include:

- `Use the pre-render structure as the source of truth.`
- `Preserve exact player names: EZ, Candy Peace, Dr.Feed.`
- `Preserve exact hero count: 9 bottom roster cards.`
- `Preserve slot state: all three slots are UNASSIGNED.`
- `Preserve squad status: 0 / 3 assigned.`
- `Do not invent battle results, kills, injuries, rewards, or selected heroes.`
- `No official WH40 logos, official faction names, or protected insignia in public assets.`

Prompt may include:

- `grimdark gothic sci-fi interface`
- `cathedral-industrial UI frame`
- `brass, blackened steel, red warning lamps, parchment labels, skull-like generic gothic ornaments`
- `distant war-torn planetary skyline`
- `premium game UI mockup`

## 12. Acceptance checklist

A generated hero-selection artifact is accepted only if:

- [ ] title is `HERO SELECTION` or `Hero Selection`;
- [ ] three reserved slots exist;
- [ ] reserved slots are exactly `EZ`, `Candy Peace`, `Dr.Feed`;
- [ ] each reserved slot is `UNASSIGNED`;
- [ ] squad status is `0 / 3 assigned`;
- [ ] bottom roster has exactly 9 cards;
- [ ] roster names match the 9 hero names above;
- [ ] no selected hero appears in a reserved slot;
- [ ] no battle outcome/reward/injury appears;
- [ ] visible stats, if numeric, match the pre-render structure;
- [ ] mission facts are either absent or sourced from an explicit mission reference;
- [ ] no official WH40 logos/protected names/insignia are used in public assets.

## 13. Next implementation packet

Suggested next small task:

```text
Goal:
Create tools/render_hero_selection_structure_v044.py.

Input:
game-data/screen-payloads/campaign01_v044_screen_payloads.json

Output:
out/pre-render/hero_selection_v044_structure.json
out/pre-render/hero_selection_v044_structure.svg

Rules:
- Read only screen_00.
- Do not mutate campaign runtime files.
- Render all 3 player slots.
- Render all 9 hero cards.
- Emit numeric stats from payload.
- Mark mission sidebar as unresolved unless a mission_ref is provided.

Tests:
- hero_count == 9
- assigned_count == 0
- player names match exactly
- all slots are unassigned
- every visible stat comes from payload
```
