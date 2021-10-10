import asyncio
import traceback

class Task:
    def __init__(self, sleep):
        self.finished = True
        self.continuous_task = None
        self.sleep = sleep
        
    def run(self):
        pass

    def stop(self):
        pass

    def done_callback(self, msg):
        exc = msg.exception()
        if exc:
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        print(self, "exited without callback?")

    async def continuously(self, coro):
        while not self.finished:
            task = asyncio.get_event_loop().create_task(coro)
            task.add_done_callback(self.done_callback)
            await asyncio.wait([self.aTask])
            await asyncio.sleep(5)
