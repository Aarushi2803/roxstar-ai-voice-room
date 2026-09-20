import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

import certifi
from dotenv import load_dotenv

load_dotenv("../.env")
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("SSL_CERT_DIR", os.path.dirname(certifi.where()))

from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    RunContext,
    function_tool,
    llm,
    room_io,
)
from livekit.plugins import google


logger = logging.getLogger("roxstar.voice")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)


ROXSTAR_DOST_INSTRUCTIONS = """
You are Roxstar AI Dost, the default active voice assistant in a shared LiveKit room.

You understand English, Hindi, and Hinglish.

Language behavior:
- English -> English
- Hindi -> Hindi
- Hinglish -> Hinglish
- Never force a language change.

Personality:
- Friendly, casual, warm, helpful
- Natural Indian conversational style
- Keep replies short and human

Conversation rules:
- Respond in 1-3 short sentences unless the user asks for more detail.
- Remember prior conversation context.
- Answer follow-ups by using previous context.
- If the user clearly says to speak with Roxstar AI Sathi, call transfer_to_sathi.
- If the user shares their name, remember it in the session memory.
"""

ROXSTAR_SATHI_INSTRUCTIONS = """
You are Roxstar AI Sathi, a warm, cheerful, supportive female voice assistant.

You understand English, Hindi, and Hinglish.

Language behavior:
- English -> English
- Hindi -> Hindi
- Hinglish -> Hinglish
- Never force a language change.

Personality:
- Warm, friendly, supportive, cheerful
- Natural Indian conversational style
- Keep replies short and human

Conversation rules:
- Respond in 1-3 short sentences unless the user asks for more detail.
- Remember prior conversation context.
- Answer follow-ups by using previous context.
- If the user clearly says to speak with Roxstar AI Dost, call transfer_to_dost.
- If the user shares their name, remember it in the session memory.
"""


def detect_handoff_target(text: str) -> str | None:
    normalized = re.sub(r"[^a-zA-Z0-9\s]", " ", (text or "").lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if not normalized:
        return None

    sathi_markers = (
        "talk to sathi",
        "sathi se",
        "sathi ko",
        "speak with sathi",
        "i want sathi",
        "i want to speak with sathi",
        "talk to roxstar ai sathi",
        "sathi bulao",
    )
    dost_markers = (
        "talk to dost",
        "speak with dost",
        "i want dost",
        "i want to speak with dost",
        "talk to roxstar ai dost",
        "dost ko bulao",
    )

    if any(marker in normalized for marker in sathi_markers):
        return "sathi"
    if any(marker in normalized for marker in dost_markers):
        return "dost"
    return None


@dataclass
class SessionMemory:
    room_id: str = "default-room"
    active_agent: str = "dost"
    participants: dict[str, str] = field(default_factory=dict)
    speaker_facts: dict[str, dict[str, Any]] = field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)

    def record_participant(self, participant_id: str, display_name: str | None = None) -> None:
        self.participants[participant_id] = display_name or participant_id

    def add_conversation_turn(
        self,
        participant_id: str,
        text: str,
        *,
        role: str | None = None,
    ) -> None:
        if not text or not text.strip():
            return
        normalized_role = (role or "user").strip().lower()
        if normalized_role not in {"user", "assistant"}:
            normalized_role = "user"
        self.conversation_history.append(
            {
                "participant_id": participant_id,
                "text": text.strip(),
                "role": normalized_role,
                "timestamp": time.time(),
            }
        )

    def build_chat_context(self, limit: int = 12) -> llm.ChatContext:
        chat_ctx = llm.ChatContext()
        for turn in self.conversation_history[-limit:]:
            text = (turn.get("text") or "").strip()
            if not text:
                continue
            role = turn.get("role") or "user"
            chat_ctx.add_message(role=role, content=text)
        return chat_ctx

    def record_fact(self, participant_id: str, key: str, value: str) -> None:
        speaker_entry = self.speaker_facts.setdefault(participant_id, {})
        speaker_entry[key] = value

    def set_active_agent(self, agent_name: str) -> None:
        self.active_agent = agent_name


class LiveLatencyLogger:
    def __init__(self, memory: SessionMemory, session: AgentSession | None = None) -> None:
        self.memory = memory
        self.session = session

    def on_user_input_transcribed(self, event) -> None:
        transcript = (event.transcript or "").strip()
        if transcript:
            participant_id = event.speaker_id or "unknown"
            self.memory.record_participant(participant_id, participant_id)
            self.memory.add_conversation_turn(participant_id, transcript, role="user")
            if self.session is not None:
                try:
                    self.session.history.add_message(role="user", content=transcript)
                except Exception:
                    logger.warning("[VOICE] failed to persist transcript into LiveKit session history")
            logger.info("[VOICE] user turn detected: %s", transcript[:80])

    def on_agent_state_changed(self, event) -> None:
        if event.new_state == "thinking":
            logger.info("[LLM] model response started for %s", self.memory.active_agent)
        elif event.new_state == "speaking":
            logger.info("[VOICE] assistant audio started for %s", self.memory.active_agent)

    def on_speech_created(self, event) -> None:
        logger.info("[VOICE] speech created for %s using %s", self.memory.active_agent, event.source)


class RoxstarBaseAgent(Agent):
    def __init__(self, *, instructions: str, session_memory: SessionMemory, llm=None, chat_ctx=None):
        self.session_memory = session_memory
        self._llm = llm
        if chat_ctx is None:
            chat_ctx = session_memory.build_chat_context(limit=12)
        super().__init__(instructions=instructions, chat_ctx=chat_ctx)

    def set_voice(self, voice_name: str) -> None:
        if self._llm is not None and hasattr(self._llm, "update_options"):
            self._llm.update_options(voice=voice_name)

    @function_tool()
    async def remember_speaker_fact(self, participant_id: str, key: str, value: str):
        normalized_id = (participant_id or "unknown").strip() or "unknown"
        self.session_memory.record_participant(normalized_id)
        self.session_memory.record_fact(normalized_id, key, value)
        logger.info("[MEMORY] stored %s=%s for %s", key, value, normalized_id)
        return f"Saved {key} for {normalized_id}."


class RoxstarDost(RoxstarBaseAgent):
    def __init__(self, *, session_memory: SessionMemory, llm=None, chat_ctx=None):
        super().__init__(
            instructions=ROXSTAR_DOST_INSTRUCTIONS,
            session_memory=session_memory,
            llm=llm,
            chat_ctx=chat_ctx,
        )

    @function_tool()
    async def transfer_to_sathi(self, context: RunContext):
        """Transfer to Roxstar AI Sathi when the user clearly asks to speak with Sathi."""
        self.session_memory.set_active_agent("sathi")
        self.set_voice("Aoede")
        logger.info("[HANDOFF] Dost -> Sathi")
        return (
            RoxstarSathi(
                session_memory=self.session_memory,
                llm=self._llm,
                chat_ctx=self.chat_ctx.copy(exclude_instructions=True),
            ),
            "Sure, I’m bringing Roxstar AI Sathi into the conversation.",
        )


class RoxstarSathi(RoxstarBaseAgent):
    def __init__(self, *, session_memory: SessionMemory, llm=None, chat_ctx=None):
        super().__init__(
            instructions=ROXSTAR_SATHI_INSTRUCTIONS,
            session_memory=session_memory,
            llm=llm,
            chat_ctx=chat_ctx,
        )

    @function_tool()
    async def transfer_to_dost(self, context: RunContext):
        """Transfer back to Roxstar AI Dost when the user clearly asks to speak with Dost."""
        self.session_memory.set_active_agent("dost")
        self.set_voice("Puck")
        logger.info("[HANDOFF] Sathi -> Dost")
        return (
            RoxstarDost(
                session_memory=self.session_memory,
                llm=self._llm,
                chat_ctx=self.chat_ctx.copy(exclude_instructions=True),
            ),
            "Absolutely, I’m handing the conversation back to Roxstar AI Dost.",
        )


server = AgentServer()


@server.rtc_session(agent_name="roxstar-dost")
async def dost_session(ctx: agents.JobContext):
    session_memory = SessionMemory(room_id=(ctx.room.name or "room-default"))
    llm = google.realtime.RealtimeModel(
        model="gemini-live-2.5-flash-native-audio",
        voice="Puck",
        temperature=0.2,
        max_output_tokens=256,
    )
    session = AgentSession(llm=llm)
    latency_logger = LiveLatencyLogger(session_memory, session)

    session.on("user_input_transcribed", latency_logger.on_user_input_transcribed)
    session.on("agent_state_changed", latency_logger.on_agent_state_changed)
    session.on("speech_created", latency_logger.on_speech_created)

    await session.start(
        room=ctx.room,
        agent=RoxstarDost(session_memory=session_memory, llm=llm),
        room_options=room_io.RoomOptions(
            text_input=True,
            audio_input=True,
            text_output=True,
            audio_output=True,
        ),
    )

    logger.info("[ROOM] room=%s active_agent=%s", session_memory.room_id, session_memory.active_agent)
    await session.generate_reply(
        instructions="""
Briefly greet the user as Roxstar AI Dost.
Mention that you can chat in Hindi, Hinglish, or English.
Keep the greeting short and natural.
"""
    )


def run_room_server() -> None:
    agents.cli.run_app(server)


if __name__ == "__main__":
    run_room_server()