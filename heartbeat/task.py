import asyncio
import traceback
import datetime
from log import logger

class Task:
    def __init__(self, sleep):
        self.finished = True
        self.continuous_task = None
        self.sleep = sleep
        
    def run(self):
        pass

    def stop(self):
        pass

    def done_callback(self, task: asyncio.Task):
        # retrieve exception
        exc = task.exception()
        if exc:
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        print(self, "exited without callback?")

    async def continuously(self, coro):
        try:
            while not self.finished:
                try:
                    await coro()
                except Exception as e:
                    traceback.print_exception(type(e), e, e.__traceback__)
                    logger.info("Restarting (Error Occured?)")
                await asyncio.sleep(10)
        except Exception as e:
            print(e)