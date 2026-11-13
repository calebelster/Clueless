from enum import Enum


class CardType(Enum):
    WEAPON = "weapon"
    ROOM = "room"
    CHARACTER = "character"


class Weapon(Enum):
    ROPE = "rope"
    LEAD_PIPE = "lead pipe"
    KNIFE = "knife"
    WRENCH = "wrench"
    CANDLESTICK = "candlestick"
    REVOLVER = "revolver"


class Room(Enum):
    STUDY = "study"
    HALL = "hall"
    LOUNGE = "lounge"
    LIBRARY = "library"
    BILLIARD_ROOM = "billiard room"
    DINING_ROOM = "dining room"
    CONSERVATORY = "conservatory"
    BALLROOM = "ballroom"
    KITCHEN = "kitchen"


class Character(Enum):
    MISS_SCARLET = "miss scarlett"
    COLONEL_MUSTARD = "colonel mustard"
    PROFESSOR_PLUM = "professor plum"
    MRS_PEACOCK = "mrs. peacock"
    MR_GREEN = "mr. green"
    MRS_WHITE = "mrs. white"


DECK = {
    CardType.WEAPON: [weapon for weapon in Weapon],
    CardType.ROOM: [room for room in Room],
    CardType.CHARACTER: [character for character in Character]
}


class Card:
    def __init__(self, card_type: str, name: str):
        self.card_type = CardType(card_type)
        match self.card_type:
            case CardType.ROOM:
                self.name = Room(name)
            case CardType.WEAPON:
                self.name = Weapon(name)
            case CardType.CHARACTER:
                self.name = Character(name)

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
            data_dict['card_type'],
            data_dict['name']
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
            raise ValueError(f'Invalid room card, received a {room.card_type.value} card')

        if weapon.card_type != CardType.WEAPON:
            raise ValueError(f'Invalid weapon card, received a {weapon.card_type.value} card')

        if character.card_type != CardType.CHARACTER:
            raise ValueError(f'Invalid character card, received a {character.card_type.value} card')

        self.room = room
        self.weapon = weapon
        self.character = character

    @classmethod
    def from_dict(cls, data_dict):
        return CaseFile(
            room=Card.from_dict(data_dict['room']),
            weapon=Card.from_dict(data_dict['weapon']),
            character=Card.from_dict(data_dict['character'])
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
