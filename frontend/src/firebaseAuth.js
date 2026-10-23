// Client side Authentication subsystem (FR-AU-1, NFR-SPR-2)
//
// Signs the player in to Firebase anonymously and attaches their ID token as
// "sessionToken" to every message, which is what backend/game/auth.py checks
// The rest of the client never touches Firebase
//
// Usage:
//   import { signIn, withToken } from "./firebaseAuth";
//
//    1. When  player enters  name:
//   ws.send(JSON.stringify(await signIn("player_name")));
//     The server replies with AUTH_RESP: { success, playerId, displayName }
//
//   2. For every message after that:
//   ws.send(JSON.stringify(await withToken({ type: "MOVE_REQ", payload: { targetLocationId: "hall" } })));
//
// Requires the Firebase package: npm install firebase

import { initializeApp } from "firebase/app";
import { inMemoryPersistence, initializeAuth, signInAnonymously } from "firebase/auth";

// Import the functions you need from the SDKs you need
import { getAnalytics } from "firebase/analytics";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyD-2XGxI09JLq7AyMFuwU3tEB8V2x62iFw",
  authDomain: "clueless-50e4a.firebaseapp.com",
  projectId: "clueless-50e4a",
  storageBucket: "clueless-50e4a.firebasestorage.app",
  messagingSenderId: "544265353777",
  appId: "1:544265353777:web:161555aa0e057f32c57310",
  measurementId: "G-TSJHE643WN"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

// In-memorypersistence gives each browser tab its own anonymous player, so
// several tabs can play against each other in testing and in the demo
// TODO: (Talk to team about this) 
// Side effect: refreshing the page signs the player in as a new player
const auth = initializeAuth(app, { persistence: inMemoryPersistence });

// Signs in anonymously and returns the AUTH_REQ message to send
export async function signIn(displayName) {
  if (!auth.currentUser) {
    await signInAnonymously(auth);
  }
  return withToken({ type: "AUTH_REQ", payload: { displayName } });
}
 

// Returns a copy of the message with a fresh session token
// Call this before sending EVERY message. Tokens expire after an hour,
// and getIdToken() refreshes  automatically
export async function withToken(message) {
  if (!auth.currentUser) {
    throw new Error("Not signed in. Call signIn() first.");
  }
  const sessionToken = await auth.currentUser.getIdToken();
  return { ...message, sessionToken };
}