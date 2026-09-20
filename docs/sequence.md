# Sequence flow

## User joins

1. Frontend enters room name + participant name.
2. Frontend requests a token from the FastAPI `/token` endpoint.
3. FastAPI validates input and creates a LiveKit access token.
4. Frontend connects to LiveKit room with the returned token.
5. Agent is dispatched into the room.
6. Dost becomes the default active assistant.
7. Greeting is generated and audio is returned through LiveKit.

## Normal conversation

1. User speaks in the room.
2. LiveKit/Gemini realtime server detects the turn boundary.
3. LLM generates a response using shared context and prompt instructions.
4. The assistant returns audio via the realtime model.
5. The user hears the audio in the room.

## Handoff

1. User says a phrase such as “Talk to Sathi”.
2. Handoff detection identifies the target.
3. The active assistant triggers the transfer to Sathi.
4. Conversation state and session memory remain attached to the room.
5. Sathi speaks and continues the conversation.

## Interruption

1. AI is speaking.
2. User starts speaking.
3. LiveKit-supported interruption path detects overlap.
4. Active speech is interrupted.
5. The new user turn is processed and a new model response begins.

## Failure handling

1. Missing or invalid token input is rejected by the API.
2. Connection issues are surfaced through frontend status/error UI.
3. SSL errors are reduced by setting `SSL_CERT_FILE` to the local certifi bundle.
4. Agent or network problems are logged with clear operational context.
