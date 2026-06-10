# HEX MIGRATION — переход тактического поля с квадратов на гексы

Статус: **v0.7 — геометрия готова и протестирована; полный порт боя — v0.8 (в работе).**

Поле боя меняется с квадратной сетки 8×8 (Chebyshev) на **гексы в стиле Heroes**.
Источник истины не меняется: state / log / replay; визуал рендерится из снапшотов.

## 1. Система координат

- Раскладка **odd-r offset** (горизонтальные ряды, нечётные ряды сдвинуты вправо).
- Человеко-читаемая метка гекса: `(col, row)` → сериализация `c{col}r{row}` (например `c3r2`).
- Для дистанций/радиусов offset переводится в **cube**-координаты.
- Модуль: `engine/hexgrid.py` (чистая геометрия, без игрового состояния).

### API hexgrid.py
| Функция | Назначение |
|---|---|
| `oddr_to_cube(col,row)` | offset → cube |
| `cube_distance(a,b)` | дистанция в cube |
| `distance(a,b)` | гекс-дистанция между двумя offset-гексами |
| `neighbors(hex)` | 6 соседей с учётом чётности ряда |
| `in_bounds(hex,w,h)` / `neighbors_in_bounds(...)` | проверка/фильтр по границам |
| `hexes_in_range(center,radius)` | все гексы в радиусе (BFS) |
| `reachable(start,budget,w,h,enter_cost)` | Dijkstra: достижимые гексы в пределах бюджета хода |
| `shortest_path(start,goal,w,h,enter_cost)` | Dijkstra: путь + стоимость |

Тесты: `tests/test_hexgrid.py` (6 соседей, dist=1 у соседа, симметрия, радиусы, бюджет/границы, недостижимость). **5/5 PASS.**

## 2. Что меняется в тактическом движке (square → hex)

| Аспект | Было (квадраты) | Станет (гексы) |
|---|---|---|
| Соседство | 8 направлений | 6 направлений |
| Дистанция | Chebyshev `max(|dx|,|dy|)` | `hexgrid.distance` (cube) |
| Движение | move-6 по клеткам | бюджет хода + `reachable`/`shortest_path` с enter_cost террейна |
| Дальность атак/АОЕ | квадратные кольца | `hexes_in_range` |
| LOS / cover / blocked | по клеткам | по линии гексов (cube lerp) — порт в v0.8 |
| Фланги | соседние клетки | соседние гексы (6) — порт в v0.8 |

## 3. План порта боевого движка (v0.8)

1. Ввести `enter_cost`/террейн на тактическом гекс-поле; заменить Chebyshev на `hexgrid.distance` во всех проверках дальности.
2. Переписать выбор перемещения на `reachable`/`shortest_path`.
3. Портировать LOS/cover/blocked на гекс-линии; пересмотреть фланг-логику (6 соседей).
4. Обновить render-contract боевых экранов: `grid.type="hex"`, `layout="odd-r"`.
5. Перегенерировать golden-снапшот боя на гексах и зафиксировать новую детерминированную канву (старый square-golden остаётся как v0.7 архив).

> Принцип честности: полный порт боя не выдаётся за готовый. battle_v04..v07 содержат квадратные допущения; слепой порт сломает golden. Поэтому геометрия и стратегический слой готовы сейчас, а боевой порт идёт отдельным детерминированным шагом v0.8.

## 4. v0.8 — порт боя на гексы ВЫПОЛНЕН ✅

`engine/battle_v08.py` (`BattleV08(BattleV07)`, seed `enc_005_v08`) — полный тактический бой на гексах.

**Как сделано без поломки golden v0.4/v0.7:**
- Геометрия в `battle_v04` вынесена в переопределяемые методы `self.cheb` / `self.adjacent` (дефолт = прежний Чебышёв → поведение v0.4–v0.7 не изменилось).
- `battle_v08` переопределяет `cheb` (→ `hexgrid.distance`), `adjacent` (→ `cheb==1`), `neighbors` (6 гекс-соседей), `line_cells` (гекс-линия). `los`/`cover`/`path_to`/`best_adjacent`/`safest_retreat`/`move`/OA/фланки работают через эти примитивы автоматически.
- `hexgrid` расширен `cube_round`/`cube_to_oddr`/`line` (cube-интерполяция) для LOS.

**Канон v0.8 (детерминирован):** победа enemies / `ritual_complete`, 8 раундов, 54 активации, ritual 5/5, flanks 3, focus_marks 8, crits 2, ignites 1. Снапшот: `game-data/snapshots/snap-enc-005-v08-final.json`, полный лог: `game-data/battle-reports/enc-005-v08-final-state.json`.

**Тесты:** `tests/test_battle_v08.py` (гекс-инварианты 5/5: соседи≤6+симметрия, adjacency↔dist1, hex≠Чебышёв, LOS×full-cover, бюджет хода) и `tests/test_golden_v08.py` (детерминизм + golden + контракт). Рендер-контракт: `rules/render-contract-v08.json` (`grid.type=hex`, `odd-r`).

**Regression:** golden v0.4 ✓, v0.7 ✓, hexgrid 5/5 ✓, strategic 8/8 ✓ — всё зелёное.
