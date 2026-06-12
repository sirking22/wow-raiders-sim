# wow-raiders-sim

## Codex Sync 2026-06-12

This branch adds a safe GitHub sync layer for continuing WoW Raiders from Codex,
ChatGPT web, Claude Code, Antigravity, or lower-effort executors.

New entry points:

- `AGENTS.md` - repo-level agent contract.
- `docs/WEB_CHAT_DEVELOPMENT_GUIDE.md` - compact packet for web ChatGPT work.
- `docs/AGENT_TASK_ARCHITECTURE.md` - planner/executor/verifier architecture.
- `docs/V040_SYNC_AND_MERGE_PLAN.md` - how v0.40 should enter the repo without
  overwriting the older v0.8/v0.9 line.
- `handoffs/v0.40-codex-handoff-github-ready/` - imported v0.40 Codex handoff.

Use `handoffs/v0.40-codex-handoff-github-ready/` as preserved source material.
Do not merge it into the active engine until a v0.41 production spec chooses the
merge path.

Детерминированное симуляционное ядро тактической RPG **WoW Raiders · AI Game Master Run**.
Deterministic-first: один и тот же `seed` → идентичный прогон. Источник правды — state/log/snapshot, визуал рендерится из данных, ничего не выдумывая.

## Слои
- **Тактика** — разрешение боя. v0.4 (база, квадраты 8×8) → v0.5 (криты/фланги/OA) → v0.6 (focus-mark, поджог) → v0.7 (ритуал, victory_type, пост-бой) → **v0.8 (гексы, odd-r 8×8, 6 соседей)**.
- **Стратегия** — пошаговая карта региона (`strategic_v07.py`): отряд, террейн, POI, таймер ритуала, handoff в бой.

## Структура
```
engine/      # движок v0.4–v0.8 + hexgrid + strategic + пост-бой
schema/      # JSON Schema игрового состояния
rules/       # рендер-контракты + словарь статусов
tests/       # golden + инварианты (запуск без pytest)
tools/       # генераторы golden-артефактов
fixtures/    # golden-фикстуры enc-005 (вход + эталонные snapshot)
game-data/   # snapshots/ — эталон v0.8 (остальное генерируется, см. .gitignore)
docs/        # модель данных, миграция на гексы, стратегическая карта
```

## Запуск
```bash
# прогнать каноничный бой v0.8 (гексы)
python3 engine/battle_v08.py

# весь тест-набор (golden + детерминизм + гекс-инварианты)
for t in tests/test_*.py; do python3 "$t"; done
```

## Канон v0.8 (детерминирован)
Победа enemies / `ritual_complete`, 8 раундов, 54 активации, ritual 5/5. Эталон: `game-data/snapshots/snap-enc-005-v08-final.json`.
