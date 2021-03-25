import asyncio

from aiohttp import ClientSession

from parsing.management.commands.async_v2.youtubescrapy import YoutubeScrapy
from parsing.models import Channel, YoutubeKey, JobTasker


def starter():
    JobTasker.objects.create(name="async parser")
    channels = Channel.objects.filter(parsed=False)
    keys = YoutubeKey.objects.filter(alive=True)[0:]
    loop = asyncio.new_event_loop()
    loop.create_task(start_parsing(channels, keys))
    loop.run_forever()
    # asyncio.run()

    pass


async def start_parsing(channels, keys):
    await asyncio.gather(*[
        YoutubeScrapy(channel, keys).get_channel_info() for channel in channels
    ])
