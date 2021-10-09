import asyncio

class Task:
    def __init__(self, sleep):
        self.finished = True
        self.aTask = None
        self.sleep = sleep
        
    def run(self):
        pass

    def stop(self):
        pass
