// suggest, accuse and disprove modals

import { useState } from "react";

// card decks
export const CHARACTERS = [
  "Miss Scarlet",
  "Colonel Mustard",
  "Mrs. White",
  "Mr. Green",
  "Mrs. Peacock",
  "Professor Plum",
];

const WEAPONS = ["Rope", "Lead Pipe", "Knife", "Wrench", "Candlestick", "Revolver"];

export const ROOMS = [
  "Study",
  "Hall",
  "Lounge",
  "Library",
  "Billiard Room",
  "Dining Room",
  "Conservatory",
  "Ballroom",
  "Kitchen",
];

// cards arrive as objects or plain strings
export function cardName(card) {
  if (typeof card === "string") {
    return card;
  }
  return card?.name ?? "";
}

// modal shell
function Modal({ title, children, onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          {onClose && (
            <button className="modal-close" onClick={onClose} aria-label="Close">
              ×
            </button>
          )}
        </div>
        {children}
      </div>
    </div>
  );
}

// labeled select
function CardSelect({ label, options, value, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

// suggest, room is implicit
export function SuggestModal({ room, onSubmit, onClose }) {
  const [character, setCharacter] = useState(CHARACTERS[0]);
  const [weapon, setWeapon] = useState(WEAPONS[0]);

  return (
    <Modal title="Make a suggestion" onClose={onClose}>
      <p className="modal-note">Room: {room} (implicit)</p>
      <CardSelect label="Suspect" options={CHARACTERS} value={character} onChange={setCharacter} />
      <CardSelect label="Weapon" options={WEAPONS} value={weapon} onChange={setWeapon} />
      <button onClick={() => onSubmit(character, weapon)}>Suggest</button>
    </Modal>
  );
}

// accuse, all three cards
export function AccuseModal({ onSubmit, onClose }) {
  const [character, setCharacter] = useState(CHARACTERS[0]);
  const [weapon, setWeapon] = useState(WEAPONS[0]);
  const [room, setRoom] = useState(ROOMS[0]);

  return (
    <Modal title="Make an accusation" onClose={onClose}>
      <CardSelect label="Suspect" options={CHARACTERS} value={character} onChange={setCharacter} />
      <CardSelect label="Weapon" options={WEAPONS} value={weapon} onChange={setWeapon} />
      <CardSelect label="Room" options={ROOMS} value={room} onChange={setRoom} />
      <button onClick={() => onSubmit(character, weapon, room)}>Accuse</button>
    </Modal>
  );
}

// disprove, show a matching card or pass, no close button
export function DisproveModal({ suggestion, hand, onRespond }) {
  const suggested = [
    cardName(suggestion.character),
    cardName(suggestion.weapon),
    cardName(suggestion.room),
  ];
  const matches = (hand ?? []).filter((card) => suggested.includes(cardName(card)));

  return (
    <Modal title="Disprove the suggestion">
      <p className="modal-note">
        {suggested[0]} with the {suggested[1]} in the {suggested[2]}
      </p>
      {matches.length > 0 ? (
        <>
          <p>Your matching cards:</p>
          <div className="card-row">
            {matches.map((card, index) => (
              <button key={index} onClick={() => onRespond(card)}>
                {cardName(card)}
              </button>
            ))}
          </div>
        </>
      ) : (
        <p>You have no matching cards.</p>
      )}
      <button onClick={() => onRespond(null)}>Pass</button>
    </Modal>
  );
}
