# Blackstar Raiders · Current Full Game v0.52

This page is the current game state, not only a pitch.

## What the game is now

**Blackstar Raiders** is a deterministic-first tactical RPG / strategic exploration prototype.

The player controls a neutral interspecies salvage/exploration artel: **Артель добытчиков «Чёрная Звезда»**. They are not a clean heroic army. They are explorers, scavengers, relic hunters, medics, psykers, armored escorts and technical specialists operating in a hostile ruined sector.

## Current active scale

```text
Strategic layer: 32×32 open-world hex sector
Tactical layer: 12×12 hex battle map by default
Small tactical tests: 8×8 only
```

The strategic layer is **not** a route-line board. No hero route-lines as the main map. The current direction is an open sector with terrain, fog of war, visibility radius, scouting, event points, enemy patrols, neutral squads, resource sites and tactical-entry nodes.

## Source of truth rule

```text
Runtime/data/tests define facts.
Visuals are references and outputs.
A generated victory screen may never invent numbers.
Hero models must match hero canon across hero page, battle, victory and intel screens.
```

## Current playable/runtime package

The compact runtime snapshot is here:

```text
blackstar-raiders/blackstar_game_v052.py
```

It contains:

- 32×32 strategic sector generation;
- terrain types and movement/risk rules;
- fog states: unknown / visible / scanned / discovered;
- party token with visibility radius;
- scout action;
- movement action;
- event points;
- 12×12 tactical encounter generation;
- three hero entities;
- four enemy entities;
- equipment and abilities;
- deterministic action log;
- formula-driven damage and objective progress.

Tests:

```text
blackstar-raiders/test_blackstar_game_v052.py
```

## Heroes

### EZ

Role: Призма-псайкер / control / objective pressure.

Identity: purple prism psyker, slim explorer silhouette, prism focus/staff. Must match the hero-canon reference.

Equipment: Призменный фокус.

Abilities:

- Якорь узора;
- Призменный замок;
- Копьё разума.

### Candy Peace

Role: Часовенный Бездны / tank / line holder.

Identity: heavy armored tank knight, shield/refraction field, broad silhouette. Must match the hero-canon reference.

Equipment: Рефракторное поле.

Abilities:

- Удержание линии;
- Щитовой рывок;
- Удар Бездны.

### Dr.Feed

Role: Чумной хирург / medic / support.

Identity: plague surgeon medic, mask, vials, green toxic accent. Must match the hero-canon reference.

Equipment: Токсичный экран.

Abilities:

- Полевая хирургия;
- Заплатать и сдвинуться;
- Токсичный экран.

## Enemy pack

Current base hostile pack:

- Хранитель реликвария — objective guardian;
- Подавитель — suppression;
- Рой сервопауков — fast pressure;
- Сканирующий адепт — heat/control.

## Strategic layer rules

Tile states:

```text
unknown
visible
scanned
discovered
```

Terrain types:

```text
blocked
ash_waste
ruins
industrial_hulk
catacombs
relic_site
safe_camp
enemy_zone
```

Event kinds:

```text
calm
resource
intel
hazard
battle
boss
mystery
```

Battle or boss events generate tactical encounters at **12×12**.

## Current known mistake fixed

Previous context push was too thin: it described the direction but did not carry enough of the actual game. This v0.52 package adds the compact runtime and invariant tests so the repo contains a working current game skeleton, not only notes.

## What is still outside GitHub

Raw PNG/JPG reference images are still better stored in Notion/Drive, not in normal Git history. GitHub stores the game logic, data contracts and tests. If we later want images in repo, use Git LFS or a curated small `assets/references/` folder.
