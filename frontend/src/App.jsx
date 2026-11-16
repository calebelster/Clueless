// clue-less client ui
// all game state comes from the server, the client only sends requests
// panels for stuff the backend does not send yet stay hidden until it does

import { useEffect, useRef, useState } from "react";

import { Board, normalizeLocationId } from "./board";
import { GameClient } from "./gameClient";
import {
  AccuseModal,
  CHARACTERS,
  DisproveModal,
  cardName,
  ROOMS,
  SuggestModal,
} from "./modals";

// backend used several status spellings, map them all
function normalizeStatus(value) {
  const status = String(value || "").toLowerCase();
  if (status === "ended" || status === "finished") {
    return "ended";
  }
  if (status === "started" || status === "in_progress") {
    return "started";
  }
  return "lobby";
}

// cards arrive in a couple of shapes
function cardType(card) {
  const type = card?.card_type ?? card?.category ?? "";
  return type === "suspect" ? "character" : type;
}

// case file can be card objects or plain strings
function caseFileCards(caseFile) {
  if (!caseFile) {
    return null;
  }
  return {
    character: cardName(caseFile.character) || caseFile.suspect,
    weapon: cardName(caseFile.weapon) || caseFile.weapon,
    room: cardName(caseFile.room) || caseFile.room,
  };
}

export default function App() {
  const clientRef = useRef(null);

  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [authenticated, setAuthenticated] = useState(false);

  const [displayName, setDisplayName] = useState("");
  const [playerId, setPlayerId] = useState("");

  // full game state from the server
  const [game, setGame] = useState(null);

  const [joinGameId, setJoinGameId] = useState("");

  const [logs, setLogs] = useState([]); // raw message log, dev tool
  const [events, setEvents] = useState([]); // human readable events
  const [toasts, setToasts] = useState([]); // rejection popups
  const [modal, setModal] = useState(null); // suggest or accuse

  function addLog(direction, message) {
    const entry = {
      id: crypto.randomUUID(),
      time: new Date().toLocaleTimeString(),
      direction,
      message,
    };

    setLogs((current) => [...current, entry].slice(-100));
  }

  function addToast(text) {
    const id = crypto.randomUUID();
    setToasts((current) => [...current, { id, text }]);
    // auto dismiss so the board stays readable
    setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 4000);
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
          } else {
            addToast(`Sign-in failed: ${message.payload?.reason ?? "unknown error"}`);
          }
        }

        if (message.type === "GAME_STATE_UPDATE") {
          setGame(message.payload ?? null);
        }

        if (message.type === "EVENT_LOG_NOTIFICATION") {
          const text = message.payload?.description ?? message.payload?.eventType;
          if (text) {
            setEvents((current) =>
              [...current, { id: crypto.randomUUID(), time: new Date().toLocaleTimeString(), text }].slice(-100),
            );
          }
        }

        if (message.type === "ACTION_REJECTED") {
          addToast(message.payload?.reason ?? "Action rejected");
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

  // derived game state
  const status = normalizeStatus(game?.status);
  const inLobby = status === "lobby";
  const gameEnded = status === "ended";

  const myPlayer = game?.players?.[playerId] ?? null;
  const myCharacter = myPlayer?.characterId ?? null;
  // own hand, hidden until the backend sends it
  const myHand = Array.isArray(myPlayer?.hand) ? myPlayer.hand : null;

  const isMyTurn = Boolean(game && game.currentTurnPlayer === playerId);
  const currentPlayer = game?.players?.[game.currentTurnPlayer] ?? null;

  const myLocationId = myCharacter
    ? normalizeLocationId(game?.boardLocations?.[myCharacter])
    : null;
  const myRoom =
    ROOMS.find((room) => room.toLowerCase() === String(myLocationId ?? "").toLowerCase()) ??
    null;

  // disprove prompt, shows when the backend sends suggestion state
  const suggestion = game?.currentSuggestion ?? null;
  const disproveTurn =
    game?.disproveTurnPlayer ?? game?.disproveTurnPlayerId ?? game?.currentTurnPlayer;
  const mustDisprove = Boolean(suggestion && status === "started" && disproveTurn === playerId);

  const winner = game?.winnerId
    ? (game.players?.[game.winnerId]?.displayName ?? null)
    : null;
  const revealedCaseFile = gameEnded ? caseFileCards(game?.caseFile) : null;

  async function authenticate() {
    const name = displayName.trim();

    if (!name) {
      addToast("Enter a display name first.");
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
      addToast(error.message);
    }
  }

  async function send(type, payload = {}) {
    if (!authenticated) {
      addToast("Sign in before sending game requests.");
      return;
    }

    try {
      // log without the session token
      addLog("OUT", {
        type,
        payload,
      });

      await clientRef.current.send(type, payload);
    } catch (error) {
      addToast(error.message);
    }
  }

  async function createGame() {
    await send("CREATE_GAME_REQ");
  }

  async function joinGame() {
    const id = joinGameId.trim();

    if (!id) {
      addToast("Enter a game ID first.");
      return;
    }

    await send("JOIN_GAME_REQ", {
      gameId: id,
    });
  }

  async function selectCharacter(name) {
    await send("SELECT_CHAR_REQ", {
      characterId: name,
    });
  }

  async function startGame() {
    if (!game?.gameId) {
      addToast("Create or join a game first.");
      return;
    }

    await send("START_GAME_REQ", {
      gameId: game.gameId,
    });
  }

  async function move(targetLocationId) {
    await send("MOVE_REQ", {
      targetLocationId,
    });
  }

  async function suggest(character, weapon) {
    setModal(null);
    await send("SUGGEST_REQ", {
      character,
      weapon,
    });
  }

  async function accuse(character, weapon, room) {
    setModal(null);
    await send("ACCUSE_REQ", {
      character,
      weapon,
      room,
    });
  }

  // send the card back as received, null to pass
  async function disprove(card) {
    await send("DISPROVE_REQ", {
      card,
    });
  }

  async function endTurn() {
    await send("END_TURN_REQ");
  }

  async function copyGameId() {
    try {
      await navigator.clipboard.writeText(game.gameId);
      addToast("Game ID copied.");
    } catch {
      addToast("Copy failed — select the ID manually.");
    }
  }

  return (
    <main className="app">
      <header>
        <h1>Clue-Less</h1>
        <p>Find the suspect, weapon, and room before anyone else does.</p>
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
          <strong>Game ID:</strong> {game?.gameId || "-"}
        </div>

        <div>
          <strong>Game Status:</strong> {status}
        </div>
      </section>

      {gameEnded && (
        <section className="panel end-game">
          <h2>Game over</h2>
          <p>{winner ? `${winner} wins!` : "No winner — every player was eliminated."}</p>
          {revealedCaseFile && (
            <p>
              The Case File was {revealedCaseFile.character} with the{" "}
              {revealedCaseFile.weapon} in the {revealedCaseFile.room}.
            </p>
          )}
        </section>
      )}

      {(!authenticated || !game || inLobby) && (
        <>
          {!authenticated && (
            <section className="panel">
              <h2>Sign in</h2>

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
          )}

          <section className="panel">
            <h2>Game lobby</h2>

            <div className="row">
              <button onClick={createGame} disabled={!authenticated}>
                Create Game
              </button>

              <input
                value={joinGameId}
                onChange={(event) => setJoinGameId(event.target.value)}
                placeholder="Game ID (g-12345678)"
              />

              <button onClick={joinGame} disabled={!authenticated}>
                Join Game
              </button>
            </div>

            {game && (
              <>
                <div className="game-id-row">
                  <strong>Game ID:</strong> <code>{game.gameId}</code>
                  <button onClick={copyGameId}>Copy</button>
                </div>

                <h3>Choose a character</h3>
                <div className="character-grid">
                  {CHARACTERS.map((name) => {
                    const takenBy = Object.entries(game.players ?? {}).find(
                      ([uid, player]) => player.characterId === name && uid !== playerId,
                    );

                    return (
                      <button
                        key={name}
                        className={myCharacter === name ? "character chosen" : "character"}
                        disabled={!authenticated || Boolean(takenBy)}
                        onClick={() => selectCharacter(name)}
                      >
                        {name}
                        {takenBy && <small> ({takenBy[1].displayName})</small>}
                      </button>
                    );
                  })}
                </div>

                <h3>Players</h3>
                <ul className="player-list">
                  {Object.entries(game.players ?? {}).map(([uid, player]) => (
                    <li key={uid}>
                      {player.displayName || uid}
                      {player.characterId ? ` — ${player.characterId}` : ""}
                      {uid === game.hostId ? " (host)" : ""}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={startGame}
                  disabled={!authenticated || game.hostId !== playerId}
                >
                  Start Game
                </button>
                {game.hostId !== playerId && (
                  <p className="hint">Only the host can start the game.</p>
                )}
              </>
            )}
          </section>
        </>
      )}

      {game && !inLobby && (
        <>
          <section className={`turn-banner${isMyTurn && !gameEnded ? " my-turn" : ""}`}>
            {gameEnded
              ? "Game over"
              : isMyTurn
                ? "Your turn — move, suggest, accuse, or end turn"
                : `Waiting for ${currentPlayer?.displayName ?? "another player"}`}
          </section>

          <Board
            boardLocations={game.boardLocations}
            myCharacter={myCharacter}
            canAct={Boolean(myCharacter) && !gameEnded}
            highlight={isMyTurn && !gameEnded}
            onMove={move}
          />

          {!gameEnded && (
            <section className="panel action-panel">
              <button onClick={() => setModal("suggest")} disabled={!isMyTurn || !myRoom}>
                Suggest
              </button>

              <button onClick={() => setModal("accuse")} disabled={!isMyTurn}>
                Accuse
              </button>

              <button onClick={endTurn} disabled={!isMyTurn}>
                End Turn
              </button>
            </section>
          )}

          {myHand && (
            <section className="panel">
              <h2>Your cards</h2>
              <div className="card-row">
                {myHand.map((card, index) => (
                  <span key={index} className="card-chip">
                    {cardName(card)}
                    <small>{cardType(card)}</small>
                  </span>
                ))}
              </div>
            </section>
          )}

          <section className="panel">
            <h2>Game events</h2>
            <div className="events">
              {events.length === 0 && <p>No events yet.</p>}

              {events.map((event) => (
                <div key={event.id} className="event">
                  <span className="event-time">{event.time}</span> {event.text}
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      {modal === "suggest" && (
        <SuggestModal room={myRoom} onSubmit={suggest} onClose={() => setModal(null)} />
      )}

      {modal === "accuse" && (
        <AccuseModal onSubmit={accuse} onClose={() => setModal(null)} />
      )}

      {mustDisprove && (
        <DisproveModal suggestion={suggestion} hand={myHand} onRespond={disprove} />
      )}

      <div className="toasts">
        {toasts.map((toast) => (
          <div key={toast.id} className="toast">
            {toast.text}
          </div>
        ))}
      </div>

      <details className="panel log-panel">
        <summary>Message log ({logs.length})</summary>

        <div className="log-header">
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
      </details>
    </main>
  );
}
