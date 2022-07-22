import asyncio
from heartbeat import Heartbeat
import websockets

ev = asyncio.get_event_loop()

async def terr_connect(websocket, path):
    Heartbeat.wsconns.add(websocket)
    try:
        await websocket.recv()
    finally:
        Heartbeat.wsconns.remove(websocket)

start = websockets.serve(terr_connect, "localhost", 8090)
ev.run_until_complete(start)

Heartbeat.run_tasks()

ev.run_forever()