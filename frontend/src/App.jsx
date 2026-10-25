import { useEffect, useRef, useState } from "react";

import { GameClient } from "./gameClient";

const CHARACTERS = [
  "Miss Scarlet",
  "Colonel Mustard",
  "Mrs. White",
  "Mr. Green",
  "Mrs. Peacock",
  "Professor Plum",
];

export default function App() {
  const clientRef = useRef(null);

  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [authenticated, setAuthenticated] = useState(false);

  const [displayName, setDisplayName] = useState("");
  const [playerId, setPlayerId] = useState("");

  const [gameId, setGameId] = useState("");
  const [joinGameId, setJoinGameId] = useState("");
  const [gameStatus, setGameStatus] = useState("-");

  const [characterId, setCharacterId] = useState("Miss Scarlet");
  const [targetLocationId, setTargetLocationId] = useState("hall");

  const [logs, setLogs] = useState([]);

  function addLog(direction, message) {
    const entry = {
      id: crypto.randomUUID(),
      time: new Date().toLocaleTimeString(),
      direction,
      message,
    };

    setLogs((current) => [...current, entry].slice(-100));
  }

  useEffect(() => {
    const client = new GameClient({
      onStatus: setConnectionStatus,

      onMessage: (message) => {
        addLog("IN", message);

        if (message.type === "AUTH_RESP") {
          if (message.payload?.success) {
            setAuthenticated(true);
            setPlayerId(message.payload.playerId ?? "");
          }
        }

        if (message.type === "GAME_STATE_UPDATE") {
          if (message.payload?.gameId) {
            setGameId(message.payload.gameId);
          }

          if (message.payload?.status) {
            setGameStatus(message.payload.status);
          }
        }
      },
    });

    clientRef.current = client;

    client.connect().catch((error) => {
      addLog("ERROR", {
        message: error.message,
      });
    });

    return () => {
      client.disconnect();
    };
  }, []);

  async function authenticate() {
    const name = displayName.trim();

    if (!name) {
      addLog("ERROR", {
        message: "Enter a display name first.",
      });
      return;
    }

    try {
      addLog("OUT", {
        type: "AUTH_REQ",
        payload: {
          displayName: name,
        },
      });

      await clientRef.current.authenticate(name);
    } catch (error) {
      addLog("ERROR", {
        message: error.message,
      });
    }
  }

  async function send(type, payload = {}) {
    if (!authenticated) {
      addLog("ERROR", {
        message: "Authenticate before sending game requests.",
      });
      return;
    }

    try {
      // Intentionally log the request without the Firebase session token.
      addLog("OUT", {
        type,
        payload,
      });

      await clientRef.current.send(type, payload);
    } catch (error) {
      addLog("ERROR", {
        message: error.message,
      });
    }
  }

  async function createGame() {
    await send("CREATE_GAME_REQ");
  }

  async function joinGame() {
    const id = joinGameId.trim();

    if (!id) {
      addLog("ERROR", {
        message: "Enter a game ID first.",
      });
      return;
    }

    await send("JOIN_GAME_REQ", {
      gameId: id,
    });
  }

  async function selectCharacter() {
    await send("SELECT_CHAR_REQ", {
      characterId,
    });
  }

  async function startGame() {
    if (!gameId) {
      addLog("ERROR", {
        message: "Create or join a game first.",
      });
      return;
    }

    await send("START_GAME_REQ", {
      gameId,
    });
  }

  async function move() {
    await send("MOVE_REQ", {
      targetLocationId,
    });
  }

  async function endTurn() {
    await send("END_TURN_REQ");
  }

  return (
    <main className="app">
      <header>
        <h1>Clue-Less</h1>
        <p>Skeletal System Client</p>
      </header>

      <section className="status-panel">
        <div>
          <strong>Server:</strong> {connectionStatus}
        </div>

        <div>
          <strong>Authentication:</strong>{" "}
          {authenticated ? "authenticated" : "not authenticated"}
        </div>

        <div>
          <strong>Player ID:</strong> {playerId || "-"}
        </div>

        <div>
          <strong>Game ID:</strong> {gameId || "-"}
        </div>

        <div>
          <strong>Game Status:</strong> {gameStatus}
        </div>
      </section>

      <section className="panel">
        <h2>1. Authentication</h2>

        <input
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Display name"
          maxLength={20}
        />

        <button
          onClick={authenticate}
          disabled={connectionStatus !== "connected"}
        >
          Sign In
        </button>
      </section>

      <section className="panel">
        <h2>2. Game Session</h2>

        <button onClick={createGame} disabled={!authenticated}>
          Create Game
        </button>

        <div className="row">
          <input
            value={joinGameId}
            onChange={(event) => setJoinGameId(event.target.value)}
            placeholder="g-12345678"
          />

          <button onClick={joinGame} disabled={!authenticated}>
            Join Game
          </button>
        </div>

        <div className="row">
          <select
            value={characterId}
            onChange={(event) => setCharacterId(event.target.value)}
          >
            {CHARACTERS.map((character) => (
              <option key={character} value={character}>
                {character}
              </option>
            ))}
          </select>

          <button onClick={selectCharacter} disabled={!authenticated}>
            Select Character
          </button>
        </div>

        <button onClick={startGame} disabled={!authenticated || !gameId}>
          Start Game
        </button>
      </section>

      <section className="panel">
        <h2>3. Rules Engine Communication</h2>

        <p>
          These controls demonstrate messages reaching Game Session and being
          forwarded to the Rules Engine interface.
        </p>

        <div className="row">
          <input
            value={targetLocationId}
            onChange={(event) => setTargetLocationId(event.target.value)}
            placeholder="Target location"
          />

          <button onClick={move} disabled={!authenticated || !gameId}>
            Send MOVE_REQ
          </button>
        </div>

        <button onClick={endTurn} disabled={!authenticated || !gameId}>
          Send END_TURN_REQ
        </button>
      </section>

      <section className="panel log-panel">
        <div className="log-header">
          <h2>Communication Log</h2>

          <button onClick={() => setLogs([])}>Clear</button>
        </div>

        <div className="log">
          {logs.length === 0 && <p>No messages yet.</p>}

          {logs.map((entry) => (
            <div key={entry.id} className={`log-entry ${entry.direction}`}>
              <strong>
                [{entry.time}] [{entry.direction}]
              </strong>

              <pre>{JSON.stringify(entry.message, null, 2)}</pre>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}