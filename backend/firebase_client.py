"""Firebase connection. The one place in the server that talks to Firebase."""

import logging
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials

load_dotenv()  # reads backend/.env if present

logger = logging.getLogger(__name__)


def init_firebase():
    # if already initialized, do nothing
    if firebase_admin._apps:
        return

    cred_path = os.environ.get("FIREBASE_CREDENTIALS")
    if not cred_path:
        # make hard error when they land
        logger.warning("FIREBASE_CREDENTIALS not set, running without Firebase")
        return

    firebase_admin.initialize_app(credentials.Certificate(cred_path))
    logger.info("Firebase connected (project %s)", firebase_admin.get_app().options.get("projectId"))
