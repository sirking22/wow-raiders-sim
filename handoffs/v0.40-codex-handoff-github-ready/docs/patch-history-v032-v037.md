# Patch History v0.32 → v0.37

## v0.32 · Role Performance + Name Canon

- зафиксирован точный канон имени: HesH Dem
- добавлен role-performance ledger: damage, taken, kills, objective, downs, role score
- разделены Campaign MVP и raw role-score leader
- HP=red, XP=purple в stat UI rules

## v0.33 · Final Campaign Screens

- созданы первые data-driven финальные экраны
- зафиксирован мост в Campaign III
- обнаружено, что структура экранов начинает дублироваться

## v0.34 · XP + Base Progression

- исправлен XP-канон: +1220 each, после тренировки Level 6 · 320/1200
- добавлена Пепельная застава Tier 1
- добавлены post-campaign facilities и unlock’и сквада
- 120/300 помечен как запрещённый визуальный дрейф

## v0.35 · Campaign Summary Stat Screens

- созданы 4 экрана статистики
- выявлена проблема: FS01 и FS04 дублировали хронологию и ключевые показатели
- экран FS04 Clean Stat Board признан избыточным для финального UX

Deprecated:
- FS04 Clean Stat Board as a separate final screen

## v0.36 · Campaign Summary IA Fix

- сокращение финальных экранов до 3
- разведены 3 вопроса: что произошло / как выросли / что переносится дальше
- ENC00 зафиксирован как tactical defeat / escape continuation, а не чистая победа
- прогресс героев, прогресс сквада и достижения сквада выведены на отдельный экран
- base/fortress progression вынесен в экран переноса Campaign III

## v0.37 · Full Run Screen Standard

- исправлен канон ENC00: это победа с тяжёлыми потерями, не поражение
- введён единый стандарт экранов полного рана
- все последние image-gen визуалы помечены deprecated visual_reference_only
- описаны 7 типов экранов: strategic, tactical, battle result, chronicle, hero progress, squad/base, next campaign
- создан QA-процесс pre-render / post-render
- сохранена хронология v0.32-v0.37

