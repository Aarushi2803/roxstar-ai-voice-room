import os
import logging
import certifi
from dotenv import load_dotenv

load_dotenv("../.env")

# Fix Windows SSL certificate path BEFORE importing LiveKit
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["SSL_CERT_DIR"] = os.path.dirname(certifi.where())

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, RunContext, function_tool
from livekit.plugins import google

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("roxstar")


DOST_PROMPT = """
You are Roxstar AI Dost, a friendly male AI voice assistant.

Speak naturally in Hindi, Hinglish, or English depending on the user.

Keep responses short and conversational, usually 1-3 sentences.

Remember the conversation.

If the user clearly asks to speak with Sathi, transfer to Sathi.
"""


SATHI_PROMPT = """
You are Roxstar AI Sathi, a warm and cheerful female AI voice assistant.

Speak naturally in Hindi, Hinglish, or English depending on the user.

Keep responses short and conversational, usually 1-3 sentences.

Remember the conversation.

If the user clearly asks to speak with Dost, transfer to Dost.
"""


class RoxstarDost(Agent):

    def __init__(self):
        super().__init__(instructions=DOST_PROMPT)

    @function_tool()
    async def transfer_to_sathi(self, context: RunContext):
        """Transfer the conversation to Roxstar AI Sathi."""
        logger.info("[HANDOFF] Dost -> Sathi")

        return (
            RoxstarSathi(),
            "Sure, I am bringing Roxstar AI Sathi into the conversation.",
        )


class RoxstarSathi(Agent):

    def __init__(self):
        super().__init__(instructions=SATHI_PROMPT)

    @function_tool()
    async def transfer_to_dost(self, context: RunContext):
        """Transfer the conversation to Roxstar AI Dost."""
        logger.info("[HANDOFF] Sathi -> Dost")

        return (
            RoxstarDost(),
            "Sure, I am bringing Roxstar AI Dost back.",
        )


server = AgentServer()


@server.rtc_session(agent_name="roxstar-dost")
async def dost_session(ctx: agents.JobContext):

    logger.info("[JOB] STARTED room=%s", ctx.room.name)

    llm = google.realtime.RealtimeModel(
        model="gemini-live-2.5-flash-native-audio",
        voice="Puck",
        temperature=0.2,
        max_output_tokens=256,
    )

    session = AgentSession(llm=llm)

    await session.start(
        room=ctx.room,
        agent=RoxstarDost(),
    )

    logger.info("[ROOM] DOST JOINED room=%s", ctx.room.name)

    await session.generate_reply(
        instructions=(
            "Briefly greet the user as Roxstar AI Dost. "
            "Say you can chat in Hindi, Hinglish, or English."
        )
    )


def run_room_server():
    agents.cli.run_app(server)


if __name__ == "__main__":
    run_room_server()