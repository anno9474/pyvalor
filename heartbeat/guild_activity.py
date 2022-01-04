import asyncio
import aiohttp
from db import Connection
from configs import guilds
from network import Async
from .task import Task
import time
import datetime
import sys

class GuildActivityTask(Task):
    def __init__(self, sleep, wsconns):
        super().__init__(sleep)
        self.wsconns = wsconns
        
    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        async def guild_activity_task():
            while not self.finished:
                print(datetime.datetime.now().ctime(), "GUILD ACTIVITY TRACK START")
                start = time.time()

                current_guild_members = (await Async.get("https://api.wynncraft.com/public_api.php?action=guildStats&command=Titans%20Valor"))["members"]
                current_guild_members = {x["name"] for x in current_guild_members}
                old_guild_members = {x[1] for x in Connection.execute(f"SELECT * FROM guild_member_cache") if x[0] == "Titans Valor"}
                left = [f'"{x}"' for x in old_guild_members-current_guild_members]
                join = [f'"{x}"' for x in current_guild_members-old_guild_members]
                
                for ws in self.wsconns:
                    if left or join:
                        await ws.send('{"type":"join","leave":'+f'[{",".join(left)}],"join":'+f'[{",".join(join)}]' + "}")

                Connection.execute("DELETE FROM guild_member_cache WHERE guild='Titans Valor'")
                Connection.execute("INSERT INTO guild_member_cache VALUES "+",".join(f"('Titans Valor','{x}')" for x in current_guild_members))
                
                online_all = await Async.get("https://api.wynncraft.com/public_api.php?action=onlinePlayers")
                online_all = {y for x in online_all for y in online_all[x] if not "request" in x}

                inserts = []

                # get cached members
                cached = {m: g for g, m in Connection.execute("SELECT * FROM guild_member_cache")}
                guild_member_cnt = {g: 0 for g in guilds}
                
                for m in cached.keys() & online_all:
                    guild_member_cnt[cached[m]] += 1

                now = int(time.time())
                Connection.execute("INSERT INTO guild_member_count VALUES" +
                    ','.join(f"(\"{guild}\", {guild_member_cnt[guild]}, {now})" for guild in guild_member_cnt))

                end = time.time()
                print(datetime.datetime.now().ctime(), "GUILD ACTIVITY TASK", end-start, "s")
                
                await asyncio.sleep(self.sleep)
        
            print(datetime.datetime.now().ctime(), "GuildActivityTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(guild_activity_task))