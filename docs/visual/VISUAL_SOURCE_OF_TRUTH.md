# War Raiders · Visual Source of Truth

Purpose: keep War Raiders visual production systematic, reviewable, and tied to runtime facts.

## Core loop

```text
Runtime facts -> Visual contract -> Prompt / Worker -> Visual artifact -> Review -> Visual DB -> Canon / Task / GitHub doc
```

## Storage policy

- **Notion Visual DB** stores images, review notes, statuses, What We Take / What We Don't Take, Asset Sets, Canon Levels, Runtime Anchors.
- **GitHub** stores text-level contracts: manifests, prompt templates, runtime anchors, situation taxonomy, guardrails.
- **PC / worker** packages batches: prompts, payload placeholders, contact sheets, review packets.
- **GPT Web / GPT Image** are scout/generation layers, not canon.

## Asset Sets

Asset Sets are the primary gallery grouping model.

Initial sets:

- `WR-SET-STRATEGIC-MAP`
- `WR-SET-GAME-STATE-KIT`
- `WR-SET-HERO-TRIO`
- `WR-SET-TACTICAL-UI`
- `WR-SET-VICTORY-POSTBATTLE`
- `WR-SET-EXTERNAL-GPT-REFS`
- `WR-SET-IMAGE-BATCH-01`
- `WR-SET-IMAGE-BATCH-02`
- `WR-SET-WORKER-OUTPUTS`

## Canon levels

- `L0 Raw / External` — unreviewed image / GPT output / web ref.
- `L1 Reference` — useful reference with What We Take / Don't Take.
- `L2 Useful Direction` — fits current project direction.
- `L3 Approved Direction` — accepted by human review.
- `L4 Production Lock` — bound to runtime / screen contract / repeated use.

## Hard rules

- Visuals never invent gameplay facts.
- No invented HP, damage, objective values, rewards, XP, injuries, enemy stats, hero status, campaign consequences, economy values.
- Use `TBD from runtime` for missing values.
- Strategic map is open-world hex sector, not route-line board.
- Raw images are not stored in GitHub by default.
