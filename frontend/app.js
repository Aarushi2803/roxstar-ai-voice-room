import {
    Room,
    RoomEvent,
    Track,
} from "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs";

let room = null;
let isMicEnabled = true;

const joinSection = document.getElementById("join-section");
const roomSection = document.getElementById("room-section");
const roomNameInput = document.getElementById("room-name");
const participantNameInput = document.getElementById("participant-name");
const joinButton = document.getElementById("join-button");
const leaveButton = document.getElementById("leave-button");
const micButton = document.getElementById("mic-button");
const participantsDiv = document.getElementById("participants");
const messagesDiv = document.getElementById("messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const statusEl = document.getElementById("connection-status");
const errorEl = document.getElementById("error-message");
const dostButton = document.getElementById("dost-button");
const sathiButton = document.getElementById("sathi-button");

function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.className = `status ${isError ? "error" : "connected"}`;
}

function clearError() {
    errorEl.textContent = "";
}

function showError(message) {
    errorEl.textContent = message;
    setStatus("Error", true);
}

function attachRemoteAudio(track) {
    const audioElement = track.attach();
    audioElement.autoplay = true;
    audioElement.style.width = "100%";
    audioElement.style.marginTop = "8px";
    document.body.appendChild(audioElement);
}

joinButton.addEventListener("click", async () => {
    const roomName = roomNameInput.value.trim();
    const participantName = participantNameInput.value.trim();

    if (!roomName || !participantName) {
        showError("Please enter both room name and participant name.");
        return;
    }

    try {
        joinButton.disabled = true;
        joinButton.textContent = "Joining...";
        clearError();
        setStatus("Requesting LiveKit token...");

        const response = await fetch("http://127.0.0.1:8000/token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                room_name: roomName,
                participant_name: participantName,
            }),
        });

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({ detail: "Could not get token" }));
            throw new Error(errorPayload.detail || "Could not get token");
        }

        const data = await response.json();
        room = new Room();

        room.on(RoomEvent.ParticipantConnected, (participant) => {
            console.log("Participant connected:", participant.identity);
            updateParticipants();
        });

        room.on(RoomEvent.ParticipantDisconnected, (participant) => {
            console.log("Participant disconnected:", participant.identity);
            updateParticipants();
        });

        room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log("Track subscribed:", track.kind, participant.identity);
            if (track.kind === Track.Kind.Audio) {
                attachRemoteAudio(track);
            }
        });

        room.on(RoomEvent.DataReceived, (payload, participant) => {
            const message = new TextDecoder().decode(payload);
            addMessage(participant ? participant.identity : "Unknown", message);
        });

        await room.connect(data.url, data.token);
        await room.localParticipant.setMicrophoneEnabled(true);
        isMicEnabled = true;
        micButton.textContent = "🎤 Mute";

        joinSection.style.display = "none";
        roomSection.style.display = "block";
        updateParticipants();
        setStatus("Connected");
        console.log("Connected to room!");
    } catch (error) {
        console.error(error);
        showError(error.message || "Could not join room. Check backend and console.");
        joinButton.disabled = false;
        joinButton.textContent = "Join Room";
    }
});

micButton.addEventListener("click", async () => {
    if (!room) return;

    isMicEnabled = !isMicEnabled;
    await room.localParticipant.setMicrophoneEnabled(isMicEnabled);
    micButton.textContent = isMicEnabled ? "🎤 Mute" : "🔇 Unmute";
    setStatus(isMicEnabled ? "Mic enabled" : "Mic muted");
});

leaveButton.addEventListener("click", async () => {
    if (room) {
        await room.disconnect();
        room = null;
    }

    roomSection.style.display = "none";
    joinSection.style.display = "block";
    participantsDiv.innerHTML = "";
    messagesDiv.innerHTML = "";
    joinButton.disabled = false;
    joinButton.textContent = "Join Room";
    setStatus("Disconnected");
    clearError();
});

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        sendMessage();
    }
});

dostButton.addEventListener("click", () => sendTextCommand("Talk to Dost"));
sathiButton.addEventListener("click", () => sendTextCommand("Talk to Sathi"));

async function sendTextCommand(text) {
    if (!room) return;
    const encoder = new TextEncoder();
    await room.localParticipant.publishData(encoder.encode(text), { reliable: true });
    addMessage(room.localParticipant.identity, text);
}

async function sendMessage() {
    if (!room) return;

    const message = messageInput.value.trim();
    if (!message) return;

    const encoder = new TextEncoder();
    await room.localParticipant.publishData(encoder.encode(message), { reliable: true });
    addMessage(room.localParticipant.identity, message);
    messageInput.value = "";
}

function updateParticipants() {
    if (!room) return;
    participantsDiv.innerHTML = "";

    const local = document.createElement("div");
    local.className = "participant";
    local.innerText = `👤 ${room.localParticipant.identity} (You)`;
    participantsDiv.appendChild(local);

    room.remoteParticipants.forEach((participant) => {
        const element = document.createElement("div");
        element.className = "participant";

        let label = participant.identity;
        if (participant.identity.includes("roxstar-dost")) {
            label = "🤖 Roxstar AI Dost";
        } else if (participant.identity.includes("roxstar-sathi")) {
            label = "🤖 Roxstar AI Sathi";
        }

        element.innerText = label;
        participantsDiv.appendChild(element);
    });
}

function addMessage(sender, message) {
    const element = document.createElement("div");
    element.className = "message";
    element.innerText = `${sender}: ${message}`;
    messagesDiv.appendChild(element);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

setStatus("Disconnected");
clearError();