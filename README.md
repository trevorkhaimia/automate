# Automate UI Starter

Local starter app for launching and talking to a local Nullclaw/Claw clone, with Firefox browser control.

## What this adds

- FastAPI backend for process control
- React + Vite frontend for a simple UI
- Playwright Firefox hooks
- Placeholder `NullclawAdapter` you can point at your local claw source

## Structure

```text
backend/
  app/
    main.py
    adapter.py
    browser.py
    models.py
  requirements.txt
frontend/
  src/
    App.jsx
    main.jsx
    styles.css
  package.json
  index.html
  vite.config.js
```

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install firefox
uvicorn app.main:app --reload --port 8000
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

## Configure Nullclaw

By default the backend tries to launch a local process from:

```bash
../nullclaw
```

Override with env vars:

```bash
export NULLCLAW_CWD=/absolute/path/to/your/claw/clone
export NULLCLAW_CMD='python main.py'
```

If your project uses another entrypoint, change those values.

## API

- `POST /api/nullclaw/start`
- `POST /api/nullclaw/stop`
- `GET /api/nullclaw/status`
- `POST /api/nullclaw/message`
- `POST /api/browser/firefox/start`
- `POST /api/browser/firefox/open`
- `POST /api/browser/firefox/click`
- `POST /api/browser/firefox/type`
- `GET /api/browser/firefox/status`
- `WS /ws/events`

## Notes

This is a starter scaffold. The adapter currently writes to the child process stdin and streams stdout. If your cloned claw repo exposes a Python API instead, wire that into `backend/app/adapter.py`.
