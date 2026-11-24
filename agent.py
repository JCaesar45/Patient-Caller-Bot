import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import cartesia, deepgram, openai, silero

from scenarios import build_prompt

load_dotenv()
log = logging.getLogger("patient-bot")

MAX_CALL_SECONDS = 240
TRANSCRIPT_DIR = Path("transcripts")


class Patient(Agent):
    def __init__(self, scenario: str, room_name: str, lk: api.LiveKitAPI):
        super().__init__(instructions=build_prompt(scenario))
        self._room_name = room_name
        self._lk = lk

    @function_tool
    async def end_call(self, context: RunContext):
        """Hang up. Only call this after you have said goodbye out loud."""
        asyncio.create_task(self._hangup())
        return "Hanging up."

    async def _hangup(self):
        await asyncio.sleep(3)
        try:
            await self._lk.room.delete_room(api.DeleteRoomRequest(room=self._room_name))
        except Exception:
            log.exception("delete_room failed")


async def start_recording(ctx: JobContext, tag: str):
    s3 = api.S3Upload(
        access_key=os.environ["S3_ACCESS_KEY"],
        secret=os.environ["S3_SECRET"],
        bucket=os.environ["S3_BUCKET"],
        endpoint=os.environ.get("S3_ENDPOINT", ""),
        region=os.environ.get("S3_REGION", "auto"),
        force_path_style=True,
    )
    req = api.RoomCompositeEgressRequest(
        room_name=ctx.room.name,
        audio_only=True,
        file_outputs=[
            api.EncodedFileOutput(
                file_type=api.EncodedFileType.OGG,
                filepath=f"recordings/{tag}.ogg",
                s3=s3,
            )
        ],
    )
    await ctx.api.egress.start_room_composite_egress(req)


async def entrypoint(ctx: JobContext):
    meta = json.loads(ctx.job.metadata)
    scenario = meta["scenario"]
    number = os.environ["TARGET_NUMBER"]
    tag = f"{scenario}-{datetime.now():%Y%m%d-%H%M%S}"
    lines: list[str] = []
    t0 = asyncio.get_event_loop().time()

    await ctx.connect()
    await start_recording(ctx, tag)

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="en-US"),
        llm=openai.LLM(model="gpt-4o-mini", temperature=0.7),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        allow_interruptions=True,
        min_endpointing_delay=0.7,
    )

    @session.on("conversation_item_added")
    def _on_item(ev):
        text = ev.item.text_content
        if not text:
            return
        who = "PATIENT(bot)" if ev.item.role == "assistant" else "AGENT"
        stamp = asyncio.get_event_loop().time() - t0
        lines.append(f"[{int(stamp // 60):02d}:{stamp % 60:04.1f}] {who}: {text}")

    async def save():
        TRANSCRIPT_DIR.mkdir(exist_ok=True)
        (TRANSCRIPT_DIR / f"{tag}.txt").write_text("\n".join(lines) + "\n")

    ctx.add_shutdown_callback(save)

    await session.start(agent=Patient(scenario, ctx.room.name, ctx.api), room=ctx.room)

    await ctx.api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=os.environ["SIP_OUTBOUND_TRUNK_ID"],
            sip_call_to=number,
            room_name=ctx.room.name,
            participant_identity="test-line",
            participant_name="Test line",
            wait_until_answered=True,
        )
    )

    await asyncio.sleep(MAX_CALL_SECONDS)
    await ctx.api.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="patient-bot"))
