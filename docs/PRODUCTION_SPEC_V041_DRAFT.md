# Production Spec v0.41 Draft

Status: implemented foundation checkpoint plus remaining planner questions.

## Goal

Turn the v0.40 handoff into an executable next development plan without
overwriting the existing v0.8/v0.9 simulator line.

The first implemented checkpoint is not a broad engine rewrite. It adds a
campaign orchestrator above the existing tactical/strategic modules:

```text
engine/campaign_v041.py
tests/test_campaign_v041.py
docs/GAME_SYSTEM_V041.md
docs/SCREEN_PIPELINE_V041.md
```

This checkpoint produces a deterministic full-run with hero selection,
directives, camp loadout, route screens, tactical rounds, extraction, summary,
hero progression, and camp return.

The second implemented checkpoint is v0.42:

```text
engine/rules_v042.py
engine/campaign_v042.py
tests/test_rules_v042.py
tests/test_campaign_v042.py
docs/RULES_MODEL_V042.md
```

v0.42 replaces ad hoc demo stats with a calculated rules spine: equal attribute
budget, derived stat formulas, loadout budget, player directives, AI action
scoring, action budgets, camp costs, and progression.

The third implemented checkpoint is v0.43:

```text
engine/battle_adapter_v043.py
tests/test_battle_adapter_v043.py
docs/BATTLE_ADAPTER_V043.md
```

v0.43 creates a read-only adapter contract between the v0.42 calculated
campaign and the legacy `battle_v08.py` hex battle engine. It maps heroes,
enemies, stats, and actions, and records explicit gaps before a future
BattleV09 runtime accepts external rosters.

The fourth implemented checkpoint is BattleV09:

```text
engine/battle_v09.py
tests/test_battle_v09.py
docs/BATTLE_V09_RUNTIME.md
```

BattleV09 is the first tactical runtime that accepts the v0.42 external roster
directly. It preserves v0.8 instead of replacing it, carries campaign clocks
into combat, resolves hex movement, one main action, one bonus action, objective
progress, extraction readiness, and native `Dr.Feed` medic/support behavior.

The fifth implemented checkpoint is v0.44:

```text
engine/campaign_v044.py
tests/test_campaign_v044.py
docs/FULL_CAMPAIGN_RUNTIME_V044.md
```

v0.44 embeds BattleV09 into a full campaign runtime. It outputs a 20-screen
chain from hero selection through route decisions, tactical rounds, AI GM
interlude, extraction, highlights, progression, camp return, and campaign
continuity. It also writes a continuity ledger and a v0.44 patch intake contract
for ChatGPT Web, Notion, GitHub PRs, Google Drive manifests, and local file
packets.

## Recommended Path

Start with Option B from `docs/V040_SYNC_AND_MERGE_PLAN.md`: promote the v0.40
renderer and field standards into the active repo as tools/rules, while keeping
the v0.40 simulator run frozen under `handoffs/`.

Reason:

- lower risk than replacing the engine;
- immediately improves visual/output capability;
- creates testable adapters before deeper engine migration;
- keeps the older golden tests intact.

## Non-Goals

- No broad rewrite of `engine/battle_v08.py`.
- No deletion of v0.40 handoff files.
- No legal/platform claim about Warcraft or private servers.
- No balance rewrite without playtest or deterministic run evidence.

## Proposed File Moves / Additions

Candidate future files:

```text
tools/render_hex_field.py
rules/hex-field-standard-v040.json
tests/test_render_hex_field_v040.py
docs/V041_RENDERER_ADAPTER_NOTES.md
```

Source material:

```text
handoffs/v0.40-codex-handoff-github-ready/engine/render_hex_field_v040.py
handoffs/v0.40-codex-handoff-github-ready/game-data/standards/hex-field-standard-v040.json
handoffs/v0.40-codex-handoff-github-ready/game-data/raid-runs/campaign03_raid01_full_run_v039.json
```

## Acceptance For v0.41 / v0.42 / BattleV09 / v0.44

Implemented foundation acceptance:

1. `tests/test_campaign_v041.py` passes.
2. Campaign run is deterministic for the same seed.
3. Player slots are exact: `EZ`, `Candy Peace`, `Dr.Feed`.
4. The first screen keeps all three player slots unassigned before lock-in.
5. The setting profile records a hard WH40 latest-edition grimdark reference
   direction while keeping public assets original-safe.
6. Generated state exists under `game-data/agent-directives/`,
   `game-data/campaign-runs/`, `game-data/screen-payloads/`, and
   `game-data/camp/`.
7. BattleV09 accepts `EZ`, `Candy Peace`, and `Dr.Feed` from v0.42 without
   weak legacy actor mapping.
8. `Dr.Feed` is the canonical nickname and resolves as a native medic.
9. BattleV09 outputs generated state under `game-data/battle-runs/` and
   `game-data/screen-payloads/`.
10. BattleV09 validation returns zero errors.
11. v0.44 full campaign run embeds BattleV09 instead of using abstract tactical
    rounds.
12. v0.44 screen payloads are replayable from `state`, `log_refs`, and
    `calculation_refs`.
13. v0.44 records AI Director, AI GM, AI Heroes, and AI Enemies turns.
14. v0.44 writes a continuity ledger for between-run hero/camp development.
15. v0.44 includes a balance audit that names concrete next tuning targets
    instead of hiding crooked stats.

Older renderer-promotion acceptance remains relevant for a later renderer checkpoint:

1. Existing tests still pass.
2. v0.40 verifier still passes.
3. Renderer tool can render at least one standard field from active repo path.
4. Test asserts rectangular bounds or output existence.
5. Handoff folder remains frozen.

## Low-Effort Task Packets

### Task 1: Renderer Inventory

```text
Goal:
Summarize render_hex_field_v040.py into inputs, outputs, assumptions, and files it reads/writes.

Files allowed:
handoffs/v0.40-codex-handoff-github-ready/engine/render_hex_field_v040.py
handoffs/v0.40-codex-handoff-github-ready/game-data/standards/hex-field-standard-v040.json

Do not touch:
engine/
tests/
tools/

Acceptance:
- Names CLI arguments.
- Names field types.
- Names output formats.
- Lists adapter risks.

Check command:
No command; review-only inventory.
```

### Task 2: Test Design

```text
Goal:
Draft tests for renderer promotion without writing code.

Files allowed:
docs/PRODUCTION_SPEC_V041_DRAFT.md
handoffs/v0.40-codex-handoff-github-ready/scripts/verify_v040.py

Acceptance:
- 3-5 concrete test cases.
- Each test has input, expected output, and failure signal.
- No broad engine migration.
```

### Task 3: Adapter Notes

```text
Goal:
Compare old snapshot shape with v0.40 run payload shape.

Files allowed:
game-data/snapshots/snap-enc-005-v08-final.json
handoffs/v0.40-codex-handoff-github-ready/game-data/raid-runs/campaign03_raid01_full_run_v039.json

Acceptance:
- Lists shared fields.
- Lists missing/incompatible fields.
- Recommends adapter boundary.
```

## Planner Review Questions

1. Is renderer promotion the correct v0.41 first step?
2. Should v0.40 simulator become a separate future engine line after renderer
   integration?
3. Should visual standards live under `rules/`, `game-data/standards/`, or
   `visual-standards/` in active repo?
