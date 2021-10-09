import asyncio
import aiohttp
from db import Connection
from configs import guilds
from network import Async
from .task import Task
import time
import sys
import datetime

class TerritoryTrackTask(Task):
    def __init__(self, sleep, wsconns):
        super().__init__(sleep)
        self.wsconns = wsconns
        
    def stop(self):
        self.finished = True
        self.aTask.cancel()

    def run(self):
        self.finished = False
        async def terr_tracker_task():
            while not self.finished:
                print(datetime.datetime.now().ctime(), "TERRITORY TRACK START")
                start = time.time()

                URL = "https://api.wynncraft.com/public_api.php?action=territoryList"
                terrs = (await Async.get(URL))["territories"]
                old_terrs = {x[0]: x[1] for x in Connection.execute("SELECT * FROM territories")}
                queries = []
                
                ws_payload = []

                insert_exchanges = []

                for ter in terrs:
                    if terrs[ter]["guild"] != old_terrs[ter]:
                        
                        ws_payload.append('{"defender": "%s", "territory": "%s", "attacker": "%s"}' % 
                                            (old_terrs[ter], ter, terrs[ter]["guild"]))
                        
                        insert_exchanges.append(f"({int(time.time())}, {old_terrs[ter]}, {terrs[ter]['guild']}, {ter})")
                        queries.append(f"UPDATE territories SET guild=\"{terrs[ter]['guild']}\" WHERE name=\"{ter}\";")

                if len(queries):
                    Connection.exec_all(queries)
                    Connection.execute("INSERT INTO terr_exchange VALUES "+','.join(insert_exchanges))

                for ws in self.wsconns:
                    await ws.send(f"[{','.join(ws_payload)}]")

                end = time.time()
                print(datetime.datetime.now().ctime(), "TERRITORY TRACKER", end-start, "s")

                await asyncio.sleep(self.sleep)
        
            print(datetime.datetime.now().ctime(), "TerritoryTrackTask finished")

        self.aTask = asyncio.get_event_loop().create_task(terr_tracker_task())