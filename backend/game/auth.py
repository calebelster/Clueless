"""
Authentication subsytem: verified who sent message

CLients sign in to firebase with anonymous sign in and put their firebase ID session token in the top-level "token" fiel of every message

The server never trusts a player ID or display name the client sends. It takes the player ID from the verifief token and the display name from the DB

Communication calls:
    login(message)
    authenticate(message)
"""

import logging

from firebase_admin import auth as fb_auth

from game import db

logger = logging.getLogger(__name__)

MAX_NAME_LENGTH = 20

#uid -> disoplay name. Save a database read on every message
# faail back to db after a server restart 

_names = {}

def _auth_fail(error_code, reason):
    #auth resp for a failed login
    return {
        "type": "AUTH_RESP",
        "payload": {"success": False,
                     "errorCode" : error_code,
                      "reason": reason }
    }

def _rejected(error_code, reason):
    " ACTION_REJECTED (), sent to the sender only (NFR-OR-2, NFR, UER-3)"
    return {
        "type": "ACTION_REJECTED",
        "payload":{"errorCode": error_code,
                   "reason": reason
                   }
    }

def _pop_token(message):
    "remove the sseion token formt he message and return it"
    token = message.pop("sessionToken", None)
    payload = message.get("payload")
    if isinstance(payload, dict) and "sessionToken" in payload:
        payload = dict(payload)
        payload_token = payload.pop("sessionToken")
        message["payload"] = payload
        token = token or payload_token
    return token

def verify_token(token):
    "return firebase uid for a valid id token or non"
    "fails clossed: missing otken, bad token, firebase not avail"
    if not isinstance(token, str) or not token:
        return None
    try:
        return fb_auth.verify_id_token(token)["uid"]
    except fb_auth.CertificateFetchError:
        logger.error("[AUTH] could not fetch Firebase signing keys: token rejected")
    except (ValueError, fb_auth.InvalidIdTokenError) as err:
        # invalidTokenError covers expried and revoked 
        #valeuError vcoers malformed tokens
        logger.warning("[AUTH] reject:=%s", err )
    return None

def _clean_name(name):
    "return tge display name or none"
    if not isinstance(name, str):
        return None
    name = name.strip()
    if not 1 <= len(name) <= MAX_NAME_LENGTH or not name.isprintable():
        return None
    return name

def login(message):
    "Handles AUTH_REQ: verify the token, the save the player displayes name (FR-AU-1)"
    message = dict(message) #never edit the caller dict
    uid = verify_token(_pop_token(message))
    if uid is None:
        return _auth_fail("AUTH_INVALID_TOKEN", "Missing session token")

    payload = message.get("payload")
    # incline verification that payload exists and trimming to make name smaller
    name = _clean_name(payload.get("displayName") if isinstance(payload, dict) else None)
   
    if name is None:
        return _auth_fail(
            "INVALID_DISPLAY_NAME", "display name msut be 1 to 20"
        )

    try:
        db.save_player(uid,name)
    except Exception:
        logger.exception("[AUTH] ccoudl not save=%s", uid)
        return _auth_fail("SERVER_ERROR", "could not sign in/. ")

    _names[uid] = name
    logger.info("[AUTH] Auth_Red ok playerID=%s   displaayName = %s", uid, name)
    return {
        "type": "AUTH_RESP",
        "payload": {"success": True,
                    "playerId": uid,
                    "displayName": name}
    }

def _lookup_name(uid):
    #looks up the name
    name = _names.get(uid)
    if name is None:
        player = db.load_player(uid)
        if player is not None:
            name = player.get("displayName")
            _names[uid] = name
    return name

def authenticate(message):
    """
    Verify sender of any request othe than AUTH_REQ
    On success, return xopy of the message with session toke removed nad verified playedID and dislayname fiels set
    on fialyrte, returns an ACTION_REJECTED for sender only 
    """
    message = dict(message) #do not edit called dict
    uid = verify_token(_pop_token(message)) # token doe not reaxch logs
    if uid is None:
        return None, _rejected ("AUTH_INVALID_TOKEN", "missing token")
    try:
        name = _lookup_name(uid)
    except Exception:
        logger.exception("[AUTH] did not fine %s", uid)
        return None, _rejected("SERVER_ERROR", "could not verify player")

    if name is None:
        return None, _rejected("AUTH_NOT_SIGNED_IN", "send AUTH_REQ BEFORE requests")

    message["playerId"] = uid #overiwte what the client claimed
    message["displayName"] = name #ovewrties
    logger.info("[AUTH] verifed= %s playerID = %s", message.get("type"), uid)
    return message, None