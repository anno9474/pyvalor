from .task import Task
from .terr_tracker import TerritoryTrackTask
from .player_activity import PlayerActivityTask
from .gxp_tracker import GXPTrackerTask
from .guild_activity import GuildActivityTask
from .player_stats import PlayerStatsTask
from .guild_tag import GuildTagTask
import asyncio

class Heartbeat:
    wsconns = set()
    tasks: Task = [
        # TerritoryTrackTask(60, wsconns),
        # PlayerActivityTask(3600),
        # GXPTrackerTask(1800),
        # GuildActivityTask(300, wsconns),
        # PlayerStatsTask(3600),
        GuildTagTask(3600)
    ]
    
    @staticmethod
    def run_tasks():
        for t in Heartbeat.tasks:
            t.run()

    @staticmethod
    def stop_tasks():
        for t in Heartbeat.tasks:
            t.stop()