import pytest

from game.game import Character, CharType, HallType, Location, LocationType, RoomType


@pytest.mark.parametrize(
    "char_type, location_name",
    [
        (CharType.MISS_SCARLET, Character.starting_location[CharType.MISS_SCARLET]),
        (CharType.COLONEL_MUSTARD, Character.starting_location[CharType.COLONEL_MUSTARD]),
        (CharType.PROFESSOR_PLUM, Character.starting_location[CharType.PROFESSOR_PLUM]),
        (CharType.MRS_PEACOCK, Character.starting_location[CharType.MRS_PEACOCK]),
        (CharType.MR_GREEN, Character.starting_location[CharType.MR_GREEN]),
        (CharType.MRS_WHITE, Character.starting_location[CharType.MRS_WHITE]),
    ]
)
def test_create_default(char_type, location_name):
    location = Location(LocationType.HALLWAY.value, location_name.value)
    character = Character(char_type.value)

    assert character.get_location() == location
    assert character.location == location
    assert character.get_location() == location
    assert character.name == char_type
    assert not character.moved_by_suggestion


@pytest.mark.parametrize(
    "hallway_name",
    [hall for hall in HallType]
)
def test_move_to_hallway(hallway_name):
    character = Character(CharType.MISS_SCARLET.value)
    location = Location(
        LocationType.HALLWAY.value,
        hallway_name.value
    )
    starting_location = Location(
        LocationType.HALLWAY.value,
        Character.starting_location[character.name].value
    )

    assert character.location == starting_location
    assert character.get_location() == starting_location

    character.move_to(location)

    assert character.location == location
    assert character.get_location() == location


@pytest.mark.parametrize(
    "room_name",
    [room for room in RoomType]
)
def test_move_to_room(room_name):
    character = Character(CharType.MISS_SCARLET.value)
    location = Location(
        LocationType.ROOM.value,
        room_name.value
    )
    starting_location = Location(
        LocationType.HALLWAY.value,
        Character.starting_location[character.name].value
    )

    assert character.location == starting_location
    assert character.get_location() == starting_location

    character.move_to(location)

    assert character.location == location
    assert character.get_location() == location



@pytest.mark.parametrize(
    "data_dict, character, location, moved",
    [
        (
            {
                "name": CharType.MISS_SCARLET.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.MISS_SCARLET].value
                },
                "moved_by_suggestion": False
            },
            Character(CharType.MISS_SCARLET.value),
            Location(LocationType.HALLWAY.value, Character.starting_location[CharType.MISS_SCARLET].value),
            False
        ),
        (
            {
                "name": CharType.COLONEL_MUSTARD.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": HallType.STUDY_HALL.value
                },
                "moved_by_suggestion": True
            },
            Character(CharType.COLONEL_MUSTARD.value),
            Location(LocationType.HALLWAY.value, HallType.STUDY_HALL.value),
            True
        ),  
        (
            {
                "name": CharType.COLONEL_MUSTARD.value,
                "location": {
                    "location_type": LocationType.ROOM.value,
                    "name": RoomType.DINING_ROOM.value,
                },
                "moved_by_suggestion": False
            },
            Character(CharType.COLONEL_MUSTARD.value),
            Location(LocationType.ROOM.value, RoomType.DINING_ROOM.value),
            False
        ),
        (
            {
                "name": CharType.MR_GREEN.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.MR_GREEN].value,
                },
                "moved_by_suggestion": True
            },
            Character(CharType.MR_GREEN.value),
            Location(
                LocationType.HALLWAY.value,
                Character.starting_location[CharType.MR_GREEN].value
            ),
            True
        ),
    ]
)
def test_load_character(data_dict, character, location, moved):
    character.location = location
    character.moved_by_suggestion = moved

    test_character = Character.from_dict(data_dict)
    
    assert test_character.name == character.name
    assert test_character.location == character.location
    assert test_character.moved_by_suggestion == character.moved_by_suggestion

@pytest.mark.parametrize(
    "character, data_dict",
    [
        (
            Character(CharType.MISS_SCARLET.value),
            {
                "name": CharType.MISS_SCARLET.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.MISS_SCARLET].value
                },
                "moved_by_suggestion": False
            }
        ),
        (
            Character(CharType.COLONEL_MUSTARD.value),
            {
                "name": CharType.COLONEL_MUSTARD.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.COLONEL_MUSTARD].value
                },
                "moved_by_suggestion": False
            }
        ),
        (
            Character(CharType.PROFESSOR_PLUM.value), 
            {
                "name": CharType.PROFESSOR_PLUM.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.PROFESSOR_PLUM].value
                },
                "moved_by_suggestion": False
            }
        ),
        (
            Character(CharType.MRS_PEACOCK.value),
            {
                "name": CharType.MRS_PEACOCK.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.MRS_PEACOCK].value
                },
                "moved_by_suggestion": False
            }
        ),
        (
            Character(CharType.MR_GREEN.value),
            {
                "name": CharType.MR_GREEN.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.MR_GREEN].value
                },
                "moved_by_suggestion": False
            }
        ),
        (
            Character(CharType.MRS_WHITE.value),
            {
                "name": CharType.MRS_WHITE.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.MRS_WHITE].value
                },
                "moved_by_suggestion": False
            }
        ),
    ]
)
def test_save_character(character, data_dict):
    out_dict = character.to_dict()

    assert len(out_dict) == len(data_dict)
    assert set(out_dict.keys()) == set(data_dict.keys())
    assert out_dict['name'] == data_dict['name']
    assert out_dict['moved_by_suggestion'] == data_dict['moved_by_suggestion']
    assert out_dict['location']['location_type'] == data_dict['location']['location_type']
    assert out_dict['location']['name'] == data_dict['location']['name']
    

@pytest.mark.parametrize(
    "data_dict",
    [
        {
                "name": CharType.MISS_SCARLET.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": Character.starting_location[CharType.MISS_SCARLET].value,
                },
                "moved_by_suggestion": False
        },
        {
                "name": CharType.COLONEL_MUSTARD.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": HallType.STUDY_HALL.value,
                },
                "moved_by_suggestion": True
        },
        {
                "name": CharType.MRS_WHITE.value,
                "location": {
                    "location_type": LocationType.ROOM.value,
                    "name": RoomType.BILLIARD_ROOM.value
                },
                "moved_by_suggestion": False
        },
        {
                "name": CharType.PROFESSOR_PLUM.value,
                "location": {
                    "location_type": LocationType.HALLWAY.value,
                    "name": HallType.CONSERVATORY_BALLROOM.value
                },
                "moved_by_suggestion": True
        },
    ]
)
def test_load_save_character(data_dict):
    out_dict = Character.from_dict(data_dict).to_dict()

    assert len(out_dict) == len(data_dict)
    assert set(out_dict.keys()) == set(data_dict.keys())
    assert out_dict['name'] == data_dict['name']
    assert out_dict['moved_by_suggestion'] == data_dict['moved_by_suggestion']
    assert out_dict['location']['location_type'] == data_dict['location']['location_type']
    assert out_dict['location']['name'] == data_dict['location']['name']
