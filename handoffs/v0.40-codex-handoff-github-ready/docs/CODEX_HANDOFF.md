# Codex Handoff Brief · WoW Raiders v0.40

## Задача

Продолжить разработку hex-движка и UI renderer.

## Текущий канон

- Герои: CandyPeace, Dr.Feed, EZ
- Текущий рейд: `campaign03_raid01_full_run_v039.json`
- Статус: successful_extraction
- Оба боя: victory
- Все герои alive

## Следующие задачи для Codex

1. Разнести монолитный движок на модули:
   - `engine/core/hex.py`
   - `engine/core/state.py`
   - `engine/core/actions.py`
   - `engine/core/simulator.py`
   - `engine/content/heroes.py`
   - `engine/content/enemies.py`
   - `engine/content/encounters.py`

2. Улучшить renderer:
   - blocked / cover / objective / threat zones
   - SVG export
   - режим `--from-run-json`
   - проверка rectangular bounds

3. Добавить тесты:
   - hex_distance
   - movement
   - HP never negative
   - final HP equals last state
   - objective cap
   - renderer keeps rectangular arena

4. Подготовить GitHub CI.
