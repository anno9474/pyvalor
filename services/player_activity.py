import asyncio
import aiohttp
from db import Connection
from configs import guilds
from network import Async
import time
import datetime
import sys

SLEEP = 3600

async def player_activity_task():
    while True:
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
        
        await asyncio.sleep(SLEEP)