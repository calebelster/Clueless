// Client-side Authentication subsystem (FR-AU-1, NFR-SPR-2)
//
// Signs the player in to Firebase anonymously and attaches their Firebase ID
// token as the top-level "sessionToken" field on every message.
// backend/game/auth.py verifies this token before processing requests.
//
// Usage:
//   import { signIn, withToken } from "./firebaseAuth";
//
// 1. When a player enters a display name:
//    ws.send(JSON.stringify(await signIn("player_name")));
//    The server replies with AUTH_RESP: { success, playerId, displayName }
//
// 2. For every message after that:
//    ws.send(JSON.stringify(await withToken({
//      type: "MOVE_REQ",
//      payload: { targetLocationId: "hall" }
//    })));
//
// Requires:
//   npm install firebase

import { initializeApp } from "firebase/app";
import {
  inMemoryPersistence,
  initializeAuth,
  signInAnonymously,
} from "firebase/auth";

// Firebase web application configuration.
const firebaseConfig = {
  apiKey: "AIzaSyD-2XGxI09JLq7AyMFuwU3tEB8V2x62iFw",
  authDomain: "clueless-50e4a.firebaseapp.com",
  projectId: "clueless-50e4a",
  storageBucket: "clueless-50e4a.firebasestorage.app",
  messagingSenderId: "544265353777",
  appId: "1:544265353777:web:161555aa0e057f32c57310",
  measurementId: "G-TSJHE643WN",
};

// Initialize Firebase.
const app = initializeApp(firebaseConfig);

// In-memory persistence gives each browser tab its own anonymous Firebase user.
// This is useful for testing multiple Clue-Less players in separate tabs.
//
// Note: refreshing the page creates a new anonymous player session.
const auth = initializeAuth(app, {
  persistence: inMemoryPersistence,
});

// Signs the player in anonymously if needed and returns an AUTH_REQ
// containing the display name and Firebase session token.
export async function signIn(displayName) {
  if (!auth.currentUser) {
    await signInAnonymously(auth);
  }

  return withToken({
    type: "AUTH_REQ",
    payload: { displayName },
  });
}

// Returns a copy of the message with a fresh Firebase ID token attached as
// "sessionToken". Call this before sending every authenticated request.
// getIdToken() refreshes the token automatically when necessary.
export async function withToken(message) {
  if (!auth.currentUser) {
    throw new Error("Not signed in. Call signIn() first.");
  }

  const sessionToken = await auth.currentUser.getIdToken();

  return {
    ...message,
    sessionToken,
  };
}