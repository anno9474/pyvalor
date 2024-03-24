import asyncio
import aiohttp
from db import Connection
from network import Async
from .task import Task
import datetime
import time
import sys
from log import logger

class GXPTrackerTask(Task):
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

                res = Connection.execute("SELECT guild FROM guild_autotrack_active")
                guild_names = [row[0] for row in res]

                res = Connection.execute("SELECT uuid, value FROM player_global_stats WHERE label='gu_gxp'")
                prev_member_gxps = {}
                for uuid, value in res:
                    prev_member_gxps[uuid] = value

                for guild in guild_names:
                    URL = f"https://api.wynncraft.com/v3/guild/{guild}"
                    g = await Async.get(URL)
                    members = []
                    insert_gxp_deltas = []
                    update_gxp_values = []

                    for rank in g["members"]:
                        if type(g["members"][rank]) != dict: continue
                        for member_name in g["members"][rank]:
                            member_fields = g["members"][rank][member_name]
                            members.append({"name": member_name, **g["members"][rank][member_name]})
                            gxp_delta = member_fields["contributed"] - prev_member_gxps.get(member_fields["uuid"], member_fields["contributed"])
                            update_gxp_values.append((member_fields["uuid"], member_fields["contributed"]))
                            if gxp_delta > 0:
                                insert_gxp_deltas.append((member_fields["uuid"], gxp_delta))
                            
                    formatted_members = ','.join(f"(\'{guild}\', '{member['name']}')" for member in members)
                    update_members_query_1 = f"DELETE FROM guild_member_cache WHERE guild='{guild}'"
                    update_members_query_2 = f"INSERT INTO guild_member_cache (guild, name) VALUES {formatted_members}"
                    Connection.exec_all([update_members_query_1, update_members_query_2])

                    if insert_gxp_deltas:
                        query = "INSERT INTO player_delta_record VALUES " +\
                            ','.join(f"(\'{uuid}\', \'{guild}\', {start}, 'gu_gxp', {gxp_delta})" for uuid, gxp_delta in insert_gxp_deltas)
                        Connection.execute(query)
                    if update_gxp_values:
                        query = "REPLACE INTO player_global_stats VALUES " +\
                            ','.join(f"(\'{uuid}\', 'gu_gxp', {value})" for uuid, value in update_gxp_values)
                        Connection.execute(query)

                    end = time.time()
                    
                    await asyncio.sleep(0.3)
                    
                logger.info("GXP TRACKER"+f" {end-start}s")
                await asyncio.sleep(self.sleep)
        
            logger.info("GXPTrackerTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(gxp_tracker_task))