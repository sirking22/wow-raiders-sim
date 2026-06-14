# Draft PR: v0.40 Handoff + Agent Architecture

## Title

`[codex] add v0.40 handoff and web-agent workflow`

## Body

### What changed

- Added `handoffs/v0.40-codex-handoff-github-ready/` as a preserved v0.40 Codex
  handoff package.
- Added `AGENTS.md` as the repo-level agent contract.
- Added web/low-effort development docs:
  - `docs/WEB_CHAT_DEVELOPMENT_GUIDE.md`
  - `docs/AGENT_TASK_ARCHITECTURE.md`
  - `docs/V040_SYNC_AND_MERGE_PLAN.md`
  - `docs/PRODUCTION_SPEC_V041_DRAFT.md`
- Added GitHub issue and PR templates for small scoped agent tasks.
- Added a README entry block pointing future web chats to the right files.

### Why

The repo needs to become a stable sync hub for Codex, ChatGPT web, Claude Code,
Antigravity, and simpler low-effort executors. v0.40 differs from the current
`main` engine line, so it is preserved as a handoff package instead of
overwriting the active simulator.

### Checks

```text
Existing tests: PASS
v0.40 verifier: {"passed": true, "issues": 0}
```

### Non-goals

- No merge of v0.40 into active engine yet.
- No broad engine rewrite.
- No legal/platform claims about Warcraft/private servers.
- No Notion schema changes.

### Next

Review `docs/PRODUCTION_SPEC_V041_DRAFT.md` and decide whether v0.41 should
promote the v0.40 renderer into `tools/` first.

