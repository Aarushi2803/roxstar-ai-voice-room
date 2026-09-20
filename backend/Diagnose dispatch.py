"""
Diagnose the LiveKit agent dispatch chain WITHOUT the browser.
 
Put this next to main.py / agent.py (roxstar-ai-voice-room/backend/), activate
the venv, make sure your agent worker is running in another terminal, then:
 
    python diagnose_dispatch.py                       # fresh test room + dispatch
    python diagnose_dispatch.py --agent roxstar-dost  # explicit agent name
    python diagnose_dispatch.py --room my-room --no-create   # inspect existing room only
 
It prints which stage fails: dispatch stored -> job created -> job running ->
agent participant present in room. It never prints secrets.
"""
import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
 
try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv not installed; rely on the real environment
    load_dotenv = None
 
from livekit import api
 
JOB_STATUS = {0: "PENDING", 1: "RUNNING", 2: "SUCCESS", 3: "FAILED"}
KIND = {0: "STANDARD", 1: "INGRESS", 2: "EGRESS", 3: "SIP", 4: "AGENT"}
 
 
def load_env() -> None:
    if load_dotenv is None:
        return
    here = Path(__file__).resolve().parent
    for candidate in (here / ".env", here.parent / ".env", Path.cwd() / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)
            print(f"[env] loaded {candidate}")
 
 
async def snapshot(lkapi: api.LiveKitAPI, room: str):
    """Return (dispatch_lines, participant_lines, has_agent, job_failed)."""
    dispatch_lines, participant_lines = [], []
    has_agent, job_failed = False, False
 
    try:
        dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room)
    except Exception as e:  # noqa: BLE001 - we want to see everything
        dispatches = []
        dispatch_lines.append(f"list_dispatch error: {type(e).__name__}: {e}")
 
    for d in dispatches:
        jobs = list(getattr(getattr(d, "state", None), "jobs", []) or [])
        dispatch_lines.append(f"dispatch id={d.id} agent_name={d.agent_name!r} jobs={len(jobs)}")
        for j in jobs:
            st = getattr(j, "state", None)
            status = JOB_STATUS.get(getattr(st, "status", -1), "?")
            err = getattr(st, "error", "") or ""
            dispatch_lines.append(f"   job id={j.id} status={status} error={err!r}")
            if status == "FAILED":
                job_failed = True
 
    try:
        resp = await lkapi.room.list_participants(api.ListParticipantsRequest(room=room))
        for p in resp.participants:
            kind = KIND.get(p.kind, str(p.kind))
            tracks = [str(t.type) for t in p.tracks]
            participant_lines.append(f"participant identity={p.identity!r} kind={kind} tracks={tracks}")
            if kind == "AGENT":
                has_agent = True
    except Exception as e:  # noqa: BLE001
        participant_lines.append(f"list_participants: {type(e).__name__}: {e}")
 
    return dispatch_lines, participant_lines, has_agent, job_failed
 
 
async def main(args: argparse.Namespace) -> int:
    load_env()
    url = os.getenv("LIVEKIT_URL")
    key = os.getenv("LIVEKIT_API_KEY")
    secret = os.getenv("LIVEKIT_API_SECRET")
    missing = [n for n, v in (("LIVEKIT_URL", url), ("LIVEKIT_API_KEY", key), ("LIVEKIT_API_SECRET", secret)) if not v]
    if missing:
        print(f"[FAIL] missing env vars: {', '.join(missing)}")
        return 2
 
    # Compare these two lines with what the worker prints/uses. A mismatch
    # means main.py and agent.py are talking to DIFFERENT LiveKit projects.
    print(f"[env] LIVEKIT_URL host = {urlparse(url).hostname}")
    print(f"[env] LIVEKIT_API_KEY ends with ...{key[-4:]}")
 
    room = args.room or f"diag-{int(time.time())}"
    created_here = False
    lkapi = api.LiveKitAPI(url=url, api_key=key, api_secret=secret)
    try:
        if not args.no_create:
            print(f"[step 1] create_dispatch agent_name={args.agent!r} room={room!r}")
            d = await lkapi.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(agent_name=args.agent, room=room)
            )
            created_here = True
            print(f"[step 1] OK dispatch id={d.id}")
        else:
            print(f"[step 1] skipped (inspecting existing room {room!r})")
 
        print(f"[step 2] watching for up to {args.wait}s ...")
        last = None
        has_agent = job_failed = False
        dl = pl = []
        deadline = time.time() + args.wait
        while time.time() < deadline:
            dl, pl, has_agent, job_failed = await snapshot(lkapi, room)
            state = (tuple(dl), tuple(pl))
            if state != last:
                print(f"--- t+{int(args.wait - (deadline - time.time()))}s ---")
                for line in dl + pl:
                    print("  ", line)
                last = state
            if has_agent or job_failed:
                break
            await asyncio.sleep(1)
 
        print("\n================ VERDICT ================")
        jobs_seen = any("job id=" in l for l in dl)
        running = any("status=RUNNING" in l for l in dl)
        pending = any("status=PENDING" in l for l in dl)
 
        if has_agent:
            print("PASS: agent participant is in the room. Backend chain works.")
            print("      If the browser still doesn't show it, the bug is in the FRONTEND")
            print("      (participants that joined BEFORE you are not in ParticipantConnected events;")
            print("      iterate room.remoteParticipants after connect, and handle TrackSubscribed).")
        elif job_failed:
            print("FAIL at job execution: a job was created but FAILED (see error above).")
            print("      Read the worker terminal for the traceback.")
        elif not dl or not any("dispatch id=" in l for l in dl):
            print("FAIL at dispatch: no dispatch stored for this room. Check room name / API credentials.")
        elif not jobs_seen or pending:
            print("FAIL at worker matching: dispatch exists but NO worker accepted a job.")
            print("      Likely: worker not running, worker in a different LiveKit project,")
            print(f"      or worker's agent_name != {args.agent!r}, or worker rejected the job (request_fnc).")
        elif running:
            print("FAIL inside entrypoint: job is RUNNING but no agent participant ever joined.")
            print("      The entrypoint is hanging/crashing before ctx.connect() or session.start().")
            print("      Read the worker terminal for exceptions (Gemini model/key errors are common).")
        else:
            print("INCONCLUSIVE: see the snapshots above.")
        return 0 if has_agent else 1
    finally:
        if created_here and not args.keep:
            try:
                await lkapi.room.delete_room(api.DeleteRoomRequest(room=room))
                print(f"[cleanup] deleted test room {room!r}")
            except Exception as e:  # noqa: BLE001
                print(f"[cleanup] could not delete room: {type(e).__name__}: {e}")
        await lkapi.aclose()
 
 
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--agent", default="roxstar-dost")
    p.add_argument("--room", default=None)
    p.add_argument("--wait", type=int, default=25)
    p.add_argument("--no-create", action="store_true", help="don't create a dispatch; just inspect --room")
    p.add_argument("--keep", action="store_true", help="don't delete the test room afterwards")
    sys.exit(asyncio.run(main(p.parse_args())))
 
