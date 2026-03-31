# Nullclaw UI

Open `index.html` in a browser after running `nullclaw gateway`.

If messages do not respond, the gateway likely requires pairing/auth for the WebSocket protocol. The UI currently connects to `ws://127.0.0.1:32123/ws` and sends a `connect` request followed by `chat.send` requests.

This folder is intentionally minimal so it can be iterated quickly against the live Nullclaw gateway.
