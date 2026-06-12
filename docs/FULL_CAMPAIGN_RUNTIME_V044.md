# Full Campaign Runtime v0.44

Status: implemented end-to-end campaign checkpoint.

## Purpose

v0.44 turns the separate calculated layers into one replayable campaign run.

It joins:

- v0.42 rules, directives, loadout, progression, and patch intake;
- BattleV09 tactical frames and action logs;
- campaign screens from hero selection to continuity handoff.

The result is not final balance. It is a traceable game loop where every screen
can be rendered from state/logs/calculation references.

## Files

```text
engine/campaign_v044.py
tests/test_campaign_v044.py
game-data/campaign-runs/campaign01_v044_full_run.json
game-data/screen-payloads/campaign01_v044_screen_payloads.json
game-data/camp/camp_state_after_campaign01_v044.json
game-data/continuity/campaign01_v044_continuity_ledger.json
game-data/patches/campaign01_v044_patch_contract.json
```

## Screen Chain

Current run outputs 20 screens:

```text
hero_selection
squad_lock_in
campaign_briefing
camp_loadout
drop_in
strategic_map_start
strategic_turn x3
tactical_encounter_start
battle_v09_round x3
gm_interlude
extraction
run_highlights
run_summary
progression
camp_return
campaign_continuity
```

Every screen includes:

- `state`;
- `ui_panels`;
- `log_refs`;
- `calculation_refs`;
- `render_contract`;
- optional `next_decisions`.

## AI Layers

The generated `ai_turn_log` records four distinct layers:

- `ai_director`: route pressure, clocks, extraction escalation;
- `ai_gm`: player-facing choice framing after computed state;
- `ai_heroes`: movement, main action, bonus action from player directives;
- `ai_enemies`: threat pressure and target bias.

Hero AI decisions carry action score references from `rules_v042.choose_action`.

## Continuity

v0.44 writes a continuity ledger after the run:

```text
game-data/continuity/campaign01_v044_continuity_ledger.json
```

It records:

- resolved route nodes;
- hero deltas;
- camp state after rewards/progression;
- persistent events;
- AI turn count.

## Balance Audit

The run includes `balance_audit`.

Current status:

```text
provisional_balance_trace
```

This is intentional. The stats still need balance work, but v0.44 makes the
next pass concrete by preserving formulas, movement budgets, action scores,
objective speed, extraction readiness, and enemy pressure in one object.

Current next balance targets:

- enemy lethality is too low if all hostiles survive but extraction is trivial;
- objective progress reaches target quickly;
- stat names need a feel pass after the mechanics stabilize.

## Patch Intake

v0.44 patch intake accepts proposals from:

- ChatGPT Web;
- Codex;
- Notion;
- GitHub PR;
- Google Drive manifest;
- local file packet.

Heavy visuals stay outside Git and enter through Google Drive or local artifact
manifests. Repo files carry deterministic JSON/spec/test fixtures.

## Checks

```powershell
& '<bundled-python>' .\tests\test_campaign_v044.py
```

Full suite:

```powershell
foreach ($t in Get-ChildItem .\tests -Filter test_*.py) { & '<bundled-python>' $t.FullName }
```
