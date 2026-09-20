# Roxstar AI Voice Room

## Overview

This project is a local LiveKit voice room with two AI participants:

- Roxstar AI Dost — male persona, voice Puck
- Roxstar AI Sathi — female persona, voice Aoede

The room uses a single LiveKit `AgentSession` and rotates the active agent with an explicit handoff. This keeps the conversation context intact while allowing both personas to participate in the same room.

## Root cause of the missing AI participant

The browser UI was not showing the AI because the room worker was not reliably alive on the required port. In practice, the app can connect the browser to the room only if:

1. the token server is running on port 8000,
2. the LiveKit agent worker is running on port 8081,
3. the worker is started with `agent.py start`, and
4. the agent dispatch is created for the same project as the worker.

Stale worker processes on 8081 or starting the worker without the proper subcommand caused the room to join without a remote AI participant.

## Tech stack

- Python
- LiveKit Agents 1.8.2
- Google Gemini Live / Realtime
- FastAPI token server
- HTML + CSS + JavaScript frontend
- Vite for local frontend serving

## Local startup

From the project root:

Terminal 1
```powershell
cd backend
.\venv\Scripts\python.exe main.py
```

Terminal 2
```powershell
cd backend
.\venv\Scripts\python.exe agent.py start
```

Terminal 3
```powershell
cd frontend
python -m http.server 8080 --bind 127.0.0.1
```

Then open:
```text
http://127.0.0.1:8080
```

## Environment

Create a local `.env` file in the project root or backend folder with:

```env
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your-key
LIVEKIT_API_SECRET=your-secret
GOOGLE_API_KEY=your-google-key
```

Do not disable SSL verification. The project uses `certifi` and keeps certificate validation enabled.

## Features

- Two AI agents in one shared room
- Hindi / Hinglish / English persona switching
- Follow-up question handling
- Session memory and speaker facts
- Agent handoff between Dost and Sathi
- Browser mic and speaker support
- Basic text chat and handoff controls
- Operational logging and validation

## Testing

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests -q
```

## Deploying to LiveKit Cloud

For production or LiveKit Cloud deployment, keep the worker image focused on the agent process and let the token API run through a separate service or container. The repository includes a `Dockerfile` and `livekit.toml` for that deployment path.

## Project files

- Backend: `backend/agent.py`, `backend/main.py`
- Frontend: `frontend/index.html`, `frontend/app.js`
- Docs: `docs/architecture.md`, `docs/demo.md`

## Known limits

- Session memory lives in memory for the room lifecycle.
- Audio and remote participant behavior depend on the LiveKit worker and matching project credentials.
- For a real browser voice test, the browser must allow microphone access.
