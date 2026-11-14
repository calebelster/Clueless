""""
Private information filter

Every game state sent to client goes throug player_view() first. A viewer sees only their own 
hand. Other players hanf are replaced with a count, and the Case File stays hidden until the
game is finished
"""

import copy

CASE_FILE_KEYS = ("case_file", "caseFile")
FINISHED = "finished"

def player_view(state, viewer_uid):
    # Return a copy of state that is safe to send to viewer_uid
    view = copy.deepcopy(state) if state else {}

    if view.get("status") != FINISHED:
        for key in CASE_FILE_KEYS:
            view.pop(key, None)

    players = view.get("players")
    if isinstance(players, dict):
        for uid, player in players.items():
            if uid != viewer_uid and isinstance(player, dict) and "hand" in player:
                hand = player.pop("hand") or []
                player["hand_count"] = len(hand)

    return view