# Testing and manual validation

## Automated checks

Run:

```bash
cd backend
./venv/Scripts/python.exe -m pytest tests -q
```

Current automated checks cover:

- invalid room name
- invalid participant name
- handoff detection
- speaker memory
- persona instructions
- token validation

## Manual voice checklist

### TEST 1 — Join room
- Enter a room name and participant name.
- Click Join Room.
- Confirm connection succeeds.

### TEST 2 — Dost greeting
- Confirm Dost greets the user.
- Confirm greeting is short and natural.

### TEST 3 — English question
- Ask: “What is machine learning?”
- Confirm English answer is in English.

### TEST 4 — Hindi question
- Ask: “Machine learning kya hoti hai?”
- Confirm natural Hindi response.

### TEST 5 — Hinglish question
- Ask: “Yaar mujhe internship ke liye kya prepare karna chahiye?”
- Confirm Hinglish answer.

### TEST 6 — Follow-up context
- Ask: “I am preparing for an internship.”
- Then ask: “What did I say I was preparing for?”
- Confirm memory recall.

### TEST 7 — Two human participants
- Open the room with two different participant names.
- Confirm both appear in the participant list.

### TEST 8 — Speaker-specific fact
- Provide a fact for User A and User B.
- Ask for the stored fact back.
- Confirm the AI can recall the right participant data.

### TEST 9 — Dost -> Sathi handoff
- Say: “Talk to Sathi.”
- Confirm Sathi appears as the active assistant.

### TEST 10 — Sathi -> Dost handoff
- Say: “Talk to Dost.”
- Confirm Dost becomes active again.

### TEST 11 — Interrupt AI while speaking
- Let the AI start speaking.
- Talk over it.
- Confirm interruption and new turn processing.

### TEST 12 — Mute/unmute microphone
- Toggle mic mute.
- Confirm UI state updates correctly.

### TEST 13 — Leave/rejoin
- Leave the room.
- Rejoin with the same or another room.
- Confirm room works again.

### TEST 14 — Gemini/network failure
- Disconnect networking or block API access.
- Confirm frontend shows a useful error.

### TEST 15 — Latency measurement
- Record timestamps at user speech start, speech detection, model start, response generation, and audio start.
- Confirm the total flow remains within a natural conversational range.

## Manual note

Actual microphone and audio behavior must be validated in a live browser; automated tests are used for logic, handoff, and session state checks, not browser audio capture.
