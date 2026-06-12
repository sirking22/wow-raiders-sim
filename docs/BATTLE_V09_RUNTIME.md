# BattleV09 External Roster Runtime

Status: implemented tactical runtime checkpoint.

## Purpose

BattleV09 is the first tactical battle layer that consumes the v0.42 calculated
campaign roster directly.

It exists because v0.43 proved that the old `battle_v08.py` contract cannot
honestly represent the current party:

- `EZ` can map to control gameplay;
- `Candy Peace` can map to tank gameplay;
- `Dr.Feed` needs native medic/support behavior, not a weak legacy substitute.

v0.9 keeps the old v0.8 golden simulator intact and adds a new deterministic
runtime beside it.

## Files

```text
engine/battle_v09.py
tests/test_battle_v09.py
game-data/battle-runs/campaign01_v09_external_battle_run.json
game-data/screen-payloads/campaign01_v09_external_battle_screen_payloads.json
```

## Source Of Truth

BattleV09 reads:

```text
engine/rules_v042.py
engine/campaign_v042.py
```

The battle uses:

- v0.42 player slots: `EZ`, `Candy Peace`, `Dr.Feed`;
- v0.42 hero assignments;
- v0.42 derived stats, loadout, directives, and scored actions;
- v0.42 campaign clocks at tactical encounter start.

## Implemented Runtime Behavior

- Hex board: 8x8 odd-r layout.
- Movement: path cost must fit each actor's movement budget and derived
  movement stat.
- Actions: each hero resolves one main action and one bonus action.
- AI scoring: hero choices call `rules_v042.choose_action`.
- Clocks: battle carries `noise`, `threat`, `doom`, and `extraction_timer`.
- Objective: reliquary objective progress is calculated from action effects and
  position.
- Extraction: readiness is calculated from progress, surviving heroes, noise,
  and doom.
- Screens: every battle screen payload is derived from frames/action logs.

## Dr.Feed

`Dr.Feed` is the canonical player nickname.

In BattleV09:

- player id: `Dr.Feed`;
- hero: `Plague Surgeon`;
- role: `medic`;
- native support actions:
  - `stabilize_ally`;
  - `field_injector`.

Acceptance tests require `Dr.Feed` to perform real support actions and produce
at least one heal effect that improves ally HP.

## Setting Direction

Reference direction is hard latest-edition grimdark far-future planetary raid
mood.

Public repo artifacts remain original-safe under `Blackstar Raiders`. Do not
add official WH40 logos, faction names, or protected public asset names unless a
future file is explicitly marked as private fan/reference work.

## Generated Result

Current generated run:

```text
success: true
victory_type: extract_ready
rounds: 3
objective_progress: 12
heroes_alive: EZ, Candy Peace, Dr.Feed
extraction_readiness: 100
validation_errors: []
```

Hostiles can remain alive. The current win condition is extraction readiness,
not enemy annihilation.

## Checks

```powershell
& '<bundled-python>' .\tests\test_battle_v09.py
```

Full suite should still include the legacy v0.8 tests so this runtime does not
silently break preserved golden behavior.
