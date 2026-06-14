# War Raiders v0.54 Reference Game Analysis Matrix

Status: reference and production method.
Scope: extract reusable mechanics, pacing logic, screen contracts, and production
patterns from existing games without copying code, assets, lore, UI, names, or
proprietary data.

## Boundary

Existing games are useful as references, not as source material.

Allowed:

- decompose loops, currencies, failure states, progression, pacing, UI states;
- compare risk/reward structures and balance knobs;
- create original War Raiders rules that test the same player emotion;
- use official SDKs, mod APIs, or workshop routes only after a license check.

Blocked unless separately approved and legally verified:

- extracting commercial game assets or code;
- reverse engineering a downloaded Steam game as a production base;
- using another game's IP, names, setting, UI frame, or proprietary data;
- commercial distribution of fan or mod content without rights.

## Extraction Protocol

For every reference, capture:

1. Player fantasy: what pressure or promise the game creates.
2. Core loop: prepare, enter, decide, resolve, recover, repeat.
3. State model: resources, clocks, statuses, injuries, morale, map state.
4. Failure model: what is lost, what persists, what remains interesting.
5. UI contract: which decisions must be visible before the player acts.
6. War Raiders mapping: which module receives the pattern.
7. First artifact: the cheapest test in Python runtime, screen payload, or paper loop.

## Priority Stack

### 1. Campaign Pressure And Between-Run Survival

| Reference | Extractable pattern | War Raiders module | First test artifact | Risk |
|---|---|---|---|---|
| Against the Storm | Roguelite settlement cycle, monarch/storm pressure, map modifiers, meta resources | AI Director, camp economy, sector modifiers | Add a global pressure clock plus run modifiers to v0.52/v0.55 data | Avoid turning War Raiders into a city builder |
| XCOM 2 | Strategy layer feeds tactical readiness; global doom clock; soldier injury downtime | campaign clock, roster availability, mission choice | Add 3 mission options with different threat/reward/injury implications | Doom clock must create choice, not background noise |
| Darkest Dungeon | Stress, afflictions, quirks, camp recovery, expedition attrition | hero trauma, camp triage, post-run consequences | Add stress/injury/quirk fields to hero continuity ledger | Too much punishment can make players avoid risk |
| Battle Brothers | Mercenary company economy, contracts, gear scarcity, permanent injuries, world traversal | artel/camp economy, contracts, gear loss | Add contract generator with pay, danger, travel, supply cost | Can become spreadsheet-heavy without clear UI |
| Wartales | Open-world party survival, food/wages/fatigue, professions, bounties | 32x32 sector traversal, camp specialists, logistics | Add supplies, fatigue, and camp role checks to strategic movement | Logistics must support adventure, not slow it down |

### 2. Tactical Readability And Decision Quality

| Reference | Extractable pattern | War Raiders module | First test artifact | Risk |
|---|---|---|---|---|
| Into the Breach | Telegraphed enemy intent, compact tactical puzzle, civilian/objective protection | tactical screen payloads, enemy intent layer | Add visible enemy intents to battle payloads before action resolution | Too much perfect info can remove raid chaos |
| Gloomhaven | Card/action economy, initiative tension, exhaustion, scenario packs | optional card/tabletop branch, ability budget | Prototype a 6-card hero kit for Dr.Feed and one striker | Card logic must not replace the main runtime unless chosen |
| XCOM 2 | Cover, flanking, overwatch, hit chances, squad loadout | tactical combat, equipment, actor actions | Add explicit cover/flank tags and expected damage previews | Randomness needs transparent math |

### 3. Extraction And Co-op Adrenaline

| Reference | Extractable pattern | War Raiders module | First test artifact | Risk |
|---|---|---|---|---|
| Deep Rock Galactic | Mission objective variety, class utilities, extraction call, swarm pressure | extraction phase, class utilities, mission objectives | Add extraction phase with countdown, enemy wave budget, carry limits | Must preserve squad roles, not become only horde survival |
| Escape from Tarkov | Loot fear, extract-or-lose carried value, route risk, partial success | relic carry, extraction failure, high-risk variants | Add carried loot vs banked loot split to run outcome | PvP assumptions must not dominate early PvE prototype |
| Hunt: Showdown | Shared objective pressure, bounty extraction, sound/risk tension | contested relics, rival squads, event pressure | Add rival squad threat without requiring real-time shooter logic | Needs careful abstraction for turn-based runtime |
| Dark and Darker | Dungeon extraction, class party roles, loot death stakes | dungeon/raid branch, loadout risk | Add danger tier and partial escape states | IP and tone must stay original-safe |

### 4. Emergent Story And AI GM

| Reference | Extractable pattern | War Raiders module | First test artifact | Risk |
|---|---|---|---|---|
| RimWorld | Storyteller pacing, scars, moods, procedural incident memory | AI GM log, continuity ledger, event pacing | Add incident tags and after-action narrative generated from logs | Narrative must be derived from state, not invented |
| Wildermyth | Character arcs, legacy, transformed heroes, procedural memory | hero legacy, camp history, personal events | Add 1 personal event per campaign based on previous injury/choice | Keep it concise for early testing |
| Dwarf Fortress | World simulation and surprising causal chains | long-term canon/events, settlement history | Add event genealogy IDs for cause/effect tracing | Too deep for now; use only as long-term inspiration |

### 5. Run Variety And Build Synergy

| Reference | Extractable pattern | War Raiders module | First test artifact | Risk |
|---|---|---|---|---|
| Slay the Spire | Relic/build synergy, node event choices, run-defining modifiers | relic system, run modifiers, card branch | Add 10 relic modifiers with explicit formulas and tags | Current canon is open-world sector, not route-line map |
| Against the Storm | Biome/cornerstone/order combinations alter each run | sector conditions, AI Director, rewards | Add sector tags that alter objectives, enemies, and rewards | Modifiers must be readable before deployment |
| Monster Hunter | Preparation, monster knowledge, part rewards, gear crafting | boss hunts, prep kits, targeted loot | Add boss material reward table tied to tactical objectives | Avoid long grind before core loop works |

## Current War Raiders Recommendation

Use the reference stack as layers, not as a mashup:

1. Macro campaign: Against the Storm plus XCOM 2.
2. Expedition/camp attrition: Darkest Dungeon plus Battle Brothers.
3. Tactical clarity: Into the Breach plus XCOM 2.
4. Extraction adrenaline: Deep Rock Galactic plus Tarkov/Hunt as risk models.
5. Narrative continuity: RimWorld plus Wildermyth.
6. Card/tabletop branch: Gloomhaven plus Slay the Spire.

The active runtime should stay deterministic-first:

```text
reference pattern
  -> original War Raiders rule
  -> runtime variable
  -> generated state/log
  -> screen payload
  -> balance test
  -> visual/pitch artifact
```

## v0.55 Candidate Tasks

1. Reference mining worksheet:
   Create `game-data/reference-analysis/reference_patterns_v055.json` with a
   normalized schema for game, pattern, emotion, variable, target module, and
   test artifact.

2. AI Director pressure spike:
   Add a pressure model with `calm`, `threat`, `peak`, and `recovery` phases.
   Sources: Against the Storm, XCOM 2, Left 4 Dead, Deep Rock Galactic.

3. Hero trauma and recovery:
   Add stress, wound severity, quirk, and camp treatment rules to the continuity
   ledger. Sources: Darkest Dungeon, Battle Brothers, Wartales.

4. Extraction economy:
   Split `carried`, `banked`, `lost`, and `rescued` rewards. Sources: Deep Rock
   Galactic, Tarkov, Hunt, Dark and Darker.

5. Tactical screen readability:
   Add enemy intent, expected damage, cover/flank tags, and objective state to
   each battle screen payload. Sources: Into the Breach, XCOM 2, Gloomhaven.

6. Friend task packet:
   Give each collaborator one bounded module: Godot shell, browser replay,
   balance harness, visual board, or reference mining. No one gets the whole game.

## Source Index

Primary/local:

- Notion: War Raiders Game OS
  https://app.notion.com/p/7a3820000c0f46d88411d154aa3bf4c1
- Notion: Blackstar Raiders Actual v0.52 Runtime Snapshot
  https://app.notion.com/p/70d28ec868484dc1a0180ba34e225334
- Local runtime: `blackstar-raiders/`
- Engine acceleration plan: `docs/ENGINE_ACCELERATION_STRATEGY_V053.md`

External official/reference sources:

- Against the Storm on Steam:
  https://store.steampowered.com/app/1336490/Against_the_Storm/
- Darkest Dungeon official:
  https://www.darkestdungeon.com/darkest-dungeon/
- XCOM 2 official:
  https://xcom.com/news/breathing-more-layers-and-life-into-xcom-2-war-of-the-chosen/
- Battle Brothers features:
  https://battlebrothersgame.com/features/
- Battle Brothers strategic worldmap:
  https://battlebrothersgame.com/strategic-worldmap/
- Wartales on Steam:
  https://store.steampowered.com/app/1527950/Wartales/
- Gloomhaven on Steam:
  https://store.steampowered.com/app/780290/Gloomhaven/
- Into the Breach official:
  https://subsetgames.com/itb.html
- Deep Rock Galactic official:
  https://www.deeprockgalactic.com/
- Steam Subscriber Agreement:
  https://store.steampowered.com/subscriber_agreement/

## Acceptance

- A reader can see which reference supports which War Raiders module.
- No source is treated as a license to copy assets, code, IP, UI, or data.
- Every useful pattern points to a cheap v0.55 test artifact.
- The matrix supports both main game and card/tabletop branches without merging
  their mechanics prematurely.
