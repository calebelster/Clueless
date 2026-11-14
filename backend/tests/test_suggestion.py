import pytest

from game.game import (
    Card,
    CardType,
    CharType,
    Player,
    Suggestion,
    WeaponType,
    RoomType
)


@pytest.fixture
def player():
    return Player(
        "1234",
        "1234-display"
    )


@pytest.mark.parametrize(
    "weapon, room, character",
    [
        (
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            Card(CardType.ROOM.value, RoomType.HALL.value),
            Card(CardType.CHARACTER.value, CharType.COLONEL_MUSTARD.value),
        ),
        (
            Card(CardType.WEAPON.value, WeaponType.REVOLVER.value),
            Card(CardType.ROOM.value, RoomType.CONSERVATORY.value),
            Card(CardType.CHARACTER.value, CharType.PROFESSOR_PLUM.value),
        ),
        (
            Card(CardType.WEAPON.value, WeaponType.LEAD_PIPE.value),
            Card(CardType.ROOM.value, RoomType.KITCHEN.value),
            Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
        ),
    ]
)
def test_create_suggestion(player, weapon, room, character):
    suggestion = Suggestion(player, weapon, room, character)
    assert suggestion.suggester == player.player_id
    assert suggestion.room == room
    assert suggestion.weapon == weapon
    assert suggestion.character == character
    assert suggestion.disprover is None
    assert suggestion.revealed_card is None


@pytest.mark.parametrize(
    "weapon, room, character, card, disprover",
    [
        (
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            "disprover"
        ),
        (
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            "disprover"
        ),
        (
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            "disprover"
        )
    ]
)
def test_suggestion_record_disprove(player, weapon, room, character, card, disprover):
    suggestion = Suggestion(player, weapon, room, character)
    disproving_player = Player(disprover, disprover)

    suggestion.record_disproval(disproving_player, card)
    assert suggestion.disprover == disprover
    assert suggestion.revealed_card == card


@pytest.mark.parametrize(
    "weapon, room, character, card, disprover",
    [
        (
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            Card(CardType.WEAPON.value, WeaponType.REVOLVER.value),
            "disprover"
        ),
        (
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            Card(CardType.ROOM.value, RoomType.BILLIARD_ROOM.value),
            "disprover"
        ),
        (
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
            "disprover"
        )
    ]
)
def test_suggestion_record_disprove_fail(player, weapon, room, character, card, disprover):
    suggestion = Suggestion(player, weapon, room, character)
    disproving_player = Player(disprover, disprover)
    with pytest.raises(ValueError):
        suggestion.record_disproval(disproving_player, card)


@pytest.mark.parametrize(
    "weapon, room, character, disprover, revealed_card, data_dict",
    [
        (
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            None,
            None,
            {
                "suggester": "1234",
                "weapon": Card(CardType.WEAPON.value, WeaponType.KNIFE.value).to_dict(),
                "room": Card(CardType.ROOM.value, RoomType.BALLROOM.value).to_dict(),
                "character": Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value).to_dict(),
                "disprover": None,
                "revealed_card": None
            }
        ),
        (
            Card(CardType.WEAPON.value, WeaponType.CANDLESTICK.value),
            Card(CardType.ROOM.value, RoomType.LOUNGE.value),
            Card(CardType.CHARACTER.value, CharType.MR_GREEN.value),
            "disprover",
            Card(CardType.WEAPON.value, WeaponType.CANDLESTICK.value),
            {
                "suggester": "1234",
                "weapon": Card(CardType.WEAPON.value, WeaponType.CANDLESTICK.value).to_dict(),
                "room": Card(CardType.ROOM.value, RoomType.LOUNGE.value).to_dict(),
                "character": Card(CardType.CHARACTER.value, CharType.MR_GREEN.value).to_dict(),
                "disprover": "disprover",
                "revealed_card": Card(CardType.WEAPON.value, WeaponType.CANDLESTICK.value).to_dict()
            }
        )
    ]
)
def test_save_suggestion(player, weapon, room, character, disprover, revealed_card, data_dict):
    suggestion = Suggestion(player, weapon, room, character)
    suggestion.disprover = disprover
    suggestion.revealed_card = revealed_card

    out_dict = suggestion.to_dict()
    assert len(out_dict) == len(data_dict)
    assert set(out_dict.keys()) == set(data_dict.keys())
    assert out_dict['suggester'] == data_dict['suggester']
    assert out_dict['weapon'] == data_dict['weapon']
    assert out_dict['room'] == data_dict['room']
    assert out_dict['character'] == data_dict['character']
    if data_dict['disprover']:
        assert out_dict['disprover'] == data_dict['disprover']
        assert Card.from_dict(out_dict['revealed_card']) == Card.from_dict(data_dict['revealed_card'])
    else:
        assert out_dict['disprover'] == data_dict['disprover']
        assert out_dict['revealed_card'] == data_dict['revealed_card']




@pytest.mark.parametrize(
    "data_dict, weapon, room, character, disprover, revealed_card",
    [
        (   
            {
                "suggester": "1234",
                "weapon": Card(CardType.WEAPON.value, WeaponType.KNIFE.value).to_dict(),
                "room": Card(CardType.ROOM.value, RoomType.BALLROOM.value).to_dict(),
                "character": Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value).to_dict(),
                "disprover": None,
                "revealed_card": None
            },
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            None,
            None
        ),
        (   
            {
                "suggester": "1234",
                "weapon": Card(CardType.WEAPON.value, WeaponType.KNIFE.value).to_dict(),
                "room": Card(CardType.ROOM.value, RoomType.BALLROOM.value).to_dict(),
                "character": Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value).to_dict(),
                "disprover": "disprover",
                "revealed_card": Card(CardType.WEAPON.value, WeaponType.KNIFE.value).to_dict()
            },
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value),
            Card(CardType.ROOM.value, RoomType.BALLROOM.value),
            Card(CardType.CHARACTER.value, CharType.MRS_PEACOCK.value),
            "disprover",
            Card(CardType.WEAPON.value, WeaponType.KNIFE.value)
        ),
    ]
)
def test_load_suggestion(player, data_dict, weapon, room, character, disprover, revealed_card):
    suggestion = Suggestion(player, weapon, room, character)
    suggestion.disprover = disprover
    suggestion.revealed_card = revealed_card

    out_suggestion = Suggestion.from_dict(data_dict)

    assert out_suggestion.suggester == suggestion.suggester
    assert out_suggestion.weapon == suggestion.weapon
    assert out_suggestion.character == suggestion.character
    assert out_suggestion.disprover == suggestion.disprover
    assert out_suggestion.revealed_card == suggestion.revealed_card


@pytest.mark.parametrize(
    "data_dict",
    [
        {
            "suggester": "1234",
            "weapon": Card(CardType.WEAPON.value, WeaponType.KNIFE.value).to_dict(),
            "room": Card(CardType.ROOM.value, RoomType.DINING_ROOM.value).to_dict(),
            "character": Card(CardType.CHARACTER.value, CharType.MR_GREEN.value).to_dict(),
            "disprover": None,
            "revealed_card": None
        },
        {
            "suggester": "1234",
            "weapon": Card(CardType.WEAPON.value, WeaponType.KNIFE.value).to_dict(),
            "room": Card(CardType.ROOM.value, RoomType.DINING_ROOM.value).to_dict(),
            "character": Card(CardType.CHARACTER.value, CharType.MR_GREEN.value).to_dict(),
            "disprover": "5678",
            "revealed_card": Card(CardType.CHARACTER.value, CharType.MR_GREEN.value).to_dict()
        }
    ]
)
def test_load_save_suggestion(data_dict):
    out_dict = Suggestion.from_dict(data_dict).to_dict()
    assert len(out_dict) == len(data_dict)
    assert set(out_dict.keys()) == set(data_dict.keys())
    assert out_dict['suggester'] == data_dict['suggester']
    assert Card.from_dict(out_dict['weapon']) == Card.from_dict(data_dict['weapon'])
    assert Card.from_dict(out_dict['room']) == Card.from_dict(data_dict['room'])
    assert Card.from_dict(out_dict['character']) == Card.from_dict(data_dict['character'])
    if data_dict['disprover']:
        assert out_dict['disprover'] == data_dict['disprover']
        assert Card.from_dict(out_dict['revealed_card']) == Card.from_dict(data_dict['revealed_card'])
    else:
        assert out_dict['disprover'] == data_dict['disprover']
        assert out_dict['revealed_card'] == data_dict['revealed_card']
