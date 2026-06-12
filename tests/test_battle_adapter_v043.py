"""Acceptance tests for the v0.43 battle adapter contract."""

import copy
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import battle_adapter_v043 as adapter
import campaign_v042


def _report():
    return adapter.build_adapter_report()


def test_adapter_is_deterministic():
    assert _report() == _report()


def test_adapter_validates_without_errors():
    report = _report()
    assert report["validation_errors"] == []
    assert adapter.validate_adapter_report(report) == []


def test_player_mapping_preserves_names_and_unique_targets():
    report = _report()
    mappings = report["actor_contract"]["hero_mappings"]
    assert [m["player"] for m in mappings] == ["EZ", "Candy Peace", "Dr.Feed"]
    targets = [m["target_v08_actor"] for m in mappings]
    assert len(targets) == len(set(targets))


def test_dr_feed_native_medic_gap_is_explicit():
    report = _report()
    gaps = report["loss_report"]["actor_gaps"]
    assert any(gap["player"] == "Dr.Feed" and gap["severity"] == "high" for gap in gaps)
    assert report["loss_report"]["adapter_status"] == "contract_only_not_runtime_replacement"


def test_all_v042_actions_have_mapping_docs():
    report = _report()
    v042 = campaign_v042.simulate_campaign()
    expected_actions = set()
    for round_doc in v042["tactical_rounds"]:
        for hero_action in round_doc["hero_actions"]:
            expected_actions.add(hero_action["main_action"]["id"])
            expected_actions.add(hero_action["bonus_action"]["id"])
    mapped_actions = {doc["v042_action"] for doc in report["action_contract"]["action_mappings"]}
    assert expected_actions <= mapped_actions
    assert report["action_contract"]["all_v042_actions_have_mapping_doc"] is True


def test_adapter_screen_is_renderable_payload():
    report = _report()
    screen = report["adapter_screen"]
    assert screen["stage"] == "battle_adapter_review"
    assert "actor_contract" in screen["state"]
    assert "loss_report" in screen["state"]
    assert screen["render_contract"]["source_of_truth"]


def test_outputs_can_be_written_to_temp_folder():
    report = _report()
    with tempfile.TemporaryDirectory() as tmp:
        paths = adapter.write_outputs(copy.deepcopy(report), root=tmp)
        assert set(paths) == {"report", "screen"}
        for path in paths.values():
            assert os.path.exists(path), path


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("ALL BATTLE ADAPTER V0.43 TESTS PASSED (%d)" % len(fns))
