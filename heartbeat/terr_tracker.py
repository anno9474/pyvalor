import asyncio
import aiohttp
from db import Connection
from network import Async
from .task import Task
import time
import sys
import datetime

class TerritoryTrackTask(Task):
    def __init__(self, sleep, wsconns, cede_task):
        super().__init__(sleep)
        self.wsconns = wsconns
        self.cede_task = cede_task
        
    def stop(self):
        self.finished = True
        self.continuous_task.cancel()

    def run(self):
        self.finished = False
        async def terr_tracker_task():
            while not self.finished:
                print(datetime.datetime.now().ctime(), "TERRITORY TRACK START")
                start = time.time()

                URL = "https://api.wynncraft.com/public_api.php?action=territoryList"
                terrs = (await Async.get(URL))["territories"]
                old_terrs = {x[0]: x[1] for x in Connection.execute("SELECT * FROM territories")}

                guild_terr_cnt = {terrs[terr]["guild"]: 0 for terr in terrs}

                queries = []
                ws_payload = []
                insert_exchanges = []

                claim_res = Connection.execute("SELECT * FROM ally_claims")
                claim_owner = {claim: guild for guild, claim in claim_res}
                allied_guilds = {*claim_owner.values()}
                    
                ally_stats_res = Connection.execute("SELECT * FROM ally_stats")
                ally_stats = {}
                for old_ally_record in ally_stats_res:
                    ally_stats[old_ally_record[0]] = list(old_ally_record[1:])

                if "N/A" in allied_guilds: allied_guilds.remove("N/A")

                for ter in terrs:
                    guild_terr_cnt[terrs[ter]["guild"]] += 1
                    if not ter in old_terrs:
                        # new territory. should rarely happen
                        queries.append(f"INSERT INTO territories VALUES (\"{ter}\", \"{terrs[ter]['guild']}\", \"none\");")

                    elif terrs[ter]["guild"] != old_terrs[ter]:
                        defender, attacker = old_terrs[ter], terrs[ter]['guild']
                        ws_payload.append('{"defender": "%s", "territory": "%s", "attacker": "%s"}' % 
                                            (defender, ter, attacker))
                        # Alliance stuff
                        if attacker in allied_guilds:
                            if not attacker in ally_stats:
                                # { "FFA":0, "Reclaim":0, "adj help":0, "Other":0, "nom help": 0 }
                                ally_stats[attacker] = [0]*5
                        
                            terr_owner = claim_owner.get(ter, "null") # null case if new ter isn't registered yet
                            ally_stats[attacker][0] += terr_owner == "null"
                            ally_stats[attacker][1] += terr_owner == attacker

                            # adjusted helps (before adjusting)
                            is_help = attacker != terr_owner and terr_owner != "null" and terr_owner in allied_guilds and not defender in allied_guilds
                            ally_stats[attacker][2] += is_help
                            # nom help
                            ally_stats[attacker][4] += is_help
                            # for cede tracking
                            if not attacker in self.cede_task.valor_delta:
                                self.cede_task.valor_delta[attacker] = 0
                            self.cede_task.valor_delta[attacker] += 1

                            ally_stats[attacker][3] += defender == terr_owner and terr_owner in allied_guilds and attacker in allied_guilds # ally-ally cede

                        acquired = terrs[ter]["acquired"]
                        acquired = datetime.datetime.strptime(acquired, "%Y-%m-%d %H:%M:%S")
                        
                        insert_exchanges.append(f"({int(acquired.timestamp())}, \"{defender}\", \"{attacker}\", \"{ter}\")")
                        queries.append(f"UPDATE territories SET guild=\"{attacker}\" WHERE name=\"{ter}\";")

                replace_ally_stats = [f"(\"{guild}\", {ally_stats[guild][0]}, {ally_stats[guild][1]}, {ally_stats[guild][2]}, {ally_stats[guild][3]}, {ally_stats[guild][4]})"
                    for guild in ally_stats]

                if len(queries):
                    Connection.exec_all(queries)
                    Connection.execute("INSERT INTO terr_exchange VALUES "+','.join(insert_exchanges))
                    Connection.execute("REPLACE INTO ally_stats VALUES "+','.join(replace_ally_stats))
                
                Connection.execute("INSERT INTO terr_count VALUES "+
                    ','.join(f"({int(time.time())}, \"{k}\", {guild_terr_cnt[k]})" for k in guild_terr_cnt))

                for ws in self.wsconns:
                    await ws.send('{"type":"terr","data":'+f"[{','.join(ws_payload)}]" + "}")

                end = time.time()
                print(datetime.datetime.now().ctime(), "TERRITORY TRACKER", end-start, "s")

                await asyncio.sleep(self.sleep)
        
            print(datetime.datetime.now().ctime(), "TerritoryTrackTask finished")

        self.continuous_task = asyncio.get_event_loop().create_task(self.continuously(terr_tracker_task))
        