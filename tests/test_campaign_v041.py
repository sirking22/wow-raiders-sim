"""Acceptance tests for the v0.41 full campaign layer.

Run:
    python tests/test_campaign_v041.py
"""

import copy
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import campaign_v041 as campaign


def _run():
    return campaign.simulate_campaign()


def test_deterministic_full_run():
    a = _run()
    b = _run()
    assert a == b


def test_screen_stages_exist_and_are_ordered():
    run = _run()
    errors = campaign.validate_full_run(run)
    assert errors == [], errors
    stages = [screen["stage"] for screen in run["screen_payloads"]]
    assert stages[0] == "hero_selection"
    assert stages[-1] == "camp_return"
    assert stages.count("tactical_round") == 3


def test_required_player_slots_and_dr_feed_name():
    run = _run()
    assert [slot["player"] for slot in run["player_slots"]] == ["EZ", "Candy Peace", "Dr.Feed"]
    first = run["screen_payloads"][0]
    assert first["stage"] == "hero_selection"
    assert [slot["status"] for slot in first["state"]["player_slots"]] == ["unassigned", "unassigned", "unassigned"]


def test_setting_profile_is_hard_far_future_reference():
    run = _run()
    profile = run["setting_profile"]
    assert profile["production_mode"] == "blackstar_raiders_original_safe"
    assert "WH40" in profile["reference_target"]
    assert "no-soft-fantasy" in profile["tone"]


def test_no_negative_hp_and_progression_changes_camp():
    run = _run()
    for round_doc in run["tactical_rounds"]:
        for hero in round_doc["squad_state"]:
            assert hero["hp"] >= 0
    assert run["final_camp"]["resources"]["scrap"] > run["initial_camp"]["resources"]["scrap"]
    assert len(run["final_camp"]["persistent_events"]) == 1


def test_player_directives_are_included_for_patchability():
    run = _run()
    directives = run["player_directives"]
    assert directives["EZ"]["ability_bias"] == "control_priority"
    assert directives["Candy Peace"]["ability_bias"] == "guard_allies"
    assert directives["Dr.Feed"]["ability_bias"] == "heal_early"


def test_outputs_can_be_written_to_temp_folder():
    run = _run()
    with tempfile.TemporaryDirectory() as tmp:
        paths = campaign.write_outputs(copy.deepcopy(run), root=tmp)
        for path in paths.values():
            assert os.path.exists(path), path


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL CAMPAIGN V0.41 TESTS PASSED (%d)" % len(fns))
