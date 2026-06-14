# Blackstar Raiders · Full Game Package v0.52

This folder is the **current full handoff package** for the Blackstar Raiders branch of `wow-raiders-sim`.

This is the game package, not only a context note. It includes the current runtime prototype contract, map scale, RPG entities, strategic layer rules, tactical layer rules, data manifests and tests.

## Current design direction

- **Strategic map:** 32×32 open-world hex sector.
- **Tactical map:** 12×12 hex by default.
- **8×8:** small test arena only.
- **Strategic UI:** no linear route-lines; use terrain, fog of war, visibility radius, scouting, event points, enemy/neutral units and resources.
- **Player faction:** neutral interspecies salvage/exploration artel — добытчики / исследователи / реликтовые рейдеры.
- **Source of truth:** runtime/data/tests first; visuals are references and outputs, not facts.

## Included in this repo package

- `GAME_V052.md` — full human-readable current game description.
- `blackstar_game_v052.py` — compact playable/runtime prototype with 32×32 strategic exploration and 12×12 tactical encounter generation.
- `test_blackstar_game_v052.py` — invariant tests for current game logic.
- Existing repo context docs remain in `docs/blackstar-raiders/`.

## Important storage note

PNG/JPG visual references are intentionally not treated as repo truth here. Use Notion/Drive for raw visual refs, or Git LFS later if we want binary assets in the repository. Runtime facts live in code, JSON payloads, action logs and tests.

## Notion hub

https://app.notion.com/p/37ecf67d88c6810c91aac7a157069324
