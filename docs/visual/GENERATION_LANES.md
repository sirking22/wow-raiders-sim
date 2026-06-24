# War Raiders · Final Visual Generation Lanes

Final/high-quality visuals are produced in dedicated generation lanes, not by Notion storage or the PC worker.

## Current decision

- **GPT Images 2** — primary final visual lane for polished images, hero canon, key UI frames and approved-direction candidates.
- **GPT Web** — active support lane for web-based visual experiments, references, prompt iteration and creative exploration.
- **Codex** — future lane for automation, prompt docs, manifests and possible generation handoff. Currently blocked for final generation because Codex has no tokens.
- **Notion AI Images** — prototype/draft lane only.
- **PC-worker** — packaging lane only: contact sheets, batch folders, review boards and handoff files.

## Standard loop

```text
Visual DB row / Asset Set
-> Prompt packet
-> GPT Images 2 / GPT Web / Codex lane
-> Output image
-> Notion Visual DB intake
-> Review packet
-> Canon Level update
-> GitHub manifest update
-> Next generation uses approved refs
```

## Stability rule

Stable generations come from:

- Asset Set
- Canon Level
- prompt template
- Runtime Anchor
- visual manifest
- approved references
- What We Take / What We Don't Take

The image model can vary, but the system prompt + manifest + approved refs must remain stable.

## Default until Codex has tokens

```text
Final visuals: GPT Images 2
Fast exploration: GPT Web
System / storage / review: Notion + GitHub + PC-worker
Codex generation: paused until tokens
```
