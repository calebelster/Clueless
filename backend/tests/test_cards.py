import pytest


from game.game import (
    Card,
    CardType,
    CaseFile,
    DECK,
    CharType, WeaponType, RoomType
)


def test_all_cards():
    weapon_gt_len = len(DECK[CardType.WEAPON])
    room_gt_len = len(DECK[CardType.ROOM])
    char_gt_len = len(DECK[CardType.CHARACTER])
    deck_gt_len = weapon_gt_len + room_gt_len + char_gt_len
    
    deck = Card.all_cards()

    # Correct number of each card type
    assert len(deck) == deck_gt_len
    assert len([card for card in deck if card.card_type == CardType.WEAPON]) == weapon_gt_len
    assert len([card for card in deck if card.card_type == CardType.ROOM]) == room_gt_len
    assert len([card for card in deck if card.card_type == CardType.CHARACTER]) == char_gt_len

    # All unique cards
    assert len(deck) == len(set(deck))

    for card in deck:
        match card.card_type:
            case CardType.WEAPON:
                pass
            case CardType.ROOM:
                pass
            case CardType.CHARACTER:
                pass
            case _:
                raise AssertionError(f"Invalid {card.card_type=}")


@pytest.mark.parametrize(
    "card_type, name",
    [
        (CardType.ROOM.value, CharType.COLONEL_MUSTARD.value),
        (CardType.ROOM.value, "invalid_string"),
        ("abcdefg", "mrs.white"),
        ("invalid_string", "invalid_string"),
        (CardType.WEAPON.value, RoomType.BILLIARD_ROOM.value),
        (CardType.WEAPON.value, "roperope"),
        (CardType.CHARACTER.value, WeaponType.LEAD_PIPE.value),
        (CardType.CHARACTER.value, "mr. white")
    ]
)
def test_invalid_card_create(card_type, name):
    with pytest.raises(ValueError):
        Card(card_type, name)


@pytest.mark.parametrize(
    "card_type, name",
    [
        (CardType.ROOM.value, RoomType.BILLIARD_ROOM.value),
        (CardType.ROOM.value, RoomType.DINING_ROOM.value),
        (CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
        (CardType.CHARACTER.value, CharType.PROFESSOR_PLUM.value),
        (CardType.WEAPON.value, WeaponType.WRENCH.value),
        (CardType.WEAPON.value, WeaponType.REVOLVER.value)
    ]
)
def test_valid_card_create(card_type, name):
    card = Card(card_type, name)
    assert isinstance(card, Card)
    assert card.card_type.value == card_type
    assert card.name.value == name


@pytest.mark.parametrize(
    "card_type, name",
    [
        (CardType.WEAPON.value, WeaponType.WRENCH.value),
        (CardType.CHARACTER.value, CharType.MRS_WHITE.value),
        (CardType.ROOM.value, RoomType.CONSERVATORY.value),
    ]
)
def test_card_equality(card_type, name):
    assert Card(card_type, name) == Card(card_type, name)


@pytest.mark.parametrize(
    "card_type1, name1, card_type2, name2",
    [
        (CardType.WEAPON.value, WeaponType.WRENCH.value, CardType.WEAPON.value, WeaponType.REVOLVER.value),
        (CardType.CHARACTER.value, CharType.MRS_WHITE.value, CardType.WEAPON.value, WeaponType.WRENCH.value),
        (CardType.ROOM.value, RoomType.CONSERVATORY.value, CardType.CHARACTER.value, CharType.MISS_SCARLET.value),
    ]
)
def test_card_inequality(card_type1, name1, card_type2, name2):
    assert Card(card_type1, name1) != Card(card_type2, name2)


@pytest.mark.parametrize(
    "card, data_dict",
    [
        (
            Card(CardType.WEAPON.value, WeaponType.WRENCH.value), 
            {"card_type": CardType.WEAPON.value, "name": WeaponType.WRENCH.value}
        ),
        (
            Card(CardType.CHARACTER.value, CharType.MISS_SCARLET.value), 
            {"card_type": CardType.CHARACTER.value, "name": CharType.MISS_SCARLET.value}
        ),
        (
            Card(CardType.ROOM.value, RoomType.LOUNGE.value), 
            {"card_type": CardType.ROOM.value, "name": RoomType.LOUNGE.value}
        ),
    ]
)
def test_save_card(card, data_dict):
    out_dict = card.to_dict()
    assert set(data_dict.keys()) == set(out_dict.keys())
    for key, value in data_dict.items():
        assert out_dict[key] == value


@pytest.mark.parametrize(
    "data_dict, card",
    [
        (
            {"card_type": CardType.WEAPON.value, "name": WeaponType.CANDLESTICK.value},
            Card(CardType.WEAPON.value, WeaponType.CANDLESTICK.value)
        ),
        (
            {"card_type": CardType.CHARACTER.value, "name": CharType.MR_GREEN.value},
            Card(CardType.CHARACTER.value, CharType.MR_GREEN.value), 
        ),
        (
            {"card_type": CardType.ROOM.value, "name": RoomType.BALLROOM.value},
            Card(CardType.ROOM.value, RoomType.BALLROOM.value)
        ),
    ]
)
def test_load_card(data_dict, card):
    assert Card.from_dict(data_dict) == card


@pytest.mark.parametrize(
    "data_dict",
    [
        {"card_type": CardType.WEAPON.value, "name": WeaponType.ROPE.value},
        {"card_type": CardType.CHARACTER.value, "name": CharType.MRS_PEACOCK.value},
        {"card_type": CardType.ROOM.value, "name": RoomType.KITCHEN.value}
    ]
)
def test_load_save_card(data_dict):
    out_dict = Card.from_dict(data_dict).to_dict()
    assert set(data_dict.keys()) == set(out_dict.keys())
    for key, value in data_dict.items():
        assert out_dict[key] == value


@pytest.mark.parametrize(
    "room, weapon, character",
    [
        (
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            Card(CardType.CHARACTER.value, CharType.COLONEL_MUSTARD.value),
        ),
        (
            Card(CardType.ROOM.value, RoomType.CONSERVATORY.value),
            Card(CardType.ROOM.value, RoomType.CONSERVATORY.value),
            Card(CardType.CHARACTER.value, CharType.COLONEL_MUSTARD.value),
        ),
        (
            Card(CardType.ROOM.value, RoomType.CONSERVATORY.value),
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
            Card(CardType.WEAPON.value, WeaponType.ROPE.value),
        )

    ]
)
def test_create_invalid_case_file(room, weapon, character):
    with pytest.raises(ValueError):
        CaseFile(
            room=room,
            weapon=weapon,
            character=character
        )


@pytest.mark.parametrize(
    "data_dict, weapon, room, character",
    [
        (
            {
                CardType.WEAPON.value: {
                    "card_type": CardType.WEAPON.value,
                    "name": WeaponType.CANDLESTICK.value
                },
                CardType.ROOM.value: {
                    "card_type": CardType.ROOM.value,
                    "name": RoomType.HALL.value
                },
                CardType.CHARACTER.value: {
                    "card_type": CardType.CHARACTER.value,
                    "name": CharType.MR_GREEN.value
                },
            },
            Card(
                CardType.WEAPON.value,
                WeaponType.CANDLESTICK.value
            ),
            Card(
                CardType.ROOM.value,
                RoomType.HALL.value,
            ),
            Card(
                CardType.CHARACTER.value,
                CharType.MR_GREEN.value
            )
        )
    ]
)
def test_load_case_file(data_dict, weapon, room, character):
    case_file = CaseFile.from_dict(data_dict)
    assert case_file.weapon == weapon
    assert case_file.room == room
    assert case_file.character == character


@pytest.mark.parametrize(
    "case_file, data_dict",
    [
        (
            CaseFile(
                weapon=Card(
                    CardType.WEAPON.value,
                    WeaponType.CANDLESTICK.value
                ),
                room=Card(
                    CardType.ROOM.value,
                    RoomType.HALL.value
                ),
                character=Card(
                    CardType.CHARACTER.value,
                    CharType.MR_GREEN.value
                )
            ),
            {
                CardType.WEAPON.value: {
                    "card_type": CardType.WEAPON.value,
                    "name": WeaponType.CANDLESTICK.value
                },
                CardType.ROOM.value: {
                    "card_type": CardType.ROOM.value,
                    "name": RoomType.HALL.value
                },
                CardType.CHARACTER.value: {
                    "card_type": CardType.CHARACTER.value,
                    "name": CharType.MR_GREEN.value
                },
            }
        )
    ]
)
def test_save_case_file(case_file, data_dict):
    out_dict = case_file.to_dict()
    assert set(data_dict.keys()) == set(out_dict.keys())
    for category, card_dict in data_dict.items():
        assert set(data_dict[category].keys()) == set(card_dict.keys())
        for field_name, field in card_dict.items():
            assert out_dict[category][field_name] == field


@pytest.mark.parametrize(
    "data_dict",
    [
        {
            "weapon": {
                "card_type": CardType.WEAPON.value,
                "name": WeaponType.CANDLESTICK.value
            },
            "room": {
                "card_type": CardType.ROOM.value,
                "name": RoomType.HALL.value
            },
            "character": {
                "card_type": CardType.CHARACTER.value,
                "name": CharType.MR_GREEN.value
            }
        }
    ]
)
def test_load_save_case_file(data_dict):
    out_dict = CaseFile.from_dict(data_dict).to_dict()
    assert set(data_dict.keys()) == set(out_dict.keys())
    for category, card_dict in data_dict.items():
        assert set(data_dict[category].keys()) == set(card_dict.keys())
        for field_name, field in card_dict.items():
            assert out_dict[category][field_name] == field


def test_accuse():
    # Test equality
    room = Card(CardType.ROOM.value, RoomType.DINING_ROOM.value)
    weapon = Card(CardType.WEAPON.value, WeaponType.KNIFE.value)
    character = Card(CardType.CHARACTER.value, CharType.MR_GREEN.value)

    case = CaseFile(room, weapon, character)

    # Test equality
    assert case.accuse(room, weapon, character)

    # Test inequality
    wrong_room = Card(CardType.ROOM.value, RoomType.HALL.value)
    wrong_weapon = Card(CardType.WEAPON.value, WeaponType.REVOLVER.value)
    wrong_character = Card(CardType.CHARACTER.value, CharType.MRS_WHITE.value)

    assert not case.accuse(wrong_room, weapon, character)
    assert not case.accuse(room, wrong_weapon, character)
    assert not case.accuse(room, weapon, wrong_character)
    assert not case.accuse(wrong_room, wrong_weapon, wrong_character)
