"""Acceptance tests for the v0.42 rules spine."""

import copy
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import rules_v042 as rules


def test_rules_model_validates():
    assert rules.validate_rules_model() == []


def test_every_hero_uses_exact_attribute_budget():
    for hero in rules.build_roster():
        assert hero["attribute_budget"] == rules.ATTRIBUTE_BUDGET
        assert sorted(hero["attributes"]) == sorted(rules.ATTRIBUTE_KEYS)


def test_derived_stats_are_formula_based():
    chaplain = rules.hero_by_id("void_chaplain")
    attrs = chaplain["attributes"]
    derived = chaplain["derived"]
    assert derived["max_hp"] == 18 + attrs["endurance"] * 4 + attrs["force"]
    assert derived["movement"] == 3 + attrs["agility"] // 2
    assert derived["initiative"] == attrs["agility"] + attrs["will"] // 2
    assert derived["supply_slots"] == 2 + attrs["tech"] // 3 + attrs["endurance"] // 4


def test_loadout_respects_slots_and_resources():
    hero = rules.hero_by_id("plague_surgeon")
    directive = rules.normalize_directive({"survival": 0.9, "consumable": 0.9, "objective": 0.5})
    resources = {"scrap": 18, "relic_shards": 4, "medicae": 3, "intel": 3}
    loadout, after = rules.recommend_loadout(hero, directive, resources)
    loaded = rules.apply_loadout(hero, loadout)
    assert loaded["loadout_slots_used"] <= hero["derived"]["supply_slots"]
    for key, value in after.items():
        assert value >= 0, key
    assert loaded["derived"]["max_hp"] == hero["derived"]["max_hp"]


def test_squad_assembly_preserves_player_names():
    slots = [
        {"player": "EZ", "assigned_hero": "sanctioned_prism_psyker"},
        {"player": "Candy Peace", "assigned_hero": "void_chaplain"},
        {"player": "Dr.Feed", "assigned_hero": "plague_surgeon"},
    ]
    directives = {name: {"objective": 0.5, "survival": 0.5} for name in rules.PLAYER_NAMES}
    squad, resources, log = rules.assemble_squad(slots, directives, {"scrap": 18, "relic_shards": 4, "medicae": 3, "intel": 3})
    assert [hero["player"] for hero in squad] == ["EZ", "Candy Peace", "Dr.Feed"]
    assert len(log) == 3
    assert all(v >= 0 for v in resources.values())


def test_tactical_resolution_is_deterministic_and_budgeted():
    slots = [
        {"player": "EZ", "assigned_hero": "sanctioned_prism_psyker"},
        {"player": "Candy Peace", "assigned_hero": "void_chaplain"},
        {"player": "Dr.Feed", "assigned_hero": "plague_surgeon"},
    ]
    directives = {
        "EZ": {"objective": 0.9, "ability": 0.85, "mobility": 0.6},
        "Candy Peace": {"survival": 0.9, "objective": 0.7},
        "Dr.Feed": {"survival": 0.95, "consumable": 0.9, "ability": 0.7},
    }
    squad_a, _, _ = rules.assemble_squad(slots, directives, {"scrap": 18, "relic_shards": 4, "medicae": 3, "intel": 3})
    squad_b = copy.deepcopy(squad_a)
    rounds_a, result_a = rules.resolve_tactical_encounter("seed", squad_a, {"noise": 2, "extraction_timer": 18})
    rounds_b, result_b = rules.resolve_tactical_encounter("seed", squad_b, {"noise": 2, "extraction_timer": 18})
    assert rounds_a == rounds_b
    assert result_a == result_b
    assert len(rounds_a) >= 3
    for round_doc in rounds_a:
        for action in round_doc["hero_actions"]:
            assert action["budget"]["main"] == 1
            assert action["budget"]["bonus"] == 1
            assert action["main_action"]["score_components"]
            assert action["bonus_action"]["score_components"]
        for hero in round_doc["squad_state"]:
            assert hero["hp"] >= 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL RULES V0.42 TESTS PASSED (%d)" % len(fns))
