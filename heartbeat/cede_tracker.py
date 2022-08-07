import asyncio
import aiohttp
from db import Connection
from network import Async
from .task import Task
import time
import sys
import datetime

class CedeTrackTask(Task):
    def __init__(self, sleep):
        super().__init__(sleep)
        self.last_recorded = {}

        # data is collected in terr tracker heartbeat
        self.valor_delta = {}
        
    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        async def terr_tracker_task():
            while not self.finished:
                print(datetime.datetime.now().ctime(), "CEDE TRACKER START")
                start = time.time()

                URL = "https://api.wynncraft.com/public_api.php?action=statsLeaderboard&type=guild&timeframe=alltime"
                data = (await Async.get(URL))["data"]

                ally_stats = Connection.execute("SELECT * FROM ally_stats")

                api_warcount = {}
                for guild_rec in data:
                    api_warcount[guild_rec["name"]] = guild_rec.get("warCount", 0)

                # get difference in wars
                api_delta = {}
                for guild in api_warcount:
                    if not guild in self.last_recorded:
                        api_delta[guild] = 0
                        continue
                    api_delta[guild] = max(api_warcount[guild]-self.last_recorded[guild], 0)
                
                help_change = {}

                # compare difference between pyvalor's tracking with what api reports
                for guild in api_warcount:
                    api_guild_delta = api_delta[guild]
                    valor_guild_delta = self.valor_delta.get(guild, 0)

                    help_diff = valor_guild_delta-api_guild_delta # subtract this from helps
                    help_change[guild] = help_diff
                
                changes = []
                for guild, ffa, reclaim, adj_help, other, nom_help in ally_stats:
                    if not guild in help_change: continue
                    adj_help -= help_change[guild]
                    changes.append(f"('{guild}', {ffa}, {reclaim}, {adj_help}, {other}, {nom_help})")

                replace_query = "REPLACE INTO ally_stats VALUES " + ','.join(changes)
                Connection.execute(replace_query)

                self.last_recorded = api_warcount
                self.valor_delta = {}

                end = time.time()
                print(datetime.datetime.now().ctime(), "CEDE TRACKER", end-start, "s")

                await asyncio.sleep(self.sleep)
        
            print(datetime.datetime.now().ctime(), "Cede Tracker Task finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(terr_tracker_task))
        