import asyncio
import threading
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore

# runapscheduler
from myyoutube import settings
from parsing.management.commands.async_parsing.async_parsing import AsyncYoutube
from parsing.management.commands.async_v2.starter import starter
from parsing.management.commands.parsers import start_parsing, get_info_scrapy, internal_def
from parsing.management.commands.parsing_subs.get_subs import api_getter_starter
from parsing.models import *


def my_job():
    JobTasker.objects.create(name="my_job")
    lock = threading.Lock()
    channels = Channel.objects.filter(parsed=False)
    for channel in channels:
        channel: Channel
        print(channel.pk)
        # channel.parsed = True
        # channel.save()

        thread1 = threading.Thread(
            target=start_parsing,
            args=(channel, lock)
        )
        thread1.start()


def my_tob():
    JobTasker.objects.create(name="my_tob")
    subs = Subscriber.objects.filter(vk="", instagram="", telegram="", facebook="", twitter="", others_links="")
    for sub in subs:
        # print(sub.subscriber_id)
        get_info_scrapy(sub.subscriber_id, sub)


def interval_job():
    JobTasker.objects.create(name="interval_job")
    channels = Channel.objects.all()
    internal_def(channels)


def per_hour_statistic():
    JobTasker.objects.create(name="per hour")

    try:
        PreLoadedHourStatistic.objects.filter(created__lte=str(datetime.now() - timedelta(days=5))).delete()
    except Exception as e:
        print("peload", e)
        pass

    channels = Channel.objects.all()
    end = str(datetime.now())
    start = str(datetime.now() - timedelta(hours=1))
    for channel in channels:
        comments = UserCommentsVideo.objects.filter(channel_id_id=channel.id, parsed_date__range=(start, end)).count()
        subscribers = Subscriber.objects.filter(channel_pk_id=channel.id, parsed_date__range=(start, end)).count()
        videos = VideoDone.objects.filter(channel_id_id=channel.id, parsed_date__range=(start, end)).count()
        try:
            PreLoadedHourStatistic.objects.create(channel_id=channel, comments=comments,
                                                  subscribers=subscribers, videos=videos)
            print("done", channel.channel_id)
        except Exception as e:
            print("preload", e)





class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        print("started")

        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")
        from django.utils import timezone
        now = timezone.now()
        print(now)
        date = datetime.now() + timedelta(seconds=5)

        # starter()
        scheduler.add_job(
            starter,
            trigger=CronTrigger(hour=date.hour, minute=date.minute, second=date.second, day_of_week=date.weekday()),
            id="my_job",
            max_instances=1,
            replace_existing=True,
        )
        #
        scheduler.add_job(
            api_getter_starter,
            trigger=CronTrigger(hour=date.hour, minute=date.minute, second=date.second, day_of_week=date.weekday()),
            id="subs_job",
            max_instances=1,
            replace_existing=True,
        )
        # api_getter_starter()

        #
        # scheduler.add_job(
        #     my_tob,
        #     trigger=CronTrigger(hour=date.hour, minute=date.minute, second=date.second),  # Every 10 seconds
        #     id="my_tob",  # The `id` assigned to each job MUST be unique
        #     max_instances=1,
        #     replace_existing=True,
        # )
        # interval_job()

        scheduler.add_job(
            interval_job,
            trigger=CronTrigger(hour="*/1"),  # Every 10 seconds
            id="interval_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        scheduler.add_job(
            per_hour_statistic,
            trigger=CronTrigger(hour='*/1'),  # Every 10 seconds
            id="interval_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        # interval_job()


        #
        #
        #
        # starter()

        try:
            scheduler.start()
        except KeyboardInterrupt as e:
            print(e)
            scheduler.shutdown()
