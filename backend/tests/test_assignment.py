import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_detect_handoff_target_handles_common_requests():
    import agent

    assert agent.detect_handoff_target("Talk to Sathi") == "sathi"
    assert agent.detect_handoff_target("Sathi se baat karni hai") == "sathi"
    assert agent.detect_handoff_target("I want Dost") == "dost"
    assert agent.detect_handoff_target("hello there") is None


def test_session_memory_tracks_conversation_and_speaker_facts():
    import agent

    memory = agent.SessionMemory(room_id="room-1")
    memory.record_participant("p1", "Rahul")
    memory.record_participant("p2", "Priya")
    memory.record_fact("p1", "name", "Rahul")
    memory.record_fact("p2", "name", "Priya")
    memory.add_conversation_turn("p1", "My name is Rahul")

    assert memory.active_agent == "dost"
    assert memory.speaker_facts["p1"]["name"] == "Rahul"
    assert memory.conversation_history[-1]["text"] == "My name is Rahul"


def test_persona_instructions_include_language_behavior():
    import agent

    assert "Hindi" in agent.ROXSTAR_DOST_INSTRUCTIONS
    assert "Hinglish" in agent.ROXSTAR_DOST_INSTRUCTIONS
    assert "Hindi" in agent.ROXSTAR_SATHI_INSTRUCTIONS
    assert "Hinglish" in agent.ROXSTAR_SATHI_INSTRUCTIONS


def test_token_endpoint_rejects_invalid_inputs():
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)
    bad_name = client.post("/token", json={"room_name": "   ", "participant_name": "Aarushi"})
    assert bad_name.status_code == 400
    bad_participant = client.post("/token", json={"room_name": "demo-room", "participant_name": "   "})
    assert bad_participant.status_code == 400


def test_livekit_agents_can_be_constructed_with_llm():
    import agent

    memory = agent.SessionMemory(room_id="room-1")
    dost = agent.RoxstarDost(session_memory=memory, llm=object())
    sathi = agent.RoxstarSathi(session_memory=memory, llm=object())

    assert dost.session_memory is memory
    assert sathi.session_memory is memory
