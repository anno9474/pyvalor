import asyncio
from log import logger

import grpc
from rpc import player_stats_update_pb2
from rpc import player_stats_update_pb2_grpc
from heartbeat.player_stats import PlayerStatsTask

class PlayerStatsUpdater(player_stats_update_pb2_grpc.PlayerStatsUpdater):
    async def UpdatePlayerStats(
        self,
        request: player_stats_update_pb2.Request,
        context: grpc.aio.ServicerContext,
    ) -> player_stats_update_pb2.Response:
        search_players, old_membership, prev_warcounts = await PlayerStatsTask.get_stats_track_references(needs_player_list=False)
        inserts_war_update, inserts_war_deltas, inserts_guild_log, inserts, uuid_name = PlayerStatsTask.get_empty_stats_track_buffers()
        failures = []
        for player_uuid in request.player_uuid:
            res = await PlayerStatsTask.track_player(player_uuid, old_membership, prev_warcounts, 
                                                    inserts_war_update, inserts_war_deltas, inserts_guild_log, inserts, uuid_name)
            if not res:
                failures.append(player_uuid)

        PlayerStatsTask.write_results_to_db(inserts_war_update, inserts_war_deltas, inserts_guild_log, inserts, uuid_name)
        return player_stats_update_pb2.Response(failures=failures)
    

async def serve() -> None:
    server = grpc.aio.server()
    player_stats_update_pb2_grpc.add_PlayerStatsUpdaterServicer_to_server(PlayerStatsUpdater(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logger.info("Player stats updater Starting gRPC server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()