"""Acceptance tests for BattleV09 external roster runtime."""

import copy
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import battle_v09 as battle
import rules_v042 as rules


def _run():
    return battle.build_battle_run()


def test_battle_v09_is_deterministic():
    assert _run() == _run()


def test_battle_v09_validates_without_errors():
    run = _run()
    assert run["validation_errors"] == []
    assert battle.validate_battle_run(run) == []


def test_external_roster_preserves_players_and_native_dr_feed():
    run = _run()
    heroes = [actor for actor in run["actors_initial"] if actor["team"] == "heroes"]
    assert [hero["id"] for hero in heroes] == list(rules.PLAYER_NAMES)
    dr_feed = next(hero for hero in heroes if hero["id"] == "Dr.Feed")
    assert dr_feed["role"] == "medic"
    assert dr_feed["hero_id"] == "plague_surgeon"


def test_dr_feed_performs_real_support_actions():
    run = _run()
    dr_feed_actions = [action for action in run["action_log"] if action.get("actor") == "Dr.Feed"]
    assert dr_feed_actions
    assert any(action["main_action"]["id"] == "stabilize_ally" for action in dr_feed_actions)
    assert any(action["bonus_action"]["id"] == "field_injector" for action in dr_feed_actions)
    heal_effects = [effect for action in dr_feed_actions for effect in action["effects"] if effect["type"] == "heal"]
    assert heal_effects
    assert any(effect["after"] > effect["before"] for effect in heal_effects)


def test_action_and_movement_budgets_are_enforced():
    run = _run()
    derived_movement = {
        actor["id"]: actor["derived"]["movement"]
        for actor in run["actors_initial"]
        if actor["team"] == "heroes"
    }
    for action in run["action_log"]:
        if action["type"] != "hero_turn":
            continue
        assert action["budget"]["main"] == 1
        assert action["budget"]["bonus"] == 1
        assert action["movement"]["cost"] <= action["movement"]["budget"]
        assert action["movement"]["cost"] <= derived_movement[action["actor"]]
        assert action["main_action"]["score_components"]
        assert action["bonus_action"]["score_components"]
        _assert_adjacent_path(action["movement"]["path"])


def test_frames_clocks_and_positions_are_consistent():
    run = _run()
    assert len(run["frames"]) == run["result"]["rounds"] + 1
    assert len(run["screen_payloads"]) == run["result"]["rounds"] + 2
    for key in ("noise", "threat", "doom", "extraction_timer"):
        assert key in run["result"]["clocks"]
    for frame in run["frames"]:
        live_positions = set()
        for actor in frame["actors"]:
            assert battle._cell_in_bounds(actor["position"])
            assert 0 <= actor["hp"] <= actor["max_hp"]
            if actor["hp"] > 0:
                assert actor["position"] not in live_positions
                live_positions.add(actor["position"])


def test_outputs_can_be_written_to_temp_folder():
    run = _run()
    with tempfile.TemporaryDirectory() as tmp:
        paths = battle.write_outputs(copy.deepcopy(run), root=tmp)
        assert set(paths) == {"run", "screens"}
        for path in paths.values():
            assert os.path.exists(path), path


def _assert_adjacent_path(path):
    for cell in path:
        assert battle._cell_in_bounds(cell)
    for left, right in zip(path, path[1:]):
        assert battle._distance(left, right) == 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL BATTLE V0.9 TESTS PASSED (%d)" % len(fns))
