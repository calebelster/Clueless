"Shared test setup: every test starts with an empty in-memory database, never Firestore "

import pytest

from game import db


@pytest.fixture(autouse=True)
def _memory_db():
    db.use_store(db.MemoryStore())
    yield
    db.use_store(None)
