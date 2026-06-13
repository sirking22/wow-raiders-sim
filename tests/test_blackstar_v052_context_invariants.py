"""Blackstar Raiders v0.52 context invariants.

This test guards the current project direction so future agents do not regress
back to a route-line board or an 8x8-only tactical prototype.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTX = json.loads((ROOT / "game-data" / "blackstar-raiders" / "current_context_v052.json").read_text(encoding="utf-8"))


def test_project_identity_is_blackstar_raiders():
    assert CTX["project"]["name"] == "Blackstar Raiders"
    assert "Артель добытчиков" in CTX["project"]["player_faction"]
    assert "neutral salvage crew" in CTX["project"]["player_identity"]


def test_map_scale_is_current_direction():
    assert CTX["map_scale"]["strategic_map"] == "32x32 hex"
    assert CTX["map_scale"]["normal_tactical_battle"] == "12x12 hex"
    assert CTX["map_scale"]["small_test_battle"] == "8x8 hex"


def test_strategic_layer_is_open_world_not_route_board():
    correct = CTX["strategic_layer"]["correct_direction"]
    wrong = CTX["strategic_layer"]["wrong_direction"]
    assert "open-world 32x32 hex sector" in correct
    assert "fog of war" in correct
    assert "scouting" in correct
    assert "hero route lines" in wrong
    assert "board-game path lines" in wrong


def test_fog_tile_states_are_explicit():
    assert CTX["strategic_layer"]["tile_states"] == [
        "unknown",
        "visible",
        "scanned",
        "discovered",
    ]


def test_entities_exist_for_open_sector():
    entities = set(CTX["strategic_layer"]["entity_types"])
    for required in {
        "party",
        "enemy_patrol",
        "neutral_squad",
        "resource_site",
        "event_point",
        "hazard",
        "tactical_entry",
    }:
        assert required in entities


def test_v052_requires_runtime_not_only_visuals():
    required = set(CTX["versions"]["v0.52"]["required_systems"])
    assert "party token on 32x32 hex map" in required
    assert "visibility radius" in required
    assert "scout action" in required
    assert "tactical 12x12 encounter generation" in required


def test_visuals_do_not_define_facts():
    hard_rules = "\n".join(CTX["hard_rules"])
    assert "Data first" in hard_rules
    assert "Visuals are references, not facts" in hard_rules
    assert "All victory numbers must come from run data" in hard_rules
