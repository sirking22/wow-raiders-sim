# Engine Acceleration Strategy v0.53

Status: decision packet, not final engine lock.

## Why This Exists

War Raiders / Blackstar Raiders now has two useful code lines:

- `blackstar-raiders/` v0.52 on GitHub main: compact current game runtime with
  32x32 strategic sector, fog/scouting, event points, heroes, equipment,
  abilities, 12x12 tactical encounter generation, action log and tests.
- v0.44 branch work: screen/render contracts, full campaign chain, AI layers,
  continuity, patch intake and generated payloads.

The next acceleration question is not "write more Python forever". It is:

```text
Which existing engine should host the playable/visual shell while Python/runtime
data remains the source of truth?
```

## Hard Boundary: Steam Games Are Not Our Engine

Downloaded Steam games are useful as references. They are not safe foundations
for our own game unless the developer explicitly provides a modding SDK, editor,
license, and distribution rules.

Against the Storm can be studied for:

- settlement pressure;
- dangerous expedition pacing;
- event-driven map tension;
- resource tradeoffs;
- UI density and readable production chains.

But it should not be used as a runtime base, asset source, code source, or
commercial prototype base without explicit official modding/legal permission.

Default rule:

```text
Study mechanics and UX patterns. Do not extract assets, reverse engineer code,
or build on a proprietary game executable.
```

## Engine Options

### Option A: Keep Python Runtime + Web/Canvas Frontend

Best for the next 1-2 weeks.

Use:

- Python for deterministic game state, AI turns, battle/campaign simulation;
- JSON payloads for screens;
- browser UI for hex map, logs, hero sheets and replay.

Pros:

- fastest path from current repo;
- easiest for Codex/GitHub/Notion patches;
- strong replay/debug tooling;
- friends can contribute data, maps, UI, balance and art separately.

Cons:

- not a "real game feel" until frontend work starts;
- animation/input needs separate build.

Decision:

```text
Primary short-term route.
```

### Option B: Godot

Best for a small team and a real playable prototype.

Use:

- Godot for hex-map interaction, UI, animation, exported playable builds;
- JSON imports from `blackstar-raiders/` runtime;
- later move selected logic into GDScript only after rules stabilize.

Pros:

- open-source MIT license;
- lightweight;
- good for 2D/3D hybrid, hex grids and UI-heavy prototypes;
- easier for friends than Unreal.

Cons:

- tactical RPG tooling still needs custom work;
- less off-the-shelf high-end rendering than Unreal.

Decision:

```text
Best candidate for first real playable shell.
```

### Option C: Unreal

Best for high-end grimdark visuals later.

Use:

- visual prototype, cinematic battle screens, environment mood;
- not the first gameplay implementation.

Pros:

- strong visuals;
- marketplace assets;
- good if the project becomes a 3D presentation/demo.

Cons:

- heavier team/process cost;
- overkill before mechanics are stable;
- licensing/royalty must be tracked.

Decision:

```text
Do not start here unless the next milestone is a visual pitch, not playable
systems.
```

### Option D: Unity

Viable, but not the default.

Use only if someone on the team is already fast in Unity.

Pros:

- large asset ecosystem;
- many tactical/hex/grid packages;
- broad developer familiarity.

Cons:

- licensing/history is more operationally annoying than Godot;
- easy to overbuild before our rules stabilize.

Decision:

```text
Secondary candidate if a friend can implement faster in Unity than Godot.
```

### Option E: Existing Mod Platforms

Possible but separate from the commercial/original game route.

Candidates:

- Warcraft III custom maps: strong genre heritage, but wrong visual target and
  IP/platform constraints.
- WoW addon/private prototype: useful for UI fantasy and research, risky as a
  real game foundation.
- Tabletop Simulator: useful for quick card/board playtests, not for the main
  digital runtime.

Decision:

```text
Use only as experiments or playtest shells. Do not make them the source of
truth.
```

## Recommended Architecture

```text
Runtime Core
  blackstar-raiders/blackstar_game_v052.py
  tests
  JSON payloads

Screen Contract Layer
  v0.44 render contracts
  stage definitions
  replay index

Playable Shell
  short term: browser/canvas
  first engine candidate: Godot

Visual Assets
  Notion / Google Drive
  repo only stores manifests and small curated specs

Project OS
  Notion = canon/tasks/decisions/review
  GitHub = runtime/code/tests/payloads
```

## Friend Work Split

Give friends narrow, checkable tasks. Do not ask them to "make the game".

### Friend A: Godot Spike

Goal:
Render a 32x32 hex sector from JSON with fog states and a movable party token.

Input:

- `blackstar-raiders/blackstar_game_v052.py`
- a generated JSON payload from the runtime.

Acceptance:

- loads JSON;
- draws 32x32 hex map;
- shows unknown / visible / scanned / discovered;
- party token moves between adjacent legal tiles;
- no gameplay formulas invented inside Godot.

### Friend B: Web Replay Spike

Goal:
Render one v0.44/v0.52 run as a replayable browser screen sequence.

Acceptance:

- screen list;
- previous/next controls;
- displays state panels and action log;
- reads JSON only;
- no invented stats.

### Friend C: Balance Harness

Goal:
Run 20-100 deterministic seeds and summarize success rate, injuries, objective
speed, enemy pressure and camp growth.

Acceptance:

- CSV/JSON summary;
- flags over-easy / over-lethal runs;
- names top 3 formulas to tune.

### Friend D: Visual Direction

Goal:
Create a style board for one screen type, not the whole game.

Acceptance:

- linked to a specific screen/stage;
- references stored in Drive/Notion;
- includes UI hierarchy and asset list;
- does not invent gameplay facts.

### Friend E: Content / Events

Goal:
Draft 20 strategic event points for the 32x32 sector.

Acceptance:

- each event has type, risk, reward, trigger, possible combat handoff;
- compatible with existing `EventKind`;
- no new system required unless explicitly flagged.

## Next Technical Step

Build v0.53 bridge outputs:

1. Export a v0.52 strategic sector JSON payload.
2. Export a v0.52 tactical encounter JSON payload.
3. Add a thin `runtime_export_v053.py` or method in the compact runtime.
4. Add tests that exported payloads contain only runtime facts.
5. Use those payloads for browser/Godot spikes.

## Sources / Evidence

- Notion: `War Raiders · Game OS`, fetched 2026-06-14.
- Notion: `Blackstar Raiders · Actual v0.52 Runtime Snapshot`, fetched
  2026-06-14.
- GitHub remote: `origin/main:blackstar-raiders/`.
- Official Godot license page: https://godotengine.org/license/
- Official Unreal Engine EULA: https://www.unrealengine.com/en-US/eula/unreal
- Official Unity legal terms: https://unity.com/legal
- Steam Subscriber Agreement: https://store.steampowered.com/subscriber_agreement/
