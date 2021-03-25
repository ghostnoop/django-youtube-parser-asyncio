import os

from django.core.management.base import BaseCommand

from parsing.models import Channel

URL_FULL = 'http://youtube.com/channel/'
URL_YOUTUBE = 'http://youtube.com/'


def from_txt():
    print("started")
    print(os.path.abspath(os.curdir))
    with open('channels.txt', 'r', encoding='utf-8') as f:
        items = f.read().strip().split('\n')

        print(len(items))
        channels = []
        for item in items:
            if len(item) > 0:
                if URL_FULL in item:
                    channel = item.replace(URL_FULL, '')
                    channels.append(
                        Channel(channel_id=channel)
                    )
                else:
                    channel = item.replace(URL_YOUTUBE, '')
                    channels.append(
                        Channel(username=channel)
                    )

        Channel.objects.bulk_create(channels, ignore_conflicts=True)
        print('done', len(channels))


class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        with open('channels.txt', 'r', encoding='utf-8') as f:
            items = f.read().strip().split('\n')

            print(len(items))
            channels_nick = []
            channels_url = []
            for item in items:
                if len(item) > 0:
                    if URL_FULL in item:
                        channel = item.replace(URL_FULL, '')
                        channels_url.append(
                            channel
                        )
                    else:
                        channel = item.replace(URL_YOUTUBE, '')
                        channels_nick.append(
                            channel
                        )
        new_ch=[]
        for ch in channels_url:
            try:
                Channel.objects.get(channel_id=ch)
            except:
                print(ch)
                new_ch.append(ch)
        # for ch in channels_url:
        #     try:
        #         Channel.objects.create(channel_id=ch)
        #     except Exception as e:
        #         print(e)

        # a = Channel.objects.in_bulk(channels_nick, field_name='username')
        # print(a)
