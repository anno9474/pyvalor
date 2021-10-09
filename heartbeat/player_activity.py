import asyncio
import aiohttp
from db import Connection
from configs import guilds
from network import Async
from .task import Task
import time
import datetime
import sys

class PlayerActivityTask(Task):
    def __init__(self, sleep):
        super().__init__(sleep)
        
    def stop(self):
        self.finished = True
        self.aTask.cancel()

    def run(self):
        self.finished = False
        async def player_activity_task():
            while not self.finished:
                print(datetime.datetime.now().ctime(), "PLAYER ACTIVITY TRACK START")
                start = time.time()

                URL = "https://api.wynncraft.com/public_api.php?action=guildStats&command="
                online_all = await Async.get("https://api.wynncraft.com/public_api.php?action=onlinePlayers")
                online_all = {y for x in online_all for y in online_all[x] if not "request" in x}
                inserts = []
                for guild in guilds:
                    g = await Async.get(URL+guild)
                    members = {x["name"]: x["uuid"] for x in g["members"]}
                    for name in members:
                        if name in online_all:
                            inserts.append(f"(\"{name}\", \"{guild}\", {int(time.time())}, \"{members[name]}\")")

                Connection.execute(f"INSERT INTO activity_members VALUES {','.join(inserts)}")

                end = time.time()
                print(datetime.datetime.now().ctime(), "PLAYER ACTIVITY TASK", end-start, "s")
                
                await asyncio.sleep(self.sleep)
        
            print(datetime.datetime.now().ctime(), "PlayerActivityTask finished")

        self.aTask = asyncio.get_event_loop().create_task(player_activity_task())