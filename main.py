import asyncio
from heartbeat import Heartbeat
import websockets

ev = asyncio.get_event_loop()
        
conns = set()
Heartbeat.wsconns = conns

async def terr_connect(websocket, path):
    conns.add(websocket)
    try:
        await websocket.recv()
    finally:
        conns.remove(websocket)

start = websockets.serve(terr_connect, "localhost", 8080)
ev.run_until_complete(start)

Heartbeat.run_tasks()

ev.run_forever()