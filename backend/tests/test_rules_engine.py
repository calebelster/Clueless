"""
Rules Engine Subsystem Check
"""

import pytest

from game import rules_engine


def test_reject_bad_action():
    game, player, payload = {}, {}, {}
    bad_action = "BADCMD_REQ"

    success, reason = rules_engine.execute(bad_action, game, player, payload)
    assert not success
    assert bad_action in reason
    assert "not a valid player action" in reason


@pytest.mark.parametrize(
    "action, expected",
    [
        ("MOVE_REQ", True),
        ("SUGGEST_REQ", True),
        ("DISPROVE_REQ", True),
        ("ACCUSE_REQ", True),
        ("END_TURN_REQ", True),
    ],
)
def test_validated_good_action(action, expected):
    game, player, payload = {}, {}, {}
    success, reason = rules_engine.execute(action, game, player, payload)
    assert success == expected
    assert reason == f"{action} valid"
