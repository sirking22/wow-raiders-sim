# Бриф для ПК-Клод (Claude Code)

## Контекст
Движок боя уже работает (`engine/battle_v04.py`, MVP-0.4): доска 8×8, инициатива, AC+d20, урон, bloodied/downed/death-saves, protection-reaction, Lay on Hands, cautious retreat, cunning hide/disengage, реакции, террейн, gm_morale_shift. Детерминизм проверен golden-тестом.

## Задачи (по приоритету)
1. **Формализация ядра** (Opus — ядро, Sonnet — объём):
   - разнести `battle_v04.py` на модули: `board`, `actors`, `rng`, `actions`, `reactions`, `intents`, `resolve`;
   - выделить чистую функцию `resolve_encounter(seed, state, intents) -> {snapshot, log, delta}`;
   - сохранить golden-совпадение с `fixtures/` (CI).
2. **Контракт схемы**: закрепить `schema/game.schema.json` как валидатор входа/выхода.
3. **Новые механики** (из выводов прогона): objective-based victory (extraction / artifact / alarm clock / retreat route); EZ escape kit; тюнинг protection radius/timing; валидация rogue hide/disengage.
4. **Инфра**: Cloudflare Worker `wr-sim-api` (D1 осн. + KV snapshot-кэш); Notion + FS sync writeback.
5. **Стратегический слой** (Heroes-like): карта/отряд/ресурсы → порождение стычки (encounter seed) → тактика → возврат результата.

## Инварианты (не ломать)
- Детерминизм по seed.
- Источник истины — snapshot/log, не визуал.
- Схема данных совместима с fixtures/ (не ломать ключи без миграции).
