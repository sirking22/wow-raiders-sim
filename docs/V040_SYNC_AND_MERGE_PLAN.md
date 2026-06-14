# v0.40 Sync And Merge Plan

## Current State

Remote `main` currently contains the older simulator line:

- `engine/battle_v04.py` through `engine/battle_v08.py`;
- `engine/hexgrid.py`;
- `schema/`;
- `rules/`;
- `tests/`;
- `tools/`;
- v0.9 after-action planning docs.

The imported v0.40 handoff is preserved here:

```text
handoffs/v0.40-codex-handoff-github-ready/
```

It contains:

- `engine/hex_raid_simulator_v039.py`;
- `engine/render_hex_field_v040.py`;
- `game-data/raid-runs/campaign03_raid01_full_run_v039.json`;
- `game-data/standards/hex-field-standard-v040.json`;
- `visual-standards/png/`;
- `scripts/verify_v040.py`;
- `manifests/release-manifest-v040.json`.

## Decision

Do not overwrite `main` with v0.40. Treat v0.40 as a versioned handoff package
until a merge plan converts its useful parts into the existing repo structure.

## Verification

v0.40 verification:

```bash
cd handoffs/v0.40-codex-handoff-github-ready
python scripts/verify_v040.py
```

Expected:

```json
{"passed": true, "issues": 0}
```

Existing repo tests:

```bash
for t in tests/test_*.py; do python "$t"; done
```

## Merge Options

### Option A: Keep v0.40 As Archive Only

Use when the current v0.8/v0.9 engine remains the active line.

Pros:

- safest;
- preserves historical package;
- avoids mixing incompatible structures.

Cons:

- v0.40 renderer/data are not yet part of the active engine.

### Option B: Promote v0.40 Renderer Into Tools

Move or adapt:

- `engine/render_hex_field_v040.py` -> `tools/render_hex_field.py`;
- `game-data/standards/hex-field-standard-v040.json` -> `rules/hex-field-standard-v040.json`;
- add tests for rectangular bounds and output existence.

Pros:

- useful visual output enters active repo;
- low risk if engine state is untouched.

Cons:

- needs adapter between old snapshots and v0.40 run payloads.

### Option C: Create New v0.41 Engine Line

Use v0.40 as the starting point for a new modular extraction raid simulator:

```text
engine/core/hex.py
engine/core/state.py
engine/core/actions.py
engine/core/simulator.py
engine/content/heroes.py
engine/content/enemies.py
engine/content/encounters.py
```

Pros:

- matches v0.40 handoff intent;
- creates a cleaner future engine.

Cons:

- higher risk;
- requires migration from old tests or clear separation from them.

## Recommended Next Step

Create `Production Spec v0.41` before code migration.

Acceptance for the spec:

- names the active engine line;
- chooses Option A, B, or C;
- lists files to create/change;
- lists tests;
- states what stays frozen under `handoffs/`;
- gives 3-5 low-effort task packets for execution.

