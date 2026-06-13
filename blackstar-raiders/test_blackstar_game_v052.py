"""Invariant tests for Blackstar Raiders v0.52 compact runtime."""

from blackstar_game_v052 import (
    StrategicSector,
    EventKind,
    TileState,
    make_heroes,
    generate_tactical_encounter,
)


def test_strategic_map_is_32_by_32_open_world():
    sector = StrategicSector(seed=52052)
    assert sector.width == 32
    assert sector.height == 32
    assert len(sector.tiles) == 32 * 32
    assert sector.visible_payload()["hard_rule"].startswith("no route-lines")


def test_party_has_visibility_and_fog_states():
    sector = StrategicSector(seed=52052)
    states = {tile.state for tile in sector.tiles.values()}
    assert TileState.UNKNOWN in states
    assert TileState.VISIBLE in states or TileState.DISCOVERED in states
    assert sector.party.visibility_radius == 3


def test_scouting_reveals_more_information():
    sector = StrategicSector(seed=52052)
    before = sum(1 for t in sector.tiles.values() if t.state != TileState.UNKNOWN)
    result = sector.scout((9, 16), radius=4)
    after = sum(1 for t in sector.tiles.values() if t.state != TileState.UNKNOWN)
    assert result["action"] == "scout"
    assert after > before


def test_heroes_are_salvage_artel_entities_with_budget_30():
    heroes = make_heroes()
    assert [h.name for h in heroes] == ["EZ", "Candy Peace", "Dr.Feed"]
    for hero in heroes:
        assert hero.attrs is not None
        assert hero.attrs.budget == 30
        assert hero.equipment is not None
        assert hero.abilities
        assert "must match hero-canon reference" in hero.visual_identity


def test_battle_events_generate_12_by_12_tactical_encounters():
    sector = StrategicSector(seed=52052)
    battle_events = [e for e in sector.events.values() if e.kind in (EventKind.BATTLE, EventKind.BOSS)]
    assert battle_events
    for event in battle_events:
        encounter = generate_tactical_encounter(event)
        assert encounter.size == (12, 12)
        assert len(encounter.heroes) == 3
        assert len(encounter.enemies) == 4


def test_tactical_payload_contains_formula_driven_action_log():
    sector = StrategicSector(seed=52052)
    encounter = generate_tactical_encounter(sector.events["bastion"])
    payload = encounter.run_round_one_script()
    assert payload["schema"] == "blackstar-raiders.tactical-encounter-payload.v0.52"
    assert payload["player_facing_rule"] == "screen numbers must come from this payload, not generated visuals"
    damage_events = [e for e in payload["action_log"] if "damage" in e]
    assert damage_events
    assert all("formula" in e["damage"] for e in damage_events)


def test_objective_progress_comes_from_ability_and_stats():
    sector = StrategicSector(seed=52052)
    encounter = generate_tactical_encounter(sector.events["bastion"])
    payload = encounter.run_round_one_script()
    assert payload["objective"]["progress"] > 0
    assert payload["objective"]["required"] == 10
