"""
Rules Engine subsystem

This subsystem enforces the rules for the ClueLess game:

It will satisfy the following requirements.

Turn Order:
    FR-GS-9: Same turn order throughout the game
    FR-RE-1: Only accept move, suggest, accuse requests from current player
    FR-RE-2: All player to end turn after 0+ legal actions

Movement:
    FR-RE-3: Only allow movement into adjacent hallway if hallway is
             unoccupied
    FR-RE-4: Allow secret passage from diagonal corners
    FR-RE-5: Allow characters in hall to move to adjacent room
    FR-RE-6: Involuntary movement during suggestion
    FR-RE-7: No movement if halls blocked, no secret passage, already guessed,
             and no involuntary move in preceding round

Suggestions:
    FR-RE-8: Allow suggestion if just entered room
    FR-RE-9: Allow suggestion with weapon and person (room implicit)
    FR-RE-10: Prompt players in turn order to disprove suggestion
    FR-RE-11: Force player with suggested card and next in disprove order to
              volunteer card

Accusations:
    FR-RE-12: Allow player one accusation during game
    FR-RE-13: Compare accusations to case file
    FR-RE-14: If correct accusation, end game, display winner, reveal case file
    FR-RE-15: If incorrect accusation, eliminate player from normal turn order
    FR-RE-16: Do not remove incorrect accusee token from board, still include
              them in suggestion rounds
    FR-RE-17: If everyone eliminated, no winner, show case file
"""

import logging

from game.game import (
    Card,
    CardType,
    Game,
    GameStatus,
    Location,
    LocationType,
    Player,
    Suggestion,
)

logger = logging.getLogger(__name__)


class Reason:
    OK = "ok"
    CURR_PLAYER_NO_CHAR = "Current player has no assigned character"
    GAME_NOT_STARTED_MSG = f"Game is not {GameStatus.STARTED.value}"
    NOT_CURR_PLAYER_MSG = "Player is not current player"
    PLAYER_ELIMINATED = "Player is eliminated"
    ALREADY_MOVED = "Player has already moved this turn"
    LOCATION_UNREACHABLE = "Location is not reachable from current location"
    ALREADY_IN_LOCATION = "Player is already in target location"
    HALLWAY_OCCUPIED = "Hallway is occupied"
    MOVE_DURING_SUGGEST = "Player cannot move during active suggestion"
    SUGGESTED_THIS_LOC = "Player has already made a suggestion this turn"
    SUGGEST_IN_HALLWAY = "Player cannot suggest in hallway"
    SUGGEST_DURING_SUGGEST = "Player cannot suggest during an active suggestion round"
    DISPROVE_DURING_NOT_SUGGEST = "Player cannot disprove outside of an active suggestion round"
    PASSING_WITH_VALID_DISPROVE = "Player cannot pass while holding a suggested card"
    INVALID_DISPROVE_CARD = "Player cannot disprove with card not in current suggestion"
    ACCUSE_DURING_SUGGEST = "Player cannot accuse during an active suggestion round"
    END_TURN_DURING_SUGGEST = "Player cannot end turn during an active suggestion round"
    INVALID_ACCUSATION_CARDS = "Accusation must contain a weapon, room, and character card"
    CASE_FILE_MISSING = "Game has no Case File"


class RulesEngine:
    def _validate_generic(self, game: Game, player: Player) -> tuple[bool, str]:
        # Is the game not STARTED?
        if game.status != GameStatus.STARTED:
            return False, Reason.GAME_NOT_STARTED_MSG
        curr_player = game.get_current_player()

        # Is the player not the current player?
        if player.player_id != curr_player.player_id:
            return False, Reason.NOT_CURR_PLAYER_MSG

        if curr_player.character is None:
            return False, Reason.CURR_PLAYER_NO_CHAR

        return True, Reason.OK

    def validate_move(self, game: Game, player: Player, location: Location) -> tuple[bool, str]:
        # Generic validation for all actions
        valid, reason = self._validate_generic(game, player)

        if not valid:
            return valid, reason

        curr_player = game.get_current_player()

        # Was the player eliminated?
        if curr_player.is_eliminated:
            return False, Reason.PLAYER_ELIMINATED

        # Sanity check because I haven't implemented the character assignment
        assert curr_player.character is not None

        # Is this the first move of this player's turn?
        if curr_player.character.moved_this_turn:
            return False, Reason.ALREADY_MOVED

        # Is the location reachable from the player's current location?
        adj_locations = curr_player.character.get_location().get_neighbors()
        if location not in adj_locations:
            return False, Reason.LOCATION_UNREACHABLE

        # Is the player already in this location?
        if curr_player.character.get_location() == location:
            return False, Reason.ALREADY_IN_LOCATION

        # If the location is a hallway, is the hallway occupied?
        if location.location_type == LocationType.HALLWAY:
            # Get characters
            characters = [
                player.character for player in game.players.values() if player.character is not None
            ]

            if game.board.is_hallway_occupied(location, characters):
                return False, Reason.HALLWAY_OCCUPIED

        # Is it not a suggestion round?
        if game.suggestion_round:
            return False, Reason.MOVE_DURING_SUGGEST

        return True, Reason.OK

    def perform_move(self, game: Game, player: Player, location: Location):
        valid, reason = self.validate_move(game, player, location)

        if not valid:
            return valid, reason

        curr_player = game.get_current_player()

        assert curr_player.character is not None

        curr_player.character.move_to(location, suggest=False)

        # TODO implement game state save

        # TODO implement messaging

        return valid, reason

    def validate_suggest(
        self, game: Game, player: Player, character: Card, weapon: Card
    ) -> tuple[bool, str]:
        # Generic validation for all actions
        valid, reason = self._validate_generic(game, player)

        curr_player = game.get_current_player()

        assert curr_player.character is not None

        # If player has been eliminated
        if curr_player.is_eliminated:
            return False, Reason.PLAYER_ELIMINATED

        # If we are already in a suggestion round
        if game.suggestion_round:
            return False, Reason.SUGGEST_DURING_SUGGEST

        # If player has already suggested in this location without moving
        if curr_player.character.suggested_in_curr_loc:
            return False, Reason.SUGGESTED_THIS_LOC

        # If player is in a hallway
        if curr_player.character.get_location().location_type == LocationType.HALLWAY:
            return False, Reason.SUGGEST_IN_HALLWAY

        if not valid:
            return valid, reason

        return True, Reason.OK

    def perform_suggest(self, game: Game, player: Player, character: Card, weapon: Card):
        valid, reason = self.validate_suggest(game, player, character, weapon)

        if not valid:
            return valid, reason

        # Perfom Suggest
        curr_player = game.get_current_player()
        assert curr_player.character is not None

        # Get current location
        location = curr_player.character.get_location()

        # Move suggested character to room if they're in game
        player_to_move = None
        for player_i in game.players.values():
            assert player_i.character is not None
            if player_i.character.name == character.name:
                player_to_move = player_i
                break

        if player_to_move is not None:
            assert player_to_move.character is not None
            player_to_move.character.move_to(location, suggest=True)

        # Turn location into card
        room = Card(CardType.ROOM.value, location.name.value)

        # Create suggestion
        suggestion = Suggestion(player, weapon, room, character)

        # Start suggestion round
        game.start_suggest_round(suggestion)

        # TODO implement game state save

        # TODO implement messaging

        return valid, reason

    def validate_disprove(self, game: Game, player: Player, card: Card | None) -> tuple[bool, str]:
        # Generic validation for all actions
        valid, reason = self._validate_generic(game, player)

        if not valid:
            return valid, reason

        # If it's not the suggestion round
        if not game.suggestion_round:
            return False, Reason.DISPROVE_DURING_NOT_SUGGEST

        curr_player = game.get_current_player()

        assert game.current_suggestion is not None
        assert curr_player.character is not None

        matching_cards = curr_player.get_matching_cards(
            game.current_suggestion.weapon,
            game.current_suggestion.room,
            game.current_suggestion.character,
        )

        # If player passing when they have a valid card
        if card is None and len(matching_cards) > 0:
            return False, Reason.PASSING_WITH_VALID_DISPROVE

        # If card is not in player's hand
        if card is not None and not game.current_suggestion.matches(card):
            return False, Reason.INVALID_DISPROVE_CARD

        return True, Reason.OK

    def perform_disprove(self, game: Game, player: Player, card: Card | None):
        valid, reason = self.validate_disprove(game, player, card)

        if not valid:
            return valid, reason

        # Perform Disprove
        if card is None:
            # Go on to next person
            game.advance_suggest_round()

            # TODO message / log to database?
        else:
            assert game.current_suggestion is not None
            game.current_suggestion.record_disproval(player, card)

            # TODO - Message / log to database?
            game.stop_suggest_round()

        # TODO - Save state to database?

        return valid, reason

    def validate_accuse(
        self, game: Game, player: Player, weapon: Card, room: Card, character: Card
    ) -> tuple[bool, str]:
        valid, reason = self._validate_generic(game, player)
        if not valid:
            return valid, reason

        if game.suggestion_round:
            return False, Reason.ACCUSE_DURING_SUGGEST

        curr_player = game.get_current_player()
        if curr_player.is_eliminated:
            return False, Reason.PLAYER_ELIMINATED

        if not (
            isinstance(weapon, Card)
            and isinstance(room, Card)
            and isinstance(character, Card)
            and weapon.card_type == CardType.WEAPON
            and room.card_type == CardType.ROOM
            and character.card_type == CardType.CHARACTER
        ):
            return False, Reason.INVALID_ACCUSATION_CARDS

        if game.case_file is None:
            return False, Reason.CASE_FILE_MISSING

        return True, Reason.OK

    def perform_accuse(
        self, game: Game, player: Player, weapon: Card, room: Card, character: Card
    ) -> tuple[bool, str]:
        valid, reason = self.validate_accuse(game, player, weapon, room, character)
        if not valid:
            return valid, reason

        curr_player = game.get_current_player()
        assert game.case_file is not None

        if game.case_file.accuse(room, weapon, character):
            # A correct accusation finishes the game.
            game.status = GameStatus.ENDED
            return True, Reason.OK

        # The player loses their turns but retains their character and cards,
        # allowing them to disprove suggestions later.
        curr_player.eliminate()

        remaining_players = [
            participant for participant in game.players.values() if not participant.is_eliminated
        ]
        if len(remaining_players) <= 1:
            # One survivor wins, or nobody wins if all players are eliminated.
            game.status = GameStatus.ENDED
        elif game.advance_turn() is None:
            # Nobody is available to take another turn.
            game.status = GameStatus.ENDED

        # GameSession will own persistence and client notifications after
        # the object-based RulesEngine has been integrated.
        return True, Reason.OK

    def validate_end_turn(self, game: Game, player: Player) -> tuple[bool, str]:
        valid, reason = self._validate_generic(game, player)
        if not valid:
            return valid, reason

        if game.suggestion_round:
            return False, Reason.END_TURN_DURING_SUGGEST

        curr_player = game.get_current_player()
        if curr_player.is_eliminated:
            return False, Reason.PLAYER_ELIMINATED

        return True, Reason.OK

    def perform_end_turn(self, game: Game, player: Player) -> tuple[bool, str]:
        valid, reason = self.validate_end_turn(game, player)
        if not valid:
            return valid, reason

        if game.advance_turn() is None:
            game.status = GameStatus.ENDED

        # Persistence and GAME_STATE_UPDATE are owned by GameSession
        # after integration with this object-based RulesEngine.
        return True, Reason.OK


def _validate_move(game, player, payload):
    """
    FR-RE-1
    FR-RE-3
    FR-RE-4
    FR-RE-5
    FR-RE-7
    """

    # Is the game over?
    #   Fail if yes

    # Is it the current player's turn?
    #   Fail if no

    # Is it the suggestion-disprove round?
    #   Fail if yes

    # Is the player in a hallway?
    #   Fail if trying to take hidden passage
    #   Fail if trying to go to a hallway
    #   Fail if trying to go to nonexistent/non-adjacent room

    # Is the player in a room?
    #   Fail if trying to go to blocked hallway
    #   Fail if trying to go to nonexistent secret passage
    #   Fail if trying to go to nonexistent/non-adjacent hallway

    return True, "MOVE_REQ valid"


def _validate_end_turn(game, player, payload):
    """
    FR-RE-1
    FR-RE-2
    """

    # Is the game over?
    #   Fail if yes

    # Is it the suggestion-disprove round?
    #   Fail if yes

    # Is it the current player's turn?
    #   Fail if no

    return True, "END_TURN_REQ valid"


def _validate_suggest(game, player, payload):
    """
    FR-RE-1
    FR-RE-8
    FR-RE-9
    """

    # Is the game over?
    #   Fail if yes

    # Is it the current player's turn?
    #   Fail if no

    # Is it already the suggestion-disprove round?
    #   Fail if yes

    # Is the player in a hall
    #   Fail if yes

    # Does the player suggest anything besides 1 weapon and 1 character?
    #   Fail if yes

    # Has the player suggested in this room since entering?
    #   Fail if yes

    return True, "SUGGEST_REQ valid"


def _validate_disprove(game, player, payload):
    """
    FR-RE-1
    FR-RE-11
    """

    # Is the game over?
    #    Fail if yes

    # Is it the current player's turn?
    #    Fail if no

    # Is it the suggestion-disprove round?
    #   Fail if no

    # Is the player attempting to pass but they have a suggested card?
    #   Fail if yes

    # Is the player attempting to show non-existent cards?
    #   Fail if yes

    # Is the player attempting to show a non-suggested card?
    #   Fail if yes

    return True, "DISPROVE_REQ valid"


def _validate_accuse(game, player, payload):
    """
    FR-RE-1
    FR-RE-12
    """

    # Is it the current player's turn?
    #   Fail if no

    # Has the player already made an accusation?
    #   Fail if yes

    # Is the game over?
    #   Fail if yes

    return True, "ACCUSE_REQ valid"


def _perform_move(game, player, payload) -> tuple[bool, str]:
    accepted, reason = _validate_move(game, player, payload)

    if accepted:
        # Do the move
        logger.info(f"[RULES] Accepted and executing MOVE_REQ by {player}")
    else:
        logger.info(f"[RULES] Rejecting MOVE_REQ by {player}. {reason=}")

    return accepted, reason


def _perform_suggest(game, player, payload) -> tuple[bool, str]:
    accepted, reason = _validate_suggest(game, player, payload)

    if accepted:
        # Do the suggest action
        logger.info(f"[RULES] Accepted and executing SUGGEST_REQ by {player}")
    else:
        logger.info(f"[RULES] Rejecting SUGGEST_REQ by {player}. {reason=}")

    return accepted, reason


def _perform_accuse(game, player, payload) -> tuple[bool, str]:
    """
    FR-RE-13
    FR-RE-14
    FR-RE-15
    FR-RE-16
    FR-RE-17
    """
    accepted, reason = _validate_accuse(game, player, payload)

    if accepted:
        # Do the accuse action
        logger.info(f"[RULES] Accepted and executing ACCUSE_REQ by {player}")
    else:
        logger.info(f"[RULES] Rejecting ACCUSE_REQ by {player}. {reason=}")

    return accepted, reason


def _perform_disprove(game, player, payload) -> tuple[bool, str]:
    accepted, reason = _validate_disprove(game, player, payload)

    if accepted:
        # Do the disprove action
        logger.info(f"[RULES] Accepted and executing DISPROVE_REQ by {player}")
    else:
        logger.info(f"[RULES] Rejecting DISPROVE_REQ by {player}. {reason=}")

    return accepted, reason


def _perform_end_turn(game, player, payload) -> tuple[bool, str]:
    accepted, reason = _validate_end_turn(game, player, payload)

    if accepted:
        # Do the end turn action
        logger.info(f"[RULES] Accepted and executing END_TURN_REQ by {player}")
    else:
        logger.info(f"[RULES] Rejecting END_TURN_REQ by {player}. {reason=}")

    return accepted, reason


def execute(action, game, player, payload) -> tuple[bool, str]:
    """Execute Clueless gamer operation for given action"""

    match action:
        case "MOVE_REQ":
            return _perform_move(game, player, payload)
        case "SUGGEST_REQ":
            return _perform_suggest(game, player, payload)
        case "DISPROVE_REQ":
            return _perform_disprove(game, player, payload)
        case "ACCUSE_REQ":
            return _perform_accuse(game, player, payload)
        case "END_TURN_REQ":
            return _perform_end_turn(game, player, payload)
        case _:
            reason = f'"{action}" is not a valid player action'
            logger.info(f"[RULES] Rejecting {action=}. {reason}")
            return False, reason
