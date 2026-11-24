import asyncio
import json
import sys
import time

from dotenv import load_dotenv
from livekit import api

from scenarios import SCENARIOS

load_dotenv()


async def run_one(lk: api.LiveKitAPI, name: str):
    room = f"call-{name}-{int(time.time())}"
    await lk.room.create_room(api.CreateRoomRequest(name=room, empty_timeout=30))
    await lk.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="patient-bot", room=room, metadata=json.dumps({"scenario": name})
        )
    )
    print(f"dialing: {name}")
    deadline = time.time() + 330
    while time.time() < deadline:
        await asyncio.sleep(5)
        rooms = await lk.room.list_rooms(api.ListRoomsRequest(names=[room]))
        if not rooms.rooms:
            break
    print(f"finished: {name}")


async def main():
    names = sys.argv[1:] or list(SCENARIOS)
    unknown = [n for n in names if n not in SCENARIOS]
    if unknown:
        sys.exit(f"unknown scenarios: {unknown}")
    async with api.LiveKitAPI() as lk:
        for n in names:
            await run_one(lk, n)
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
