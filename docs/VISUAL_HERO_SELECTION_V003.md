# Visual Hero Selection v003

Status: visual direction prompt, generated in Codex chat.

## Direction

- Reference mood: hard WH40 latest-edition grimdark planetary raid.
- Public mode: original-safe `Blackstar Raiders`.
- Tone: brutal, gothic, military, high-risk, no soft fantasy-MMO.
- Required player slots: `EZ`, `Candy Peace`, `Dr.Feed`.

## Screen Contract

This visual must eventually be rendered from the v0.41 `hero_selection` screen
payload:

```text
game-data/screen-payloads/campaign01_v041_screen_payloads.json
```

The image can be used as visual taste direction, but canonical text, hero stats,
slot state, and mission facts must come from the screen payload.

## Required Composition

- Top title: `BLACKSTAR RAIDERS - HERO SELECTION`.
- Left panel: three unassigned reserved player slots:
  `EZ`, `Candy Peace`, `Dr.Feed`.
- Center: 9 unselected hero cards:
  Void Chaplain, Ash Scout, Plague Surgeon, Siege Gunner,
  Sanctioned Prism Psyker, Iron Tech-Adept, Deathworld Beastmaster,
  Penitent Duelist, Xeno Relic Sniper.
- Right panel: mission preview:
  `Blightfall Relic Extraction`, `Korvash Prime`, extreme threat,
  extraction window, camp supplies.
- Bottom bar: loadout, directives, confirm/deploy disabled until heroes are
  chosen.

## Prompt Core

```text
Create a 16:9 high-resolution game UI screen concept for a hero selection lobby
in a hard grimdark far-future gothic military sci-fi extraction raid game,
strongly inspired by the latest-edition Warhammer 40,000 tabletop mood but using
original-safe symbols and no official logos. The screen should feel brutal,
heavy, militarized, cathedral-industrial, with black iron, worn gold trim, red
warning lights, ash, smoke, orbital war atmosphere, gothic arches.
```
