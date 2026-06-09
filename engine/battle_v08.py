"""WoW Raiders — боевой движок v0.8 (поверх v0.7): полный порт боя на ГЕКСЫ.

Что меняется относительно v0.7 (поле было 8x8 квадратами, дистанция Чебышёва):
  * Геометрия поля переведена на гексы (odd-r offset, как в Heroes / стратегической карте v0.7).
  * Дистанция: hexgrid.distance (cube) вместо Чебышёва (max(dx,dy)).
  * Соседство/движение: 6 соседей вместо 8 (диагоналей нет).
  * LOS / линия огня: гекс-линия (cube-интерполяция) вместо растрового луча по квадратам.
  * Укрытия (half/full), опасные клетки, поджог, фланкинг (рядом = 1 гекс), opportunity
    attacks, momentum, focus-mark, ритуал RS — ВСЕ механики v0.4-v0.7 сохранены без изменений,
    меняется только то, КАК считается соседство/дистанция/линия.

Лейблы клеток те же (B2 = столбец B, ряд 2); (col,row) трактуются как odd-r offset.
Детерминизм по seed сохранён. Свой seed "enc_005_v08" => своя канон-фикстура,
golden v0.4 / v0.7 НЕ затрагиваются (их движки и сиды не меняются).
"""
import hexgrid
from battle_v04 import cell_to_xy, xy_to_cell, COLS
from battle_v07 import BattleV07

WIDTH = 8
HEIGHT = 8


class BattleV08(BattleV07):
    VERSION = "v0.8-hex"
    GRID = "hex"

    def __init__(self, seed="enc_005_v08", ritual_required=5):
        super().__init__(seed=seed, ritual_required=ritual_required)

    # ---- ГЕКС-ГЕОМЕТРИЯ (переопределяет квадратную из v0.4) ----
    def cheb(self, a, b):
        """Имя историческое; теперь это гекс-дистанция (cube)."""
        return hexgrid.distance(cell_to_xy(a), cell_to_xy(b))

    def adjacent(self, a, b):
        return self.cheb(a, b) == 1

    def neighbors(self, cell):
        x, y = cell_to_xy(cell)
        out = []
        for nx, ny in hexgrid.neighbors((x, y)):
            if 1 <= nx <= WIDTH and 1 <= ny <= HEIGHT:
                out.append(xy_to_cell(nx, ny))
        return out

    def line_cells(self, a, b):
        return [xy_to_cell(x, y) for (x, y) in hexgrid.line(cell_to_xy(a), cell_to_xy(b))]

    # ---- визуализация: odd-r со смещением нечётных рядов ----
    def board(self):
        occ = {a.pos: a.id for a in self.actors.values() if a.alive}
        down = {a.pos: a.id.lower() for a in self.actors.values()
                if "downed" in a.statuses and "dead" not in a.statuses}
        out = []
        for y in range(HEIGHT, 0, -1):
            row = []
            for x in range(1, WIDTH + 1):
                c = xy_to_cell(x, y)
                if c in occ:
                    row.append(occ[c])
                elif c in down:
                    row.append(down[c])
                elif not self.cells[c].walkable:
                    row.append("##")
                elif self.cells[c].hazard == "unstable_rune":
                    row.append("Ru")
                elif self.cells[c].hazard == "collapse_risk":
                    row.append("Cr")
                elif self.cells[c].hazard == "oil":
                    row.append("Oi")
                elif self.cells[c].cover == "half":
                    row.append("cv")
                else:
                    row.append("..")
            indent = "  " if (y & 1) else ""  # odd-r: нечётные ряды сдвинуты
            out.append(f"{y} | {indent}" + " ".join(f"{v:>2}" for v in row))
        out.append("    " + " ".join(f"{c:>2}" for c in COLS))
        return out

    def grid_meta(self):
        return {"type": "hex", "layout": "odd-r", "width": WIDTH, "height": HEIGHT,
                "neighbors": 6, "distance": "cube", "label": "col-letter + row-number (e.g. B2)"}

    def snapshot(self):
        snap = super().snapshot()
        snap["snapshot_id"] = "snap_" + self.seed
        snap["engine_version"] = self.VERSION
        snap["grid"] = self.grid_meta()
        return snap


def main():
    import json
    snap = BattleV08().run_until_end()
    print(json.dumps({k: snap[k] for k in ["winner", "victory_type", "ritual", "round",
                                            "activation_count", "mechanics_summary", "grid", "board"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
