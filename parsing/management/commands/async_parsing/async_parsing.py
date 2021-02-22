import asyncio

from parsing.management.commands.async_parsing.Worker import Worker
from parsing.models import *


class AsyncYoutube:
    def __init__(self, channels):
        self.semaphore = asyncio.Queue(maxsize=channels.count())
        self.channels = channels

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main_worker(loop))
        loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))

    async def main_worker(self, loop):
        for channel in self.channels:
            await self.semaphore.put(channel.id)
            loop.create_task(self.worker(channel))

    async def worker(self, channel):
        print("worker", channel.channel_id)
        worker = Worker(channel)
        await worker.async_init()
