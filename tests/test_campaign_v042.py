"""Acceptance tests for the v0.42 calculated campaign layer."""

import copy
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import campaign_v042 as campaign


def _run():
    return campaign.simulate_campaign()


def test_deterministic_full_run():
    assert _run() == _run()


def test_campaign_validates_without_errors():
    run = _run()
    assert campaign.validate_full_run(run) == []


def test_screen_pipeline_has_calculation_refs_and_replay_index():
    run = _run()
    screens = run["screen_payloads"]
    assert len(screens) == len(run["replay_index"])
    assert screens[0]["stage"] == "hero_selection"
    assert screens[-1]["stage"] == "camp_return"
    assert all(screen["calculation_refs"] for screen in screens)
    assert screens[0]["state"]["rules_summary"]["schema"] == "blackstar-raiders.rules.v0.42"


def test_required_stages_and_counts():
    run = _run()
    stages = [screen["stage"] for screen in run["screen_payloads"]]
    assert stages.count("strategic_turn") == 3
    assert stages.count("tactical_round") >= 3
    assert "gm_interlude" in stages
    assert "progression" in stages


def test_player_slots_dr_feed_and_unassigned_first_screen():
    run = _run()
    assert [slot["player"] for slot in run["player_slots"]] == ["EZ", "Candy Peace", "Dr.Feed"]
    first_slots = run["screen_payloads"][0]["state"]["player_slots"]
    assert [slot["status"] for slot in first_slots] == ["unassigned", "unassigned", "unassigned"]


def test_tactical_rounds_are_scored_and_budgeted():
    run = _run()
    for round_doc in run["tactical_rounds"]:
        for action in round_doc["hero_actions"]:
            assert action["budget"]["movement"] >= 1
            assert action["budget"]["main"] == 1
            assert action["budget"]["bonus"] == 1
            assert action["main_action"]["score_components"]
            assert action["bonus_action"]["score_components"]


def test_patch_contract_supports_web_notion_github_intake():
    run = _run()
    contract = run["patch_contract"]
    assert contract["schema"] == "blackstar-raiders.patch-intake.v0.42"
    assert "player_directives" in contract["allowed_patch_targets"]
    assert "asset_policy" in contract
    assert contract["current_run"]["run_id"] == run["run_id"]


def test_outputs_can_be_written_to_temp_folder():
    run = _run()
    with tempfile.TemporaryDirectory() as tmp:
        paths = campaign.write_outputs(copy.deepcopy(run), root=tmp)
        assert set(paths) == {"rules", "directives", "full_run", "screens", "camp", "patch_contract"}
        for path in paths.values():
            assert os.path.exists(path), path


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL CAMPAIGN V0.42 TESTS PASSED (%d)" % len(fns))
