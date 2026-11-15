"""Focused tests for RulesEngine accusation and end-turn operations."""

from unittest.mock import patch

from game.game import (
    Card,
    CardType,
    CaseFile,
    Character,
    CharType,
    Game,
    GameStatus,
    Player,
    RoomType,
    WeaponType,
)
from game.rules_engine import Reason, RulesEngine


def make_game():
    players = [Player(f"p{i}", f"Player {i}") for i in range(3)]
    for player, character_type in zip(players, list(CharType)[:3], strict=True):
        player.set_character(Character(character_type.value))

    game = Game("test-game", players[0])
    for player in players[1:]:
        game.add_player(player)

    game.turn_order = [player.player_id for player in players]
    game.status = GameStatus.STARTED
    game.case_file = CaseFile(
        Card(CardType.ROOM.value, RoomType.STUDY.value),
        Card(CardType.WEAPON.value, WeaponType.ROPE.value),
        Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
    )
    return game, players


def accusation_cards():
    return (
        Card(CardType.WEAPON.value, WeaponType.ROPE.value),
        Card(CardType.ROOM.value, RoomType.STUDY.value),
        Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
    )


def test_correct_accusation_ends_game():
    game, players = make_game()
    assert RulesEngine().perform_accuse(game, players[0], *accusation_cards()) == (
        True,
        Reason.OK,
    )
    assert game.status == GameStatus.ENDED
    assert game.current_turn_index == 0
    assert not players[0].is_eliminated


def test_incorrect_accusation_eliminates_and_advances():
    game, players = make_game()
    players[0].add_card(accusation_cards()[0])
    weapon = Card(CardType.WEAPON.value, WeaponType.WRENCH.value)
    _, room, character = accusation_cards()

    assert RulesEngine().perform_accuse(game, players[0], weapon, room, character) == (
        True,
        Reason.OK,
    )
    assert players[0].is_eliminated
    assert players[0].character is not None
    assert len(players[0].hand) == 1
    assert game.get_current_player() is players[1]
    assert game.status == GameStatus.STARTED


def test_incorrect_accusation_with_one_survivor_ends_game():
    game, players = make_game()
    players[2].eliminate()
    weapon = Card(CardType.WEAPON.value, WeaponType.WRENCH.value)
    _, room, character = accusation_cards()

    assert RulesEngine().perform_accuse(game, players[0], weapon, room, character) == (
        True,
        Reason.OK,
    )
    assert game.status == GameStatus.ENDED
    assert players[0].is_eliminated
    assert not players[1].is_eliminated


def test_incorrect_accusation_when_all_eliminated_ends_game():
    game, players = make_game()
    players[1].eliminate()
    players[2].eliminate()
    weapon = Card(CardType.WEAPON.value, WeaponType.WRENCH.value)
    _, room, character = accusation_cards()

    assert RulesEngine().perform_accuse(game, players[0], weapon, room, character) == (
        True,
        Reason.OK,
    )
    assert game.status == GameStatus.ENDED
    assert all(player.is_eliminated for player in players)


def test_accusation_rejects_wrong_card_types():
    game, players = make_game()
    weapon, room, character = accusation_cards()
    assert RulesEngine().validate_accuse(game, players[0], room, weapon, character) == (
        False,
        Reason.INVALID_ACCUSATION_CARDS,
    )
    assert game.status == GameStatus.STARTED


def test_accusation_rejects_missing_case_file():
    game, players = make_game()
    game.case_file = None
    assert RulesEngine().validate_accuse(game, players[0], *accusation_cards()) == (
        False,
        Reason.CASE_FILE_MISSING,
    )


def test_accusation_rejected_during_disprove_round():
    game, players = make_game()
    game.suggestion_round = True
    game.disprove_turn_index = 1
    assert RulesEngine().validate_accuse(game, players[1], *accusation_cards()) == (
        False,
        Reason.ACCUSE_DURING_SUGGEST,
    )


def test_accusation_rejects_eliminated_player():
    game, players = make_game()
    players[0].eliminate()
    assert RulesEngine().validate_accuse(game, players[0], *accusation_cards()) == (
        False,
        Reason.PLAYER_ELIMINATED,
    )


def test_end_turn_advances_and_resets_movement():
    game, players = make_game()
    players[0].character.moved_this_turn = True
    assert RulesEngine().perform_end_turn(game, players[0]) == (True, Reason.OK)
    assert game.get_current_player() is players[1]
    assert players[0].character.moved_this_turn is False


def test_end_turn_rejects_other_player():
    game, players = make_game()
    assert RulesEngine().perform_end_turn(game, players[1]) == (
        False,
        Reason.NOT_CURR_PLAYER_MSG,
    )
    assert game.current_turn_index == 0


def test_end_turn_rejected_during_disprove_round():
    game, players = make_game()
    game.suggestion_round = True
    game.disprove_turn_index = 1
    assert RulesEngine().perform_end_turn(game, players[1]) == (
        False,
        Reason.END_TURN_DURING_SUGGEST,
    )
    assert game.current_turn_index == 0


def test_end_turn_when_advance_turn_returns_none_ends_game():
    game, players = make_game()
    with patch.object(game, "advance_turn", return_value=None) as advance_turn:
        assert RulesEngine().perform_end_turn(game, players[0]) == (True, Reason.OK)
    advance_turn.assert_called_once_with()
    assert game.status == GameStatus.ENDED
