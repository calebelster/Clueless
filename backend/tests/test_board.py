import pytest

from game.game import (
    CharType,
    Character,
    HallType, 
    Location, 
    Board, 
    LocationType,
    RoomType
)


# TODO
def test_hallway_neighbors():
    pass

# TODO
def test_room_neighbors():
    pass


@pytest.mark.parametrize(
    "data_dict, location",
    [
        (
            {
                "location_type": LocationType.HALLWAY.value,
                "name": HallType.BALLROOM_KITCHEN.value
            },
            Location(
                LocationType.HALLWAY.value,
                HallType.BALLROOM_KITCHEN.value
            )
        ),
        (
            {
                "location_type": LocationType.ROOM.value,
                "name": RoomType.LOUNGE.value
            },
            Location(
                LocationType.ROOM.value,
                RoomType.LOUNGE.value
            )
        )
    ]
)
def test_load_location(data_dict, location):
    assert Location.from_dict(data_dict) == location


@pytest.mark.parametrize(
    "data_dict, location",
    [
        (
            {
                "location_type": LocationType.HALLWAY.value,
                "name": HallType.BALLROOM_KITCHEN.value
            },
            Location(
                LocationType.HALLWAY.value,
                HallType.BALLROOM_KITCHEN.value
            )
        ),
        (
            {
                "location_type": LocationType.ROOM.value,
                "name": RoomType.LOUNGE.value
            },
            Location(
                LocationType.ROOM.value,
                RoomType.LOUNGE.value
            )
        )
    ]
)
def test_save_location(data_dict, location):
    out_dict = location.to_dict()

    assert len(out_dict) == len(data_dict)
    assert set(out_dict.keys()) == set(data_dict.keys())
    assert out_dict["location_type"] == data_dict["location_type"]
    assert out_dict["name"] == data_dict["name"]


@pytest.mark.parametrize(
    "data_dict",
    [
        {
            "location_type": LocationType.HALLWAY.value,
            "name": HallType.BALLROOM_KITCHEN.value
        },  
        {
            "location_type": LocationType.ROOM.value,
            "name": RoomType.LOUNGE.value
        },   
    ]
)
def test_load_save_location(data_dict):
    out_dict = Location.from_dict(data_dict).to_dict()

    assert len(out_dict) == len(data_dict)
    assert set(out_dict.keys()) == set(data_dict.keys())
    assert out_dict["location_type"] == data_dict["location_type"]
    assert out_dict["name"] == data_dict["name"]


@pytest.mark.parametrize(
    "location_name",
    [
        (HallType.BALLROOM_KITCHEN.value),
        (HallType.STUDY_HALL.value),
        (HallType.LIBRARY_BILLIARD_ROOM.value)
    ]
)
def test_board_hallway_occcupied(location_name):
    location = Location(LocationType.HALLWAY.value, location_name)
    character1 = Character(CharType.COLONEL_MUSTARD.value)
    character2 = Character(CharType.MISS_SCARLET.value)
    board = Board()

    assert not board.is_hallway_occupied(location, [character1, character2])

    character1.move_to(location)

    assert board.is_hallway_occupied(location, [character1])
    assert not board.is_hallway_occupied(location, [character2])
    assert board.is_hallway_occupied(location, [character1, character2])
