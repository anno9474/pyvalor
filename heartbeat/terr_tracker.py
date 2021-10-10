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
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        async def terr_tracker_task():
            while not self.finished:
                print(datetime.datetime.now().ctime(), "TERRITORY TRACK START")
                start = time.time()

                URL = "https://api.wynncraft.com/public_api.php?action=territoryList"
                terrs = (await Async.get(URL))["territories"]
                old_terrs = {x[0]: x[1] for x in Connection.execute("SELECT * FROM territories")}

                guild_terr_cnt = {terrs[terr]["guild"]: 0 for terr in terrs}

                queries = []
                ws_payload = []
                insert_exchanges = []

                for ter in terrs:
                    guild_terr_cnt[terrs[ter]["guild"]] += 1
                    if not ter in old_terrs:
                        # new territory. should rarely happen
                        queries.append(f"INSERT INTO territories VALUES (\"{ter}\", \"{terrs[ter]['guild']}\", \"none\");")

                    elif terrs[ter]["guild"] != old_terrs[ter]:
                        
                        ws_payload.append('{"defender": "%s", "territory": "%s", "attacker": "%s"}' % 
                                            (old_terrs[ter], ter, terrs[ter]["guild"]))
                        
                        acquired = terrs[ter]["acquired"]
                        acquired = datetime.datetime.strptime(acquired, "%Y-%m-%d %H:%M:%S")
                        
                        insert_exchanges.append(f"({int(acquired.timestamp())}, \"{old_terrs[ter]}\", \"{terrs[ter]['guild']}\", \"{ter}\")")
                        queries.append(f"UPDATE territories SET guild=\"{terrs[ter]['guild']}\" WHERE name=\"{ter}\";")
            

                if len(queries):
                    Connection.exec_all(queries)
                    Connection.execute("INSERT INTO terr_exchange VALUES "+','.join(insert_exchanges))
                
                Connection.execute("INSERT INTO terr_count VALUES "+
                    ','.join(f"({int(time.time())}, \"{k}\", {guild_terr_cnt[k]})" for k in guild_terr_cnt))

                for ws in self.wsconns:
                    await ws.send(f"[{','.join(ws_payload)}]")

                end = time.time()
                print(datetime.datetime.now().ctime(), "TERRITORY TRACKER", end-start, "s")

                await asyncio.sleep(self.sleep)
        
            print(datetime.datetime.now().ctime(), "TerritoryTrackTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(terr_tracker_task()))
        