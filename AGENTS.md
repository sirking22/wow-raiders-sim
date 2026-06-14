# WoW Raiders Agent Contract

Use this file when working on this repository from Codex, ChatGPT web, Claude
Code, Antigravity, or another low-effort model.

## Project Kernel

WoW Raiders is a deterministic-first tactical RPG / extraction raid simulator.
The source of truth is data, logs, fixtures, schemas, and tests. Visuals are
generated outputs and must not override engine state.

Current repository baseline:

- `main` contains the older v0.4-v0.9 tactical/strategic simulator.
- `handoffs/v0.40-codex-handoff-github-ready/` contains the imported v0.40
  Codex handoff with rectangular hex field standard, renderer, visual standards,
  and Campaign 03 Raid 01 run data.

## Operating Rules

1. Keep `WIP = 1`: one task, one branch, one acceptance gate.
2. Do not rewrite the engine broadly from a vague prompt.
3. Do not overwrite old canon. Add migration notes, adapters, or explicit
   versioned paths.
4. Do not treat PNGs, screenshots, or mockups as canon when JSON/log/test data
   disagrees.
5. Preserve deterministic behavior: same seed and same inputs should produce
   the same snapshot/log.
6. Every non-trivial change must include a check command and a short result.
7. Low-effort agents may edit only the files named in their task packet.

## Required Reading By Task Type

For any task:

1. `README.md`
2. `AGENTS.md`
3. The exact files named in the task

For web/ChatGPT workflow:

- `docs/WEB_CHAT_DEVELOPMENT_GUIDE.md`
- `docs/AGENT_TASK_ARCHITECTURE.md`

For v0.40 integration:

- `docs/V040_SYNC_AND_MERGE_PLAN.md`
- `handoffs/v0.40-codex-handoff-github-ready/docs/CODEX_HANDOFF.md`
- `handoffs/v0.40-codex-handoff-github-ready/manifests/release-manifest-v040.json`

## Check Commands

Use the available Python executable for the environment.

```bash
# Existing repo tests
for t in tests/test_*.py; do python "$t"; done

# v0.40 handoff verification
cd handoffs/v0.40-codex-handoff-github-ready
python scripts/verify_v040.py
```

On Windows with bundled Codex Python:

```powershell
& 'C:\Users\Arseniy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests\test_hexgrid.py
& 'C:\Users\Arseniy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' handoffs\v0.40-codex-handoff-github-ready\scripts\verify_v040.py
```

## Task Packet Format

Every delegated task should be this small:

```text
Goal:
Files allowed:
Do not touch:
Acceptance:
Check command:
Return:
```

If the task cannot name files and acceptance criteria, it is not ready for a
low-effort agent. Escalate it to a planner first.

## Model Routing

- E0: exact reads, file lists, checks, hashes -> script/local command.
- E1: inventories, labels, first-pass summaries -> low-effort GPT/Gemini.
- E2: scoped code/spec work -> Codex or Sonnet.
- E3: architecture, merge strategy, legal/platform risk, product direction ->
  strong planner/reviewer only.

Strong models should create compact task packets. Low-effort models should
execute those packets and stop.

