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

load_dotenv()
api_key = os.environ["API_KEY"]

class PlayerStatsTask(Task):
    def __init__(self, sleep):
        super().__init__(sleep)
        
    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        idx = {'uuid': 0, 'firstjoin': 1, 'Decrepit Sewers': 2, 'Infested Pit': 3, 'Lost Sanctuary': 4, 'Underworld Crypt': 5, 'Sand-Swept Tomb': 6, 'Ice Barrows': 7, 'Undergrowth Ruins': 8, "Galleon's Graveyard": 9, 'Fallen Factory': 10, 'Eldritch Outlook': 11,'Corrupted Decrepit Sewers': 12, 'Corrupted Infested Pit': 13, 'Corrupted Lost Sanctuary': 14, 'Corrupted Underworld Crypt': 15, 'Corrupted Sand-Swept Tomb': 16, 'Corrupted Ice Barrows': 17, 'Corrupted Undergrowth Ruins': 18, 'itemsIdentified': 19, 'chestsFound': 20, 'blocksWalked': 21, 'logins': 22, 'playtime': 23, 'Alchemism': 24, 'Armouring': 25, 'combat': 26, 'Cooking': 27, 'Farming': 28, 'Fishing': 29, 'Jeweling': 30, 'Mining': 31, 'Scribing': 32, 'Tailoring': 33, 'Weaponsmithing': 34, 'Woodcutting': 35, 'Woodworking': 36, 'Nest of the Grootslangs': 37, 'The Canyon Colossus': 38, "mobsKilled": 39, "deaths": 40, "guild": 41, "Orphion's Nexus of Light": 42, "guild_rank": 43, "The Nameless Anomaly": 44, "Corrupted Galleon's Graveyard": 45}
        async def player_stats_task():
            while not self.finished:
                print(datetime.datetime.now().ctime(), "PLAYER STATS TRACK START")
                start = time.time()

                # online_all = await Async.get("https://api.wynncraft.com/v3/player")
                # online_all = {name for name in online_all.get("players", [])}
                online_all = await Async.get("https://api.wynncraft.com/public_api.php?action=onlinePlayers")
                online_all = {y for x in online_all for y in online_all[x] if not "request" in x}

                inserts = []
                uuid_name = []
                cnt = 0

                old_membership = {}
                res = Connection.execute("SELECT uuid, guild, guild_rank FROM `player_stats` WHERE guild IS NOT NULL and guild != 'None' and guild != ''")
                for uuid, guild, guild_rank in res:
                    old_membership[uuid] = [guild, guild_rank]

                res = Connection.execute("SELECT uuid, character_id, time, warcount FROM cumu_warcounts")
                prev_warcounts = {}
                for uuid, character_id, _, warcount in res:
                    if not uuid in prev_warcounts:
                        prev_warcounts[uuid] = {}
                    prev_warcounts[uuid][character_id] = warcount

                inserts_war_update = []
                inserts_war_deltas = []
                inserts_guild_log = []

                for player in online_all:
                    uri = f"https://api.wynncraft.com/v3/player/{player}?fullResult=True&apikey="+api_key
                    try:
                        stats = await Async.get(uri)
                    except:
                        print(uri, "borked")
                        continue
                    row = [0]*len(idx)
                    if not stats or not "uuid" in stats:
                        print(player, "no uuid, skip")
                        continue

                    uuid = stats["uuid"]
                    row[idx["uuid"]] = uuid

                    guild = None
                    guild_rank = None
                    if stats["guild"]:
                        guild = stats["guild"]["name"]
                        guild_rank = stats["guild"]["rank"]
                    
                    old_guild, old_rank = old_membership.get(uuid, [None, None])
                    if guild != old_guild:
                        inserts_guild_log.append(f"('{uuid}', '{old_guild}', '{old_rank}', '{guild}', {time.time()})")

                    row[idx["guild"]] = f'"{guild}"'
                    row[idx["guild_rank"]] = f'"{guild_rank}"'
                    row[idx["firstjoin"]] = datetime.datetime.fromisoformat(stats["firstJoin"]).timestamp()

                    character_data = stats["characters"]
                    for cl_name in character_data:
                        cl = character_data[cl_name]
                        cl_type = character_data["type"]

                        warcount = cl["wars"]
                        if uuid in prev_warcounts and cl_name in prev_warcounts[uuid]:
                            old_warcount = prev_warcounts[uuid][cl_name]
                            # if war count hasn't changed don't update a thing
                            if warcount != old_warcount:
                                inserts_war_deltas.append((uuid, cl_name, warcount-old_warcount, cl_type))
                                inserts_war_update.append((uuid, cl_name, warcount, cl_type))
                        else:
                            inserts_war_update.append((uuid, cl_name, warcount))

                        if cl["dungeons"]:
                            for dung, dung_count in cl["dungeons"]["list"].items():
                                if dung in idx:
                                    row[idx[dung]] += dung_count

                        if cl["raids"]:
                            for raid, raid_count in cl["raids"]["list"].items():
                                if raid in idx:
                                    row[idx[raid]] += raid_count

                        row[idx["itemsIdentified"]] += cl["itemsIdentified"]
                        row[idx["mobsKilled"]] += cl["mobsKilled"]
                        row[idx["chestsFound"]] += cl["chestsFound"]
                        row[idx["blocksWalked"]] += cl["blocksWalked"]
                        row[idx["logins"]] += cl["logins"]
                        row[idx["deaths"]] += cl["death"]
                        row[idx["playtime"]] += cl["playtime"]
                        # row[idx["combat"]] += cl["level"] todo combat lvl is gone
                        
                        for prof in cl["professions"]:
                            xp = cl["professions"][prof]["xpPercent"]
                            row[idx[prof]] += cl["professions"][prof]["level"] + (xp if xp else 0)/100
                    
                    inserts.append(row)
                    uuid_name.append((uuid, player))
                    cnt += 1

                    if (cnt % 50 == 0 or cnt == len(online_all)-1):
                        if inserts:
                            curr_time = time.time()
                            query_stats = "REPLACE INTO player_stats VALUES " + ','.join(f"('{x[0]}', {str(x[1])}, {','.join(map(str, x[2:]))})" for x in inserts)
                            query_uuid = "REPLACE INTO uuid_name VALUES " + ','.join(f"(\'{uuid}\',\'{name}\')" for uuid, name in uuid_name)
                            query_wars_update  = "REPLACE INTO cumu_warcounts VALUES " + ','.join(f"(\'{uuid}\',\'{character_id}\', {curr_time}, {warcount}, \'{cl_type}\')" 
                                                                                                    for uuid, character_id, warcount in inserts_war_update)
                            query_wars_delta  = "INSERT INTO delta_warcounts VALUES " + ','.join(f"(\'{uuid}\',\'{character_id}\', {curr_time}, {wardiff}, \'{cl_type}\')" 
                                                                        for uuid, character_id, wardiff in inserts_war_deltas)
                            if inserts_war_update:
                                Connection.execute(query_wars_update)
                                inserts_war_update = []
                            if inserts_war_deltas:
                                Connection.execute(query_wars_delta)
                                inserts_war_deltas = []

                            name_paren = ['\''+uuid+'\'' for uuid, _ in uuid_name]
                            old_names = Connection.execute(
                                f"SELECT uuid, name FROM uuid_name WHERE uuid IN ({','.join(name_paren)})")
                            old_names_dict = {uuid: old for uuid, old in old_names} # believe me, this way is still faster than tmp table join
                            uuid_name_history_update = []
                            for uuid, name in uuid_name:
                                if uuid in old_names_dict and old_names_dict[uuid] != name:
                                    uuid_name_history_update.append((uuid, old_names_dict[uuid], name, curr_time))
                            if uuid_name_history_update:
                                query_uuid_name_history = "INSERT INTO uuid_name_history VALUES " + \
                                    ','.join(f"('{uuid}','{old}','{new}',{curr_time})" for uuid, old, new, curr_time in uuid_name_history_update)
                                Connection.execute(query_uuid_name_history)

                            Connection.execute(query_stats)
                            Connection.execute(query_uuid)
                            
                        if inserts_guild_log:
                            query_guild_log = "INSERT INTO guild_join_log VALUES " + ','.join(inserts_guild_log)
                            Connection.execute(query_guild_log)
                            
                        inserts_guild_log = []
                        inserts = []
                        uuid_name = []

                    await asyncio.sleep(0.3)

                end = time.time()
                print(datetime.datetime.now().ctime(), "PLAYER STATS TASK", end-start, "s")
                
                await asyncio.sleep(self.sleep)
        
            print(datetime.datetime.now().ctime(), "PlayerStatsTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(player_stats_task))