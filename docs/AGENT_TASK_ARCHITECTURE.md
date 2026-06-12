# Agent Task Architecture

WoW Raiders should be developed as a chain of small, verifiable tasks. The
planner spends reasoning once, then lower-cost agents do scoped mechanical work.

## Roles

| Role | Purpose | Typical model/surface |
|---|---|---|
| Planner | Chooses architecture, task split, acceptance gates | Codex high effort, Claude Opus/Sonnet |
| Executor | Makes a small patch or inventory | ChatGPT low effort, Gemini/Antigravity, Codex low effort |
| Verifier | Runs tests, compares manifests, checks files | local scripts, CI, Codex |
| Curator | Records outcome and next task | GitHub issue/PR, Notion, README/task docs |

## Task Size Rule

A task is ready for a low-effort executor only if it has:

- one goal;
- named files or folders;
- explicit non-goals;
- 3-5 acceptance criteria;
- one check command or review method;
- expected return format.

If any of those are missing, the task remains with the planner.

## Canon Layers

1. Deterministic source: engine code, schemas, fixtures, logs, manifests.
2. Derived artifacts: reports, renderer output, PNGs, boards.
3. Planning artifacts: docs, issues, PR bodies, Notion notes.
4. Inspiration: Warcraft-like visuals, extraction games, board/card references.

Only layer 1 can define game truth.

## GitHub As Sync Hub

GitHub should hold:

- stable code and tests;
- versioned handoffs;
- issues for narrow tasks;
- PRs for reviewable change batches;
- docs that let web chats join without local workspace memory.

GitHub should not hold:

- secrets;
- broad personal memory;
- unreviewed Notion schema changes;
- raw prompt dumps;
- private legal assumptions.

## Branch Strategy

Use branches like:

```text
codex/<short-purpose>
web/<short-purpose>
agent/<short-purpose>
```

Recommended branch flow:

1. Start from `main`.
2. Add one coherent change.
3. Run relevant checks.
4. Push branch.
5. Open draft PR or leave branch as sync checkpoint.

Do not push large unrelated task batches in one branch.

## Backlog Shape

Use this issue/task format:

```text
Title:
Track: Core / v0.40 / Mechanics / Visual / Card / Agent OS
Effort: E0 / E1 / E2 / E3
Goal:
Files:
Acceptance:
Check:
Non-goals:
```

## Current Routing

P0 now:

- Keep v0.40 handoff preserved and reviewable in GitHub.
- Create a clear merge path from v0.40 into the existing v0.8/v0.9 simulator.
- Make this repo usable from web chats through compact docs.

P1 next:

- Create `Production Spec v0.41`.
- Decide whether v0.40 renderer becomes a new module or a separate tool package.
- Add tests for rectangular field bounds, HP floor, objective cap, and final HP
  consistency.

