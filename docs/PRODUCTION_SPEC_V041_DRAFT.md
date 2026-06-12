# Production Spec v0.41 Draft

Status: draft for planner review.

## Goal

Turn the v0.40 handoff into an executable next development plan without
overwriting the existing v0.8/v0.9 simulator line.

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

## Acceptance For v0.41

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

