from datetime import datetime, timezone
from enum import Enum
from typing import Any


class GameStatus(Enum):
    LOBBY = "LOBBY"
    STARTED = "STARTED"
    ENDED = "ENDED"


class CardType(Enum):
    WEAPON = "weapon"
    ROOM = "room"
    CHARACTER = "character"


class WeaponType(Enum):
    ROPE = "rope"
    LEAD_PIPE = "lead pipe"
    KNIFE = "knife"
    WRENCH = "wrench"
    CANDLESTICK = "candlestick"
    REVOLVER = "revolver"


class RoomType(Enum):
    STUDY = "study"
    HALL = "hall"
    LOUNGE = "lounge"
    LIBRARY = "library"
    BILLIARD_ROOM = "billiard room"
    DINING_ROOM = "dining room"
    CONSERVATORY = "conservatory"
    BALLROOM = "ballroom"
    KITCHEN = "kitchen"


class CharType(Enum):
    MISS_SCARLET = "miss scarlett"
    COLONEL_MUSTARD = "colonel mustard"
    PROFESSOR_PLUM = "professor plum"
    MRS_PEACOCK = "mrs. peacock"
    MR_GREEN = "mr. green"
    MRS_WHITE = "mrs. white"


class HallType(Enum):
    STUDY_HALL = "study-hall"
    HALL_LOUNGE = "hall-lounge"
    STUDY_LIBRARY = "study-library"
    HALL_BILLIARD_ROOM = "hall-billiard_room"
    LOUNGE_DINING_ROOM = "lounge-dining_room"
    LIBRARY_BILLIARD_ROOM = "library-billiard_room"
    BILLIARD_ROOM_DINING_ROOM = "billiard_room-dining_room"
    LIBRARY_CONSERVATORY = "library-conservatory"
    BILLIARD_ROOM_BALLROOM = "billiard_room-ballroom"
    DINING_ROOM_KITCHEN = "dining_room-kitchen"
    CONSERVATORY_BALLROOM = "conservatory-ballroom"
    BALLROOM_KITCHEN = "ballroom-kitchen"


class LocationType(Enum):
    ROOM = "room"
    HALLWAY = "hall"


DECK = {
    CardType.WEAPON: [weapon for weapon in WeaponType],
    CardType.ROOM: [room for room in RoomType],
    CardType.CHARACTER: [character for character in CharType]
}


class Card:
    def __init__(self, card_type: str, name: str):
        self.card_type = CardType(card_type)
        match self.card_type:
            case CardType.ROOM:
                self.name = RoomType(name)
            case CardType.WEAPON:
                self.name = WeaponType(name)
            case CardType.CHARACTER:
                self.name = CharType(name)

    @classmethod
    def all_cards(cls) -> list[Card]:
        cards = []
        for card_type, name_list in DECK.items():
            for name in name_list:
                cards.append(Card(card_type.value, name))
        return cards

    @classmethod
    def from_dict(cls, data_dict):
        return Card(
            data_dict["card_type"],
            data_dict["name"]
        )

    def _identity(self):
        return (self.card_type, self.name)

    def __eq__(self, obj):
        if not isinstance(obj, Card):
            return NotImplemented
        return self._identity() == obj._identity()

    def __hash__(self):
        return hash(self._identity)

    def to_dict(self) -> dict[str, str]:
        return {
            "card_type": self.card_type.value,
            "name": self.name.value
        }


class CaseFile:
    def __init__(self, room: Card, weapon: Card, character: Card):
        if room.card_type != CardType.ROOM:
            raise ValueError(f"Invalid room card, received a {room.card_type.value} card")

        if weapon.card_type != CardType.WEAPON:
            raise ValueError(f"Invalid weapon card, received a {weapon.card_type.value} card")

        if character.card_type != CardType.CHARACTER:
            raise ValueError(f"Invalid character card, received a {character.card_type.value} card")

        self.room = room
        self.weapon = weapon
        self.character = character

    @classmethod
    def from_dict(cls, data_dict):
        return CaseFile(
            room=Card.from_dict(data_dict["room"]),
            weapon=Card.from_dict(data_dict["weapon"]),
            character=Card.from_dict(data_dict["character"])
        )

    def accuse(self, room: Card, weapon: Card, character: Card) -> bool:
        return room == self.room and \
                weapon == self.weapon and \
                character == self.character

    def to_dict(self) -> dict[str, dict[str, str]]:
        return {
            "room": self.room.to_dict(),
            "weapon": self.weapon.to_dict(),
            "character": self.character.to_dict()
        }


class Location:
    secret_passages = {
        RoomType.STUDY: RoomType.KITCHEN,
        RoomType.KITCHEN: RoomType.STUDY,
        RoomType.LOUNGE: RoomType.CONSERVATORY,
        RoomType.CONSERVATORY: RoomType.LOUNGE,
        RoomType.HALL: None,
        RoomType.LIBRARY: None,
        RoomType.BILLIARD_ROOM: None,
        RoomType.DINING_ROOM: None,
        RoomType.BALLROOM: None
    }

    neighbors = {
        RoomType.STUDY: [
            HallType.STUDY_HALL, 
            HallType.STUDY_LIBRARY
        ],
        RoomType.KITCHEN: [
            HallType.BALLROOM_KITCHEN,
            HallType.DINING_ROOM_KITCHEN
        ],
        RoomType.LOUNGE: [
            HallType.HALL_LOUNGE,
            HallType.LOUNGE_DINING_ROOM
        ],
        RoomType.CONSERVATORY: [
            HallType.LIBRARY_CONSERVATORY,
            HallType.CONSERVATORY_BALLROOM
        ],
        RoomType.HALL: [
            HallType.STUDY_HALL,
            HallType.HALL_BILLIARD_ROOM,
            HallType.HALL_LOUNGE
        ],
        RoomType.LIBRARY: [
            HallType.STUDY_LIBRARY,
            HallType.LIBRARY_BILLIARD_ROOM,
            HallType.LIBRARY_CONSERVATORY
        ],
        RoomType.BILLIARD_ROOM: [
            HallType.HALL_BILLIARD_ROOM,
            HallType.LIBRARY_BILLIARD_ROOM,
            HallType.BILLIARD_ROOM_DINING_ROOM,
            HallType.BILLIARD_ROOM_BALLROOM
        ],
        RoomType.DINING_ROOM: [
            HallType.LOUNGE_DINING_ROOM,
            HallType.BILLIARD_ROOM_DINING_ROOM,
            HallType.DINING_ROOM_KITCHEN
        ],
        RoomType.BALLROOM: [
            HallType.BILLIARD_ROOM_BALLROOM,
            HallType.CONSERVATORY_BALLROOM,
            HallType.BALLROOM_KITCHEN
        ],
        HallType.STUDY_HALL: [
            RoomType.STUDY,
            RoomType.HALL
        ],
        HallType.HALL_LOUNGE: [
            RoomType.HALL,
            RoomType.LOUNGE
        ],
        HallType.STUDY_LIBRARY: [
            RoomType.STUDY,
            RoomType.LIBRARY
        ],
        HallType.HALL_BILLIARD_ROOM: [
            RoomType.HALL,
            RoomType.BILLIARD_ROOM
        ],
        HallType.LOUNGE_DINING_ROOM: [
            RoomType.LOUNGE,
            RoomType.DINING_ROOM
        ],
        HallType.LIBRARY_BILLIARD_ROOM: [
            RoomType.LIBRARY,
            RoomType.BILLIARD_ROOM
        ],
        HallType.BILLIARD_ROOM_DINING_ROOM: [
            RoomType.BILLIARD_ROOM,
            RoomType.DINING_ROOM
        ],
        HallType.LIBRARY_CONSERVATORY: [
            RoomType.LIBRARY,
            RoomType.CONSERVATORY
        ],
        HallType.BILLIARD_ROOM_BALLROOM: [
            RoomType.BILLIARD_ROOM,
            RoomType.BALLROOM
        ],
        HallType.DINING_ROOM_KITCHEN: [
            RoomType.DINING_ROOM,
            RoomType.KITCHEN
        ],
        HallType.CONSERVATORY_BALLROOM: [
            RoomType.CONSERVATORY,
            RoomType.BALLROOM
        ],
        HallType.BALLROOM_KITCHEN: [
            RoomType.BALLROOM,
            RoomType.KITCHEN
        ]
    }
    
    def __init__(self, location_type: str, name: str):
        self.location_type = LocationType(location_type)
        match self.location_type:
            case LocationType.ROOM:
                self.name = RoomType(name)
            case LocationType.HALLWAY:
                self.name = HallType(name)
            case _:
                raise ValueError(f"Invalid {name=} for {location_type=}")

    @classmethod
    def from_dict(cls, data_dict):
       return Location(data_dict['location_type'], data_dict['name'])

    def get_neighbors(self) -> list[Location]:
        neighbors = []

        for location in self.neighbors[self.name]:
            match self.location_type:
                case LocationType.ROOM:
                    neighbors.append(Location(LocationType.HALLWAY.value, location.value))
                case LocationType.HALLWAY:
                    neighbors.append(Location(LocationType.ROOM.value, location.value))
                case _:
                    raise ValueError(f"Invalid {location_type=}")
        
        secret_passage = self.get_secret_passage()
        neighbors = neighbors + [secret_passage] if secret_passage is not None else neighbors
        
        return neighbors

    def _identity(self):
        return (self.location_type.value, self.name.value)

    def __eq__(self, obj):
        if not isinstance(object, Location):
            raise NotImplemented
        return self._identity() == obj._identity()

    def __hash__(self) -> int:
        return hash(self._identity())

    def to_dict(self) -> dict[str, str]:        
        return {
            "location_type": self.location_type.value,
            "name": self.name.value
        }

    def get_secret_passage(self) -> Location | None:
        if isinstance(self.name, RoomType) and self.secret_passages[self.name]:
            return Location(LocationType.ROOM.value, self.secret_passages[self.name].value)
        else:
            return None

# I made this because it was in our design doc, but 
# the functionality is redundant if locations also 
# have to know their neighbors
class Board:
    def __init__(self):
        self.rooms = {room_type: Location(LocationType.ROOM.value, room_type.value) for room_type in RoomType}
        self.hallways = {hall_type: Location(LocationType.HALLWAY.value, hall_type.value) for hall_type in HallType}

    def get_location(self, location_id: str) -> Location | None:
        if location_id in RoomType:
            return self.rooms[RoomType(location_id)]
        elif location_id in LocationType:
            return self.hallways[HallType(location_id)]
        else:
            return None

    def is_hallway_occupied(self, location: Location, characters: list[Character]) -> bool:
        if location.name not in self.hallways:
            raise ValueError(f'{location=} is not a valid hallway')
        
        for character in characters:
            if character.get_location() == location:
                return True

        return False

    def get_secret_passage(self, location: Location) -> Location | None:
        return location.get_secret_passage()


class Character:
    starting_location = {
        CharType.MISS_SCARLET: HallType.HALL_LOUNGE,
        CharType.COLONEL_MUSTARD: HallType.LOUNGE_DINING_ROOM,
        CharType.PROFESSOR_PLUM: HallType.STUDY_LIBRARY,
        CharType.MRS_PEACOCK: HallType.LIBRARY_CONSERVATORY,
        CharType.MR_GREEN: HallType.CONSERVATORY_BALLROOM,
        CharType.MRS_WHITE: HallType.BALLROOM_KITCHEN.value
    }

    def __init__(self, character: str):
        self.name = CharType(character)
        self.location = Location(
            LocationType.HALLWAY.value,
            self.starting_location[self.name].value
        )
        self.moved_by_suggestion = False

    @classmethod
    def from_dict(cls, data_dict) -> Character:
        character = Character(data_dict["name"])
        character.location = Location.from_dict(data_dict["location"])
        character.moved_by_suggestion = data_dict["moved_by_suggestion"]
        return character    

    def move_to(self, location: Location) -> None:
        self.location = location

    def get_location(self) -> Location:
        return self.location

    def to_dict(self):
        return {
            "name": self.name.value,
            "location": self.location.to_dict(),
            "moved_by_suggestion": self.moved_by_suggestion
        }


class Player:
    def __init__(self, player_id: str, display_name: str):
        self.player_id = player_id
        self.display_name = display_name
        self.character = None
        self.hand = []
        self.is_eliminated = False
        self.is_connected = True

    @classmethod
    def from_dict(cls, data_dict: dict[str, Any]) -> Player:
        # Instantiate player object
        player = Player(
            data_dict["player_id"],
            data_dict["display_name"]
        )

        # Restore character
        player.character = Character.from_dict(data_dict["character"]) if data_dict["character"] is not None else None

        # Restore hand
        player.hand = [Card.from_dict(card_dict) for card_dict in data_dict["hand"]]
        
        # Restore booleans
        player.is_eliminated = data_dict["is_eliminated"]
        player.is_connected = data_dict["is_connected"]

        return player

    def add_card(self, card: Card) -> None:
        self.hand.append(card)

    def get_matching_cards(self, weapon: Card, room: Card, character: Card):
        matching = []
        if weapon in self.hand:
            matching.append(weapon)
        if room in self.hand:
            matching.append(room)
        if character in self.hand:
            matching.append(character)
        return matching

    def eliminate(self):
        self.is_eliminated = True

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "display_name": self.display_name,
            "character": self.character.to_dict() if self.character is not None else None,
            "hand": [card.to_dict() for card in self.hand],
            "is_eliminated": self.is_eliminated,
            "is_connected": self.is_connected
        }


class Suggestion:
    def __init__(
        self, 
        suggester: Player, 
        weapon: Card,
        room: Card,
        character: Card,
    ):
        self.suggester = suggester.player_id
        self.weapon = weapon
        self.room = room
        self.character = character
        self.disprover = None
        self.revealed_card = None

    @classmethod
    def from_dict(cls, data_dict) -> Suggestion:
        suggestion = Suggestion(
            suggester=Player(data_dict['suggester'], 'default'),
            weapon=Card.from_dict(data_dict['weapon']),
            room=Card.from_dict(data_dict['room']),
            character=Card.from_dict(data_dict['character'])
        )
        suggestion.disprover = data_dict['disprover']
        suggestion.revealed_card = Card.from_dict(data_dict['revealed_card']) if data_dict['revealed_card'] else None
        return suggestion

    def matches(self, card: Card):
        return card == self.weapon or \
            card == self.room or \
            card == self.character

    def record_disproval(self, player: Player, card: Card):
        self.disprover = player.player_id
        self.revealed_card = card
        
    def to_dict(self):
        return {
            "suggester": self.suggester,
            "weapon": self.weapon.to_dict(),
            "room": self.room.to_dict(),
            "character": self.character.to_dict(),
            "disprover": self.disprover if self.disprover is not None else None,
            "revealed_card": self.revealed_card.to_dict() if self.revealed_card is not None else None
        }


class Game:
    MAX_PLAYERS = 6
    def __init__(self, game_id: str, host: Player):
        self.game_id = game_id
        self.status = GameStatus.LOBBY
        self.host = host.player_id
        self.board = Board()
        self.players = {self.host: host}
        self.characters = {char_type: Character(char_type.value) for char_type in CharType}
        self.case_file = None
        self.turn_order = [self.host]
        self.current_turn_index = 0
        self.disprove_turn_index = 0
        self.current_suggestion = None
        self.suggestion_round = False
        self.created_at = datetime.now(timezone.utc)

    @classmethod
    def from_dict(cls, data_dict):
        game = Game(
            data_dict["game_id"], 
            Player(data_dict["host"], "default")
        )
        game.status = data_dict["status"]
        game.players = {
            player_id: Player.from_dict(player_dict) for player_id, player_dict in data_dict["players"].items()
        },
        game.case_file = CaseFile.from_dict(data_dict["case_file"]) if data_dict["case_file"] is not None else None,
        game.turn_order = data_dict["turn_order"],
        game.current_turn_index = data_dict["current_turn_index"]
        game.disprove_turn_index = data_dict["disprove_turn_index"]
        game.current_suggestion = Suggestion.from_dict(data_dict["current_suggestion"]) if data_dict["current_suggestion"] is not None else None,
        game.suggestion_round = data_dict["suggestion_round"]
        game.created_at = data_dict["created_at"]

        return game

    def get_current_player(self) -> Player | None:
        if self.status != GameStatus.STARTED:
            return None
        if self.suggestion_round:
            return self.players[self.turn_order[self.disprove_turn_index]]
        else:
            return self.players[self.turn_order[self.current_turn_index]]

    def advance_turn(self):
        self.current_suggestion = None
        curr_player = self.get_current_player()
        if curr_player is not None and curr_player.character is not None:
            curr_player.character.moved_by_suggestion = False
        # moved_this_turn -> False (Design doc page 9)
        
        # Advance turn count until we hit someone who is not eliminated or disconnected
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
        next_player = self.players[self.turn_order[self.current_turn_index]]
        eliminated_count = 0
        while (next_player.is_eliminated or not next_player.is_connected) \
                and eliminated_count < len(self.players):
            eliminated_count += 1
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            next_player = self.players[self.turn_order[self.current_turn_index]]

        if eliminated_count >= len(self.players):
            return None
        else:
            return next_player

    def add_player(self, player: Player):
        if self.status != GameStatus.LOBBY or len(self.players) > self.MAX_PLAYERS:
            return False
        if player.player_id not in self.players:
            self.players[player.player_id] = player
        return True

    def get_character(self, character_id: str):
        return self.characters[CharType(character_id)]

    def start_suggest_round(self, suggestion: Suggestion):
        self.suggestion_round = True
        self.current_suggestion = suggestion
        self.disprove_turn_index = (self.current_turn_index + 1) % len(self.players)

    def stop_suggest_round(self, suggestion: Suggestion):
        self.suggestion_round = False
        self.current_suggestion = None
        self.disprove_turn_index = 0

    def advance_suggest_round(self) -> bool:
        self.disprove_turn_index = (self.disprove_turn_index + 1) % len(self.players)
        
        return self.disprove_turn_index != self.current_turn_index

    def to_dict(self):
        return {
            "game_id": self.game_id,
            "status": self.status.value,
            "players": {
                player_id: player.to_dict() for player_id, player in self.players.items()
            },
            "host": self.host,
            "case_file": self.case_file.to_dict() if self.case_file is not None else None,
            "turn_order": self.turn_order,
            "current_turn_index": self.current_turn_index,
            "disprove_turn_index": self.disprove_turn_index,
            "current_suggestion": self.current_suggestion.to_dict() if self.current_suggestion is not None else None,
            "suggestion_round": self.suggestion_round,
            "created_at": self.created_at
        }
