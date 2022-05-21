import asyncio
import aiohttp
from db import Connection
from network import Async
from .task import Task
import time
import datetime
import sys

class GuildTagTask(Task):
    def __init__(self, sleep):
        super().__init__(sleep)
        
    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        async def guild_tag_task():
            while not self.finished:
                # this entire routine will take like 10MB/beat
                print(datetime.datetime.now().ctime(), "GUILD TAG NAME TASK START")
                start = time.time()

                updated_guilds = set((await Async.get("https://api.wynncraft.com/public_api.php?action=guildList"))["guilds"]) # like 200K mem max
                res = Connection.execute("SELECT guild FROM guild_tag_name")
                current_guilds = set(x[0] for x in res)
                
                difference = updated_guilds - current_guilds
                print(datetime.datetime.now().ctime(), f"GUILD TAG NAME TASK: (difference: {len(difference)})")

                inserts = []

                for new_guild in difference:
                    req = await Async.get("https://api.wynncraft.com/public_api.php?action=guildStats&command="+new_guild)
                    tag = req["prefix"]
                    n_members = len(req["members"])
                    inserts.append(f"('{new_guild}','{tag}',{n_members})")
                    await asyncio.sleep(0.3)

                # batch insert if the # is too long for some reason
                for i in range(0, len(inserts), 50):
                    batch = inserts[i:max(i+50, len(inserts))]
                    Connection.execute("INSERT INTO guild_tag_name VALUES "+','.join(batch))

                end = time.time()
                print(datetime.datetime.now().ctime(), "GUILD TAG NAME TASK", end-start, "s")
                
                await asyncio.sleep(self.sleep)
        
            print(datetime.datetime.now().ctime(), "GuildTagTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(guild_tag_task))