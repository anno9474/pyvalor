import asyncio
import aiohttp
from db import Connection
from network import Async
from .task import Task
import time
import datetime
import sys
from dotenv import load_dotenv
import json
import os
from log import logger

load_dotenv()
api_key = os.environ["API_KEY"]

class WCPlayersTask(Task):
    def __init__(self, sleep):
        super().__init__(sleep)
        
    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        async def player_stats_task():
            while not self.finished:
                break # I don't think this is used anymore?
                logger.info("WC PLAYERS TRACK START")
                start = time.time()

                online_all = await Async.get("https://api.wynncraft.com/public_api.php?action=onlinePlayers&apikey="+api_key)
                online_all = [(int(wc[2:]), player_name, start) for wc in online_all for player_name in online_all[wc] if not "request" in wc]

                batch_size = 300
                for i in range(0, len(online_all), batch_size):
                    insert_slice = [f"({wc},'{name}',{time_rec})" for wc, name, time_rec in online_all[i:min(len(online_all), i+batch_size)]]
                    Connection.execute(f"INSERT INTO wc_players VALUES {','.join(insert_slice)}")

                end = time.time()
                logger.info("WC PLAYERS TASK"+f" {end-start}s")
                
                await asyncio.sleep(self.sleep)
        
            logger.info("WCPlayers finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(player_stats_task))