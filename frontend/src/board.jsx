// board view, 3x3 rooms + hallways + tokens, click a tile to move
// legal move highlighting is a hint only, the server rejects illegal moves

const ROOMS = [
  { id: "study", name: "Study", row: 1, col: 1, passage: "Kitchen" },
  { id: "hall", name: "Hall", row: 1, col: 3 },
  { id: "lounge", name: "Lounge", row: 1, col: 5, passage: "Conservatory" },
  { id: "library", name: "Library", row: 3, col: 1 },
  { id: "billiard room", name: "Billiard Room", row: 3, col: 3 },
  { id: "dining room", name: "Dining Room", row: 3, col: 5 },
  { id: "conservatory", name: "Conservatory", row: 5, col: 1, passage: "Lounge" },
  { id: "ballroom", name: "Ballroom", row: 5, col: 3 },
  { id: "kitchen", name: "Kitchen", row: 5, col: 5, passage: "Study" },
];

// hallways between rooms, rows and cols on a 5x5 grid
const HALLWAYS = [
  { id: "study-hall", row: 1, col: 2 },
  { id: "hall-lounge", row: 1, col: 4 },
  { id: "study-library", row: 2, col: 1 },
  { id: "hall-billiard", row: 2, col: 3 },
  { id: "lounge-dining", row: 2, col: 5 },
  { id: "library-billiard", row: 3, col: 2 },
  { id: "billiard-dining", row: 3, col: 4 },
  { id: "library-conservatory", row: 4, col: 1 },
  { id: "billiard-ballroom", row: 4, col: 3 },
  { id: "dining-kitchen", row: 4, col: 5 },
  { id: "conservatory-ballroom", row: 5, col: 2 },
  { id: "ballroom-kitchen", row: 5, col: 4 },
];

// adjacent locations + secret passages
const NEIGHBORS = {
  study: ["study-hall", "study-library", "kitchen"],
  hall: ["study-hall", "hall-billiard", "hall-lounge"],
  lounge: ["hall-lounge", "lounge-dining", "conservatory"],
  library: ["study-library", "library-billiard", "library-conservatory"],
  "billiard room": [
    "hall-billiard",
    "library-billiard",
    "billiard-dining",
    "billiard-ballroom",
  ],
  "dining room": ["lounge-dining", "billiard-dining", "dining-kitchen"],
  conservatory: ["library-conservatory", "conservatory-ballroom", "lounge"],
  ballroom: ["billiard-ballroom", "conservatory-ballroom", "ballroom-kitchen"],
  kitchen: ["ballroom-kitchen", "dining-kitchen", "study"],
  "study-hall": ["study", "hall"],
  "hall-lounge": ["hall", "lounge"],
  "study-library": ["study", "library"],
  "hall-billiard": ["hall", "billiard room"],
  "lounge-dining": ["lounge", "dining room"],
  "library-billiard": ["library", "billiard room"],
  "billiard-dining": ["billiard room", "dining room"],
  "library-conservatory": ["library", "conservatory"],
  "billiard-ballroom": ["billiard room", "ballroom"],
  "dining-kitchen": ["dining room", "kitchen"],
  "conservatory-ballroom": ["conservatory", "ballroom"],
  "ballroom-kitchen": ["ballroom", "kitchen"],
};

// backend used two hallway id styles, map both to the short ids above
export function normalizeLocationId(id) {
  return String(id || "").replaceAll("_room", "");
}

// one color per suspect
const TOKEN_COLORS = {
  "Miss Scarlet": "#b03a2e",
  "Colonel Mustard": "#b7770d",
  "Mrs. White": "#616e6c",
  "Mr. Green": "#1e7e34",
  "Mrs. Peacock": "#21618c",
  "Professor Plum": "#6c3483",
};

function initials(character) {
  return character
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function Board({ boardLocations, myCharacter, canAct, highlight, onMove }) {
  // group tokens by location, remember raw ids so moves echo back exactly
  const tokensByLocation = {};
  const rawIds = {};
  for (const [character, location] of Object.entries(boardLocations ?? {})) {
    const id = normalizeLocationId(location);
    (tokensByLocation[id] ??= []).push(character);
    rawIds[id] = location;
  }

  const myLocation = myCharacter
    ? normalizeLocationId(boardLocations?.[myCharacter])
    : null;
  const legalMoves = highlight && myLocation ? NEIGHBORS[myLocation] ?? [] : [];

  function handleTileClick(tile) {
    if (!canAct) {
      return;
    }
    onMove(rawIds[tile.id] ?? tile.id);
  }

  function renderTile(tile, kind) {
    const isLegal = legalMoves.includes(tile.id);
    const tokens = tokensByLocation[tile.id] ?? [];
    return (
      <button
        key={tile.id}
        className={`tile ${kind}${isLegal ? " legal" : ""}`}
        style={{ gridRow: tile.row, gridColumn: tile.col }}
        onClick={() => handleTileClick(tile)}
        disabled={!canAct}
        title={tile.name}
      >
        {kind === "room" && <span className="tile-name">{tile.name}</span>}
        {tile.passage && (
          <span className="passage" title={`Secret passage to ${tile.passage}`}>
            ⇄
          </span>
        )}
        <span className="tokens">
          {tokens.map((character) => (
            <span
              key={character}
              className={`token${character === myCharacter ? " mine" : ""}`}
              style={{ background: TOKEN_COLORS[character] ?? "#5d6d7e" }}
            >
              {initials(character)}
            </span>
          ))}
        </span>
      </button>
    );
  }

  return (
    <section className="panel board-panel">
      <div className="board">
        {ROOMS.map((room) => renderTile(room, "room"))}
        {HALLWAYS.map((hallway) => renderTile(hallway, "hallway"))}
      </div>
      <p className="hint">
        Click a highlighted tile to move there. The server rejects illegal moves.
      </p>
    </section>
  );
}
