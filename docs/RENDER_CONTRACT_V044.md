# Render Contract v0.44

Status: draft production contract for the active v0.44 campaign runtime.

## Purpose

v0.44 is the current source-of-truth runtime. The render layer must not promote
v0.40 or any visual artifact above v0.44 state, logs, calculations, and screen
payloads.

The contract exists to preserve this order:

```text
campaign input -> runtime state -> logs/calculations -> screen payload -> render contract -> pre-render -> final visual artifact
```

Never reverse this order.

## Canon rule

Only these layers can define facts:

1. Runtime state.
2. Action logs and AI turn logs.
3. Calculation references.
4. Screen payload fields derived from the above.

Rendered PNGs, cinematic images, slide decks, screenshots, and mockups are
outputs. They may express mood, lighting, composition, and interface style, but
must not change facts.

## Required screen payload fields

Each v0.44 renderable screen should expose:

```json
{
  "screen_id": "string",
  "stage": "string",
  "title": "string",
  "time_index": 0,
  "state": {},
  "ui_panels": [],
  "log_refs": [],
  "calculation_refs": [],
  "render_contract": {},
  "next_decisions": []
}
```

`next_decisions` is optional for terminal/reporting screens.

## Render contract shape

Recommended minimum:

```json
{
  "artifact_type": "screen_structure | tactical_map | battle_round | run_report | cinematic_prompt",
  "truth_source": {
    "state_paths": [],
    "log_refs": [],
    "calculation_refs": []
  },
  "must_show": [],
  "exact_labels": [],
  "must_not_invent": [],
  "layout_intent": "string",
  "visual_tone": "string",
  "pre_render": {
    "required": true,
    "outputs": []
  }
}
```

## Required truth anchors

A render contract should explicitly anchor any field that can break trust:

- hero names;
- hero classes/archetypes;
- current HP and max HP;
- injuries and status effects;
- enemy names and alive/downed state;
- positions on tactical map;
- round number;
- action actor;
- action target;
- damage, healing, objective progress, and resource changes;
- mission outcome;
- loot, rewards, XP, traits, and continuity changes.

If a fact is not available in state/log/calculation refs, the renderer should
show it as unknown or omit it. It must not infer it from image composition.

## Pre-render requirement

For tactical, battle, and report screens, the final visual pass should be fed by
a pre-render artifact first.

A pre-render may be:

- JSON layout;
- SVG wireframe;
- deterministic tactical map PNG;
- UI panel manifest;
- slide layout manifest.

The pre-render exists to catch numeric and positional drift before cinematic
image generation.

## v0.40 relationship

v0.40 is preserved reference material only.

The old v0.40 renderer may be inspected as a geometry or implementation
reference, but it must not define the active campaign payload shape. If reused,
it should be adapted to v0.44 screen payloads through a narrow adapter.

Correct direction:

```text
v0.44 screen payload -> adapter -> renderer utility
```

Incorrect direction:

```text
v0.40 renderer shape -> v0.44 campaign runtime
```

## Acceptance checklist

A screen is render-ready when:

- it has a stable `screen_id` and `stage`;
- all numeric labels in the planned visual exist in state/log/calculation refs;
- all must-show objects are present in state or ui panels;
- `must_not_invent` blocks common hallucinations;
- tactical screens have position or layout data, or explicitly declare why they
  are abstract/non-positional;
- the pre-render output can be generated before final visual styling.

## Anti-drift examples

Do not:

- change HP for readability;
- add a dead enemy because the visual needs drama;
- move heroes to a better composition if the screen is tactical and positional;
- invent loot not present in the run summary;
- rename `Dr.Feed` or normalize player nicknames;
- copy old v0.40 field assumptions into v0.44 without an adapter.

Do:

- use cinematic framing for mood;
- crop or scale UI panels;
- use symbolic background elements when they do not contradict state;
- generate separate visual artifacts per screen;
- keep raw data references close to every rendered artifact.
