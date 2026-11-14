"""
Rules Engine Subsystem Check
"""

import pytest

from game.rules_engine import RulesEngine

NOT_IMPLEMENTED = "Not Implemented"


@pytest.fixture()
def rules_engine():
    return RulesEngine()


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_verify_move():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_move():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_verify_suggest():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_suggest():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_verify_disprove():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_disprove():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_verify_accuse():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_accuse():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_verify_end_turn():
    pass


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_end_turn():
    pass
