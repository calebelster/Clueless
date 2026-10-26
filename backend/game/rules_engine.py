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

logger = logging.getLogger(__name__)


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
