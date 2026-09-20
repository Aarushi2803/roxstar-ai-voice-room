# Demo and validation guide

## Local run

1. Start the FastAPI token server:
   ```powershell
   cd backend
   .\venv\Scripts\python.exe main.py
   ```
2. Start the LiveKit worker:
   ```powershell
   cd backend
   .\venv\Scripts\python.exe agent.py start
   ```
3. Serve the frontend:
   ```powershell
   cd frontend
   python -m http.server 8080 --bind 127.0.0.1
   ```
4. Open the app at `http://127.0.0.1:8080`.
5. Enter a room name and a participant name, then click Join Room.

## Expected behavior

- The AI participant appears in the room after the agent worker starts successfully.
- The active agent greets the user as Roxstar AI Dost.
- You can ask a question in English, Hindi, or Hinglish.
- The room can hand off to Sathi via a phrase such as `Talk to Sathi`.
- Switching back can be done with `Talk to Dost`.

## Troubleshooting

### Browser shows no AI participant

Check the worker process and port 8081. If a stale process is holding that port, terminate it and restart:

```powershell
Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
```

Then restart:

```powershell
cd backend
.\venv\Scripts\python.exe agent.py start
```

### Token server fails on port 8000

Check whether another Python process already owns port 8000:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

Terminate the stale process if needed, then restart the token server.

## LiveKit Cloud notes

- Keep the agent worker in a container that can connect to the LiveKit Cloud project.
- Keep the token API in a separate service or secure environment that can issue JWTs.
- Keep SSL verification enabled and use the Cloud project credentials from the environment.
