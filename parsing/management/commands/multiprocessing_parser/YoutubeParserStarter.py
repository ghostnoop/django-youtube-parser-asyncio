import asyncio
import multiprocessing
import time
from datetime import datetime

import django
from django.db.models import Q

django.setup()
from parsing.management.commands.multiprocessing_parser.YoutubeParser import YoutubeParser
from parsing.models import JobTasker, Channel, YoutubeKey


def starter_youtube_parse():
    channels = Channel.objects.filter(parsed=False)[:250]
    print(len(channels))
    time.sleep(5)

    st = time.monotonic()
    i = 0
    LIST = list(YoutubeKey.objects.filter(
        ~Q(banned__contains=datetime.strftime(datetime.today(), '%d.%m.%Y'))).values_list('token', flat=True)
                )
    for channel in channels:
        process1 = multiprocessing.Process(
            target=pre_starting,
            args=(channel, i, LIST)
        )
        process1.start()
        i += 1
    print('all started', time.monotonic() - st)

    while True:
        pass


def pre_starting(channel, i, LIST):
    loop = asyncio.new_event_loop()
    loop.create_task(start_parsing(channel, LIST))
    loop.run_forever()


async def start_parsing(channel, LIST):
    await YoutubeParser(channel, LIST).start()
