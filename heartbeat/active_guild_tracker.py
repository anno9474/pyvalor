import asyncio
import aiohttp
from db import Connection
from network import Async
from .task import Task
import datetime
import time
import sys
from log import logger

class ActiveGuildTrackerTask(Task):
    def __init__(self, sleep):
        super().__init__(sleep)
        
    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        async def active_guild_tracker():
            while not self.finished:
                logger.info("ACTIVE GUILD TRACKER START")
                start = time.time()

                query_1 = "DELETE FROM guild_autotrack_active;"
                query_2 = f"""
INSERT INTO guild_autotrack_active 
    (SELECT guild, COUNT(*) AS records
    FROM `player_delta_record` 
    WHERE guild<>"None" AND `time` >= {start - 3600*24*7}
    GROUP BY guild
    ORDER BY records DESC
    LIMIT 50);
"""
                Connection.exec_all([query_1, query_2]) 
                
                end = time.time()
                logger.info("ACTIVE GUILD TRACKER"+f" {end-start}s")

                await asyncio.sleep(self.sleep)
        
            logger.info("ActiveGuildTrackerTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(active_guild_tracker))