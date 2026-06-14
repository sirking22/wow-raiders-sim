# Blackstar Raiders · Current Context v0.52

Status: working project context for Notion, GitHub, Codex and future agents.

Notion hub: https://app.notion.com/p/37ecf67d88c6810c91aac7a157069324

## 0. Why this file exists

This file is the compact human-readable source of truth for the current game direction. It should let Notion, Codex and any future agent understand the latest state without replaying the whole chat.

The project started as `wow-raiders-sim`, but the current active branch of design is **Blackstar Raiders**: a dark gothic sci-fi tactical RPG / strategy prototype.

## 1. Current project identity

**Blackstar Raiders** is not just a visual skin. It is a deterministic-first tactical RPG / strategy game concept.

Current player fantasy:

- The player controls a neutral expedition / salvage crew, not a pure army of heroes.
- The crew is an interspecies / mixed-background group of scavengers, relic hunters, guides, technicians and combat specialists.
- Working name: **Артель добытчиков «Чёрная Звезда»**.
- Tone: grimdark, planetary ruin, industrial gothic, exploration, relic extraction, moral ambiguity.
- We can repeat the genre logic of dark gothic space fantasy, but we must avoid official protected names, logos, factions and symbols.

## 2. Storage model

Notion is the human project hub.

GitHub is the source of truth for:

- current context;
- rules;
- JSON payloads;
- deterministic runtime;
- tests;
- versioned decisions.

Drive / Notion uploads are used for heavy visual references and raw images.

Do not treat image generations as truth. A visual is accepted only when it matches the locked data and reference canon.

## 3. Current version map

### v0.48 · Modular RPG Combat Core

Purpose: split combat mechanics from setting. The game should support a modular setting pack rather than hardcoded visual lore.

Core ideas:

- attributes: force, agility, endurance, will, tech, presence;
- derived stats are calculated, not invented visually;
- equipment changes stats and unlocks actions;
- focus is a real combat resource;
- actions produce logs and formula breakdowns;
- visual render must not define gameplay facts.

### v0.49 · Entity Bible + Payloads

Purpose: lock heroes, enemies, gear, abilities and player-facing payloads.

Locked heroes:

- **EZ** — Призма-псайкер / control.
- **Candy Peace** — Часовенный Бездны / tank.
- **Dr.Feed** — Чумной хирург / medic.

Core enemy roles:

- Vault Warden / Хранитель реликвария;
- Suppressor Gunner / Подавитель;
- Servo-Swarm / Рой сервопауков;
- Scanner Acolyte / Сканирующий адепт.

Important rule: technical IDs may exist in JSON, but player UI should use human-readable Russian names.

### v0.50 · Battle Screen Pre-render

Purpose: validate the tactical battle screen before final image generation.

Current tactical rule:

- default tactical battle size: **12×12 hex**;
- 8×8 is only a small test arena;
- heroes and enemies must be positioned from payload;
- UI numbers come from run result;
- victory screen numbers come from data, never from image generation.

Important visual rule:

- battle units must be proportional to hexes;
- battlefield hero models must match the hero page canon;
- victory screen hero visuals must match the hero page canon.

### v0.51 · Strategic Sector Map

Earlier v0.51 introduced a 32×32 map but still had route lines. This is now corrected.

The strategic layer is **not** a linear route board.

Correct direction:

- **32×32 open-world hex sector**;
- terrain cells;
- fog of war;
- event points;
- neutral units;
- enemy patrols;
- resource sites;
- exploration radius;
- scouting;
- intel data improving understanding of surrounding tiles, events and units.

Wrong direction:

- no hero route lines;
- no board-game path lines;
- no fixed “three-lane road” as the main UI;
- no fantasy map that ignores data states.

### v0.52 · Strategic Open World + Fog Runtime

Current active next build.

Goal: make the strategic map behave like a real explorable sector.

Required systems:

- party token on a 32×32 hex map;
- visibility radius around the party;
- tile states: unknown / visible / scanned / discovered;
- scout action;
- terrain movement cost;
- detected events;
- detected enemy patrols;
- neutral squads;
- resource sites;
- risk roll when entering unsafe areas;
- tactical 12×12 encounter generated from a specific strategic location.

## 4. Current visual reference lock

The current strongest references are kept in Notion / local working files and should be uploaded to the Notion project hub.

Reference roles:

- Hero page = canon for EZ, Candy Peace and Dr.Feed appearance.
- Strategic fog map = direction for the 32×32 open-world map with fog, terrain and units.
- Battle screen = direction for tactical UI, but must obey payload and unit scale.
- Victory screen = direction for final result UI, but hero visuals and result numbers must be corrected from canon/data.

Hard visual rules:

- The hero visuals must stay consistent across hero page, battle screen and victory screen.
- The strategic map must show fog of war and exploration, not route lines.
- Any generated image may be used as reference, but cannot override game state.
- Data first: state → action log → payload → pre-render → final visual.

## 5. Current design decisions

1. Strategic map is **32×32 hex**.
2. Normal tactical battle is **12×12 hex**.
3. 8×8 remains only for small tests.
4. The party are explorers / scavengers / neutral raiders, not a clean heroic army.
5. The map should contain terrain, events, units, resources and fog.
6. Exploration gives better information about nearby areas.
7. Intel should reveal risk, rewards, enemy type and event nature.
8. Battle should start from locations, patrol contact or failed risk checks.
9. The final UI must be cinematic, but all numbers must be validated by data.
10. GitHub stores logic. Notion stores human context and references.

## 6. Immediate v0.52 tasks

- Remove strategic route-line thinking from the map model.
- Create a true open-sector map payload.
- Add party visibility radius.
- Add fog/scouting tile states.
- Add event point model.
- Add enemy patrol model.
- Add neutral / salvage faction units.
- Add terrain movement cost.
- Simulate one strategic turn.
- Generate one updated map payload after scout/move.
- Generate one tactical 12×12 encounter from a discovered point.

## 7. Agent handoff rule

Any agent continuing this project must obey this order:

1. Read this file.
2. Read the structured JSON context file.
3. Update the runtime / data first.
4. Run or update invariant tests.
5. Only then generate final visuals.

Do not make a pretty image and then retrofit the game logic to it.
