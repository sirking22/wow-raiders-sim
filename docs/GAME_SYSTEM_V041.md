# Game System v0.41

Status: foundation draft plus executable demo-run.

## Purpose

v0.41 turns WoW Raiders / Blackstar Raiders from isolated tactical and visual
experiments into a full campaign loop that can be replayed, patched, visualized,
and continued from GitHub, ChatGPT web, Notion, or local Codex.

This is not the final balance model. It is the first calculated backbone:

```text
hero selection -> squad lock-in -> campaign briefing -> loadout -> drop-in ->
route choices -> tactical encounter -> post-battle decision -> extraction ->
run summary -> hero/camp progression -> camp return
```

## Design Rule

Every screen must come from computed state. A generated image may be beautiful,
but it is only valid when it can point back to:

- a run log entry;
- a screen payload;
- hero/camp state;
- a tactical or strategic frame;
- a render contract.

## Setting Modes

The visual target may be a grimdark far-future planetary raid setting. For
production-safe artifacts, use original names and symbols. If an experiment is
explicitly made as an unofficial fan/reference prototype, mark it as such and
do not mix it into commercial/public assets.

Current reference direction:

```text
hard WH40 latest-edition grimdark planetary raid mood
```

Current original-safe codename:

```text
Blackstar Raiders
```

## Core Loop

1. Pick or assign heroes.
2. Set player directives for each hero.
3. Prepare camp loadout and supplies.
4. Drop into a hostile zone.
5. Traverse the campaign map.
6. Fight tactical encounters.
7. Make post-battle decisions.
8. Extract or fail.
9. Apply hero progression.
10. Apply camp/base progression.
11. Record persistent campaign events.
12. Generate summary screens and next hooks.

## Agents In The Simulation

| Agent | Job | Output |
|---|---|---|
| AI Director | Controls pacing, threat clocks, mission pressure, event timing | director log, threat changes |
| AI GM | Explains consequences and offers player-facing decisions | GM prompts, post-battle options |
| AI Heroes | Converts player directives into tactical priorities | hero actions, character drift |
| AI Enemies | Chooses target pressure and objective denial | enemy actions, threat events |
| Engine | Resolves numbers deterministically | state, log, screens, progression |

## Player Influence

Players do not need to micromanage every turn. They can episodically change
hero directives between runs or major screens:

- mobility focus;
- objective focus;
- greed / loot risk;
- survival focus;
- ability usage;
- consumable usage;
- quest curiosity;
- character tone.

The engine then converts those directives into behavior weights.

## Screen Contract

Every screen payload must include:

```text
screen_id
stage
title
time_index
state
ui_panels
log_refs
render_contract
next_decisions
```

The visual renderer must not invent stats or outcomes outside this payload.

## Persistent Objects

The long-term game is built from these objects:

- `squad`: named players and assigned heroes;
- `hero`: class, stats, traits, injuries, XP, directives;
- `camp`: tier, facilities, resources, morale, heat;
- `campaign`: mission seed, acts, encounters, rewards, scars;
- `run`: one completed campaign execution;
- `timeline`: replayable ordered events;
- `screen_payloads`: renderable UI states;
- `patch`: versioned change from GitHub/Web/Notion.

## v0.41 Deliverable

Executable demo:

```bash
python engine/campaign_v041.py
```

Expected generated files:

```text
game-data/agent-directives/campaign01_v041_player_directives.json
game-data/campaign-runs/campaign01_v041_full_run.json
game-data/screen-payloads/campaign01_v041_screen_payloads.json
game-data/camp/camp_state_after_campaign01_v041.json
```

Test:

```bash
python tests/test_campaign_v041.py
```

## Next v0.42 Candidates

1. Replace the simple tactical resolver with a bridge to `battle_v08.py`.
2. Add route-map replay frames using `strategic_v07.py`.
3. Add schema validation for screen payloads.
4. Add a patch intake format for ChatGPT web / Notion suggestions.
5. Add Google Drive manifest references for heavy rendered assets.
