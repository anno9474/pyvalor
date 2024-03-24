import asyncio
import aiohttp
from db import Connection
from network import Async
from .task import Task
import datetime
import time
import sys
from log import logger

class GXPTrackerTaskGuildOnly(Task):
    def __init__(self, sleep):
        super().__init__(sleep)
        
    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        async def gxp_tracker_task():
            while not self.finished:
                logger.info("GXP START")
                start = time.time()

                URL = "https://api.wynncraft.com/v3/guild/Titans Valor"
                g = await Async.get(URL)
                members = []
                for rank in g["members"]:
                    if type(g["members"][rank]) != dict: continue
                    for member_name in g["members"][rank]:
                        members.append({"name": member_name, **g["members"][rank][member_name]})

                query = Connection.execute(f"SELECT * FROM user_total_xps")
                uuid_to_xp = {x[4]:x[:4] for x in query} # name xp lastxp guild
                
                new_queries = []
                new_members = []
                record_xps = []

                for m in members:
                    if not m["uuid"] in uuid_to_xp:
                        # new user
                        new_members.append(
                            f"(\"{m['name']}\",{m['contributed']},{m['contributed']},\"Titans Valor\",\"{m['uuid']}\")"
                        )
                    elif m["contributed"] < uuid_to_xp[m["uuid"]][2]:
                        # user rejoins
                        new_xp = uuid_to_xp[m["uuid"]][1]+m["contributed"]
                        new_queries.append(f"UPDATE user_total_xps SET xp={new_xp}, last_xp={m['contributed']} WHERE uuid=\"{m['uuid']}\";")
                        record_xps.append(f"(\"{m['uuid']}\", \"{m['name']}\", \"Titans Valor\", {m['contributed']}, {int(time.time())})")
                    elif m["contributed"] > uuid_to_xp[m["uuid"]][2]:
                        # user gains xp
                        delta = m["contributed"]-uuid_to_xp[m["uuid"]][2]
                        new_xp = uuid_to_xp[m["uuid"]][1]+delta
                        new_queries.append(f"UPDATE user_total_xps SET xp={new_xp}, last_xp={m['contributed']} WHERE uuid=\"{m['uuid']}\";")
                        record_xps.append(f"(\"{m['uuid']}\", \"{m['name']}\", \"Titans Valor\", {delta}, {int(time.time())})")
                
                if len(new_members):
                    Connection.execute(f"INSERT INTO user_total_xps VALUES {','.join(new_members)};")
                if len(record_xps):
                    Connection.execute(f"INSERT INTO member_record_xps VALUES {','.join(record_xps)};")
                if len(new_queries):
                    Connection.exec_all(new_queries)
                
                end = time.time()
                logger.info("GXP TRACKER"+f" {end-start}s")

                await asyncio.sleep(self.sleep)
        
            logger.info("GXPTrackerTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(gxp_tracker_task))