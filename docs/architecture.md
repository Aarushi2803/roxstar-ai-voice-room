# Architecture

## High-level flow

```text
Browser / user
    |
    v
LiveKit room
    |
    v
Token API (FastAPI)
    |
    +--> issues room JWT
    |
    v
Agent worker (LiveKit Agents)
    |
    v
AgentSession (shared room state)
    |
    +--> Roxstar AI Dost (voice Puck)
    |
    +--> Roxstar AI Sathi (voice Aoede)
    |
    v
Gemini realtime model
    |
    v
LiveKit audio output + text chat
```

## Responsibilities

- Token server: issues room join JWTs and validates room names.
- Worker: owns the room lifecycle and handles the active AI persona.
- Shared room state: keeps the live conversation, current agent, and any facts for the room session.
- Handoff: explicit tool calls move the conversation from Dost to Sathi and vice versa while preserving turn context.
- Audio: the active realtime model streams audio into the room.
- Browser: captures microphone input, plays remote audio, and renders status and chat.

## Why the AI was missing in the browser

The room UI only shows a remote participant after the LiveKit agent worker is healthy and the room has an active dispatched agent. If the worker was not started correctly or 8081 was occupied by a stale process, the browser connected but the remote AI never appeared.

## Reliability constraints

- No SSL verification is disabled.
- API keys and secrets remain server-side.
- Room validation rejects invalid names and missing participant data.
- Logs stay operational and minimal.
