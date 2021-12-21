from .task import Task
from .terr_tracker import TerritoryTrackTask
from .player_activity import PlayerActivityTask
from .gxp_tracker import GXPTrackerTask
from .guild_activity import GuildActivityTask
from .player_stats import PlayerStatsTask
import asyncio

class Heartbeat:
    wsconns = {}
    tasks: Task = [
        TerritoryTrackTask(60, wsconns),
        PlayerActivityTask(3600),
        GXPTrackerTask(1800),
        GuildActivityTask(300),
        PlayerStatsTask(3600)
    ]
    
    @staticmethod
    def run_tasks():
        for t in Heartbeat.tasks:
            t.run()

    @staticmethod
    def stop_tasks():
        for t in Heartbeat.tasks:
            t.stop()