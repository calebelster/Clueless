import { signIn as buildAuthRequest, withToken } from "./firebaseAuth";

export class GameClient {
  constructor({
    url = "ws://127.0.0.1:5000/ws",
    onMessage = () => {},
    onStatus = () => {},
  } = {}) {
    this.url = url;
    this.ws = null;
    this.onMessage = onMessage;
    this.onStatus = onStatus;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    this.onStatus("connecting");

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this.url);
      this.ws = ws;

      ws.onopen = () => {
        this.onStatus("connected");
        resolve();
      };

      ws.onmessage = (event) => {
        try {
          this.onMessage(JSON.parse(event.data));
        } catch {
          this.onMessage({
            type: "INVALID_SERVER_MESSAGE",
            payload: {
              raw: event.data,
            },
          });
        }
      };

      ws.onerror = () => {
        this.onStatus("error");
        reject(new Error("WebSocket connection failed."));
      };

      ws.onclose = () => {
        this.onStatus("disconnected");
      };
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendRaw(message) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("Client is not connected to the Clue-Less server.");
    }

    this.ws.send(JSON.stringify(message));
  }

  async authenticate(displayName) {
    const message = await buildAuthRequest(displayName);
    this.sendRaw(message);
  }

  async send(type, payload = {}) {
    const message = await withToken({
      type,
      payload,
    });

    this.sendRaw(message);
  }
}