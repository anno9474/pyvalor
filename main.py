import asyncio
from services import player_activity_task, gxp_tracker_task, terr_tracker_task
import websockets

ev = asyncio.get_event_loop()
        
# ev.run_until_complete(player_activity_task())

ev.create_task(player_activity_task())
ev.create_task(gxp_tracker_task())

conns = set()
async def terr_connect(websocket, path):
    conns.add(websocket)
    try:
        await websocket.recv()
    finally:
        conns.remove(websocket)

start = websockets.serve(terr_connect, "localhost", 8080)
ev.run_until_complete(start)
ev.create_task(terr_tracker_task(conns))
ev.run_forever()