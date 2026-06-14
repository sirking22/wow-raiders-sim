# WoW Raiders Sim · v0.40 Codex Handoff

Готово для ПК/Codex/GitHub.

## Внутри

- `engine/hex_raid_simulator_v039.py` — текущий детерминированный hex-движок.
- `engine/render_hex_field_v040.py` — renderer прямоугольного hex-поля.
- `game-data/raid-runs/campaign03_raid01_full_run_v039.json` — текущий канон прогона.
- `game-data/standards/hex-field-standard-v040.json` — стандарт поля.
- `visual-standards/png/` — визуальные стандарты.
- `docs/CODEX_HANDOFF.md` — задача для Codex.
- `docs/GITHUB_PUSH_PLAN.md` — план пуша.

## Быстрый запуск

```bash
python engine/hex_raid_simulator_v039.py --out game-data/raid-runs/local_run.json
python engine/render_hex_field_v040.py --output visual-standards/png/local_hex.png --type STANDARD_TACTICAL_FIELD --coords
python scripts/verify_v040.py
```
