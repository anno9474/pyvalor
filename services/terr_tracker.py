import asyncio
import aiohttp
from db import Connection
from configs import guilds
from network import Async
import time
import sys

SLEEP = 30

async def terr_tracker_task(wsconns):
    while True:
        URL = "https://api.wynncraft.com/public_api.php?action=territoryList"
        terrs = (await Async.get(URL))["territories"]
        old_terrs = {x[0]: x[1] for x in Connection.execute("SELECT * FROM territories")}
        queries = []
        
        ws_payload = []

        for ter in terrs:
            if terrs[ter]["guild"] != old_terrs[ter]:
                
                ws_payload.append('{"defender": "%s", "territory": "%s", "attacker": "%s"}' % 
                                    (old_terrs[ter], ter, terrs[ter]["guild"]))
                queries.append(f"UPDATE territories SET guild=\"{terrs[ter]['guild']}\" WHERE name=\"{ter}\";")

        if len(queries):
            Connection.exec_all(queries)

        for ws in wsconns:
            await ws.send(f"[{','.join(ws_payload)}]")
            
        await asyncio.sleep(SLEEP)