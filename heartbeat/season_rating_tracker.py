import asyncio
import time
from db import Connection
from network import Async
from log import logger
from .task import Task
import datetime
import re

class SeasonRatingTrackerTask(Task):

    def __init__(self, sleep):
        super().__init__(sleep)

    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False

        async def season_rating_tracker_task():
            while not self.finished:
                logger.info("SR START")
                start = time.time()

                # Get the top 100 Guilds
                url = "https://api.wynncraft.com/v3/leaderboards/guildLevel?resultLimit=100"
                response = await Async.get(url)
                top_100_guilds = []
                guild_data = response.json()
                for guild_info in guild_data.get('data', []):
                    top_100_guilds.append(guild_info['name'])

                # Get current season number
                current_timestamp = datetime.datetime.now().timestamp()
                res = Connection.execute(
                    f"SELECT season_name FROM season_list "
                    f"WHERE start_time <= {current_timestamp} AND end_time >= {current_timestamp}"
                    f"ORDER BY start_time DESC LIMIT 1")
                current_season_name = res.fetchone()[0]
                season_number_match = re.search(r'\d+', current_season_name)
                current_season_number = int(season_number_match.group())

                for guild_name in top_100_guilds:
                    guild_url = f"https://api.wynncraft.com/v3/guild/{guild_name}"
                    guild_data = await Async.get(guild_url)
                    current_season_rating = guild_data['seasonRanks'].get(str(current_season_number), {}).get('rating', 0)

                    # Check for the last season rating for the guild
                    last_rating_result = Connection.execute(
                        f"SELECT SeasonRating FROM GuildSeasonRatings"
                        f"WHERE Guild = {guild_name} AND SeasonID = {current_season_number}"
                        f"ORDER BY Timestamp DESC LIMIT 1")

                    rating_delta = 0
                    if last_rating_result is not None:
                        last_rating = last_rating_result[0]
                        rating_delta = current_season_rating - last_rating

                    # Insert or update the season rating and delta
                    Connection.execute(
                        f"INSERT INTO GuildSeasonRAtings (Guild, SeasonID, SeasonRating, RatingDelta)"
                        f"VALUES({guild_name}, {current_season_number}, {current_season_rating}, {rating_delta})"
                    )
                    end = time.time()
                    await asyncio.sleep(0.3)

                logger.info("SR TRACKER" + f" {end - start}s")
                await asyncio.sleep(self.sleep)

            logger.info("SRTrackerTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(season_rating_tracker_task))
