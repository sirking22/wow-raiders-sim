# Battle Adapter v0.43

Status: implemented contract, not runtime replacement.

## Purpose

v0.43 connects the calculated v0.42 campaign layer to the legacy v0.8 hex battle
engine without rewriting or breaking v0.8.

It answers:

```text
Can v0.42 heroes, stats, directives, and actions be mapped into the old
BattleV08 contract?
```

The answer is now explicit:

- some actor roles map well;
- some actions map partially;
- several important systems are missing from v0.8 runtime;
- the gap is machine-readable and test-covered.

## Files

```text
engine/battle_adapter_v043.py
tests/test_battle_adapter_v043.py
game-data/battle-adapters/campaign01_v043_battle_adapter_report.json
game-data/screen-payloads/campaign01_v043_battle_adapter_screen.json
```

## Mapping

Hero mapping:

| v0.42 player | v0.42 role | v0.8 actor | Fit |
|---|---|---|---|
| EZ | control | EZ | strong |
| Candy Peace | tank | EL | strong |
| Dr.Feed | medic | HE | weak |

The weak `Dr.Feed` mapping is intentional. v0.8 has no native medic/support
slot, so the adapter must not pretend the runtime is already complete.

Enemy mapping:

| v0.42 enemy | v0.8 actor | Fit |
|---|---|---|
| blight_sergeant | SG | partial |
| rust_gunner | XB | partial |
| relic_thrall_pack | WG | partial |

## Action Support

The adapter classifies every v0.42 action as:

- `partial`: has a rough v0.8 analogue but loses rules;
- `missing`: no real v0.8 equivalent.

Examples:

- `prism_lock` -> partial: closest to `eldritch_blast` / hex-style control.
- `guard_line` -> partial: closest to `protective_guard`.
- `stabilize_ally` -> partial: closest to `lay_on_hands`, but Dr.Feed is not
  native.
- `scan_relic_signal`, `field_injector`, `secure_exit_lane` -> missing.

## Adapter Screen

v0.43 produces a renderable screen payload:

```text
stage = battle_adapter_review
```

This screen is for review and planning. It should show source campaign,
target battle engine, actor mapping, action mapping, and loss report.

## Next Runtime Work

The next technical step is not more documentation. It is a new runtime layer:

```text
BattleV09 external roster runtime
```

Minimum requirements:

1. Accept external heroes from `rules_v042.py`.
2. Preserve hex grid invariants from `battle_v08.py`.
3. Preserve deterministic seed behavior.
4. Add native medic/support actor behavior for `Dr.Feed`.
5. Carry objective, extraction, noise, and quest clocks into combat.
6. Keep v0.8 golden tests unchanged.

## Checks

```powershell
& '<bundled-python>' .\tests\test_battle_adapter_v043.py
```
