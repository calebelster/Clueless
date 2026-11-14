"""
Serialization between in-memory game state and Firestore.

Game state can be plain dicts (current code) or objects from Rules Engine turns either into
data firestone.

Friestore rules that are enforced here:
    - dict keys must be strings
    - a list cannot directly contain another list
    - only str, int, float, bool, None, dict, and list are stored

"""

import dataclasses
import enum
from datetime import date, datetime


class SerializationError(TypeError):
    "Raised when game state cannot be stored in Firestore"

def to_storable(obj, _path="state"):
    "Return a Firestore-safe copy of obj, Never edits obj"
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    if isinstance(obj, enum.Enum):
        return to_storable(obj.value, _path)

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    # Rules Engine classes can opt in by defining to_dict().
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        return to_storable(to_dict(), _path)

    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return to_storable(dataclasses.asdict(obj), _path)

    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise SerializationError(f"{_path}: key {key!r} is not a string")
            out[key] = to_storable(value, f"{_path}.{key}")
        return out

    if isinstance(obj, (list, tuple, set, frozenset)):
        items = sorted(obj) if isinstance(obj, (set, frozenset)) else obj
        out = []
        for i, value in enumerate(items):
            item_path = f"{_path}[{i}]"
            if isinstance(value, (list, tuple, set, frozenset)):
                raise SerializationError(
                    f"{item_path}: Firestore cannot store a list inside a list; use a dict"
                )
            out.append(to_storable(value, item_path))
        return out

    raise SerializationError(f"{_path}: cannot store {type(obj).__name__}")

def from_storable(doc, cls=None):
    """
    Return a stored document as a dict, or as cls if cls defines from_dict().
    Returns None for a missing document.
    """
    if doc is None:
        return None
    if cls is not None:
        return cls.from_dict(doc)
    return doc