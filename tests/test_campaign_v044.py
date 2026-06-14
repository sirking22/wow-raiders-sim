"""Acceptance tests for the v0.44 full campaign runtime."""

import copy
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import battle_v09
import campaign_v044 as campaign
import rules_v042 as rules


def _run():
    return campaign.simulate_campaign()


def test_v044_full_run_is_deterministic():
    assert _run() == _run()


def test_v044_validates_without_errors():
    run = _run()
    assert run["validation_errors"] == []
    assert campaign.validate_full_run(run) == []


def test_screen_chain_is_full_campaign_and_replayable():
    run = _run()
    screens = run["screen_payloads"]
    stages = [screen["stage"] for screen in screens]
    assert stages[0] == "hero_selection"
    assert stages[-1] == "campaign_continuity"
    assert len(screens) == len(run["replay_index"])
    assert stages.count("strategic_turn") == 3
    assert stages.count("battle_v09_round") == run["battle_run"]["result"]["rounds"]
    assert "run_highlights" in stages
    assert "camp_return" in stages
    assert all(screen["calculation_refs"] for screen in screens)
    assert all(screen["render_contract"]["source_of_truth"] for screen in screens)


def test_player_slots_and_dr_feed_are_integrated_from_battle_v09():
    run = _run()
    assert [slot["player"] for slot in run["player_slots"]] == list(rules.PLAYER_NAMES)
    assert [slot["status"] for slot in run["screen_payloads"][0]["state"]["player_slots"]] == ["unassigned", "unassigned", "unassigned"]
    assert run["battle_run"]["engine_version"] == battle_v09.ENGINE_VERSION
    assert run["battle_run"]["validation_errors"] == []
    dr_feed = next(actor for actor in run["battle_run"]["actors_initial"] if actor["id"] == "Dr.Feed")
    assert dr_feed["role"] == "medic"
    assert dr_feed["hero_id"] == "plague_surgeon"
    assert run["tactical_result"]["heroes_alive"] == ["EZ", "Candy Peace", "Dr.Feed"]


def test_ai_layers_have_director_gm_hero_and_enemy_turns():
    run = _run()
    actors = {entry["actor"] for entry in run["ai_turn_log"]}
    assert {"ai_director", "ai_gm", "ai_heroes", "ai_enemies"} <= actors
    hero_turns = [entry for entry in run["ai_turn_log"] if entry["actor"] == "ai_heroes"]
    assert hero_turns
    assert all("score_refs" in entry for entry in hero_turns)
    assert any(entry["player"] == "Dr.Feed" for entry in hero_turns)


def test_progression_camp_and_continuity_ledger_update():
    run = _run()
    ledger = run["continuity_ledger"]
    assert ledger["run_id"] == run["run_id"]
    assert len(ledger["hero_deltas"]) == 3
    assert {hero["player"] for hero in ledger["hero_deltas"]} == set(rules.PLAYER_NAMES)
    assert run["final_camp"]["resources"]["scrap"] > run["initial_camp"]["resources"]["scrap"]
    assert run["final_camp"]["morale"] > run["initial_camp"]["morale"]
    assert run["final_camp"]["facilities"]["armory_rack"]["level"] >= 2
    assert run["final_camp"]["persistent_events"]


def test_highlights_balance_audit_and_patch_contract_are_present():
    run = _run()
    assert run["highlights"]["by_actor"]["Dr.Feed"]["healing"] > 0
    assert run["balance_audit"]["status"] == "provisional_balance_trace"
    assert run["balance_audit"]["next_balance_targets"]
    contract = run["patch_contract"]
    assert contract["schema"] == "blackstar-raiders.patch-intake.v0.44"
    assert "ChatGPT Web" in contract["accepted_sources"]
    assert "Notion" in contract["accepted_sources"]
    assert "GitHub PR" in contract["accepted_sources"]
    assert "Google Drive manifest" in contract["accepted_sources"]
    assert "rules_v042_stat_formula" in contract["allowed_patch_targets"]


def test_outputs_can_be_written_to_temp_folder():
    run = _run()
    with tempfile.TemporaryDirectory() as tmp:
        paths = campaign.write_outputs(copy.deepcopy(run), root=tmp)
        assert set(paths) == {"full_run", "screens", "camp", "ledger", "patch_contract"}
        for path in paths.values():
            assert os.path.exists(path), path


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL CAMPAIGN V0.44 TESTS PASSED (%d)" % len(fns))
