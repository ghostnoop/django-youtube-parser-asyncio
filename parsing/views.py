import asyncio
import threading
import time
from datetime import datetime, timedelta

import asyncpg
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

# Create your views here.
from django.utils.safestring import SafeString
from django.views import View

from parsing.models import *


class RouteStatisticPerHour(View):
    def get(self, request, hour):
        st = time.monotonic()
        channels = Channel.objects.all()
        answers = asyncio.run(parallerizm_hour(channels, hour))
        thead = answers[0]
        answers.append(get_sums(answers))
        print("finish", time.monotonic() - st)
        return render(request, 'index.html', {'thead': thead, 'results': answers})


def get_sums(answers):
    result = {
        "final": "Итого",
        "count": 0,
        "comments": 0,
        "subscribers": 0,
        "videos": 0,
    }
    t = 0
    for a in answers:
        result['comments'] += try_except(a['comments'])
        result['subscribers'] += try_except(a['subscribers'])
        result['videos'] += try_except(a['videos'])
        t += 1
    result['count'] = t
    return result


async def parallerizm_hour(channels, hour):
    start_time = time.monotonic()
    answers = []
    tasks = []
    loop = asyncio.get_event_loop()
    for channel in channels:
        print(channel.channel_id)
        try:
            task = loop.create_task(stats_per_hours(channel, hour))
            tasks.append(task)
        except Exception as e:
            print(e)
            continue
    g = 0
    for task in tasks:
        t = await task
        g += 1
        print(g)

        answers.append(t)
    return answers


async def stats_per_hours(channel, hour):
    st = time.monotonic()
    end = str(datetime.now())
    start = str(datetime.now() - timedelta(hours=hour))

    comments = 0
    subscribers = 0
    videos = 0

    preloadeds = PreLoadedHourStatistic.objects.filter(channel_id_id=channel.id, created__range=(start, end))
    for pre in preloadeds:
        pre: PreLoadedHourStatistic
        comments += pre.comments
        subscribers += pre.subscribers
        videos += pre.videos

    print("done", channel.id)
    return {
        "name": channel.username,
        "pk": channel.channel_id,
        "comments": comments,
        "subscribers": subscribers,
        "videos": videos,
    }


class RouteStatisticAsync(View):
    def get(self, request):
        channels = Channel.objects.all()
        answers = []
        for channel in channels:
            t = statisticer_v2(channel)
            if t is not None:
                answers.append(t)
        print('d')
        thead = answers[0]
        answers.append(sum_columns(answers))

        return render(request, 'index.html', {'thead': thead, 'results': answers})


async def parallerizm(channels):
    start_time = time.monotonic()
    answers = []
    loop = asyncio.get_event_loop()
    for channel in channels:
        print(channel.channel_id)
        try:
            t = await loop.create_task(statisticer_v2(channel))
            print('t good')
        except Exception as e:
            print(e)
            print(e)
            continue

        answers.append(t)

    print(time.monotonic() - start_time)

    return answers


async def get_percent(a, b):
    try:
        percent = float(a) / float(b)
        return f"{round(percent * 100, 1)}%"
    except:
        return "-------"


class KeysView(View):
    def get(self, request, hours):
        end = str(datetime.now())
        start = str(datetime.now() - timedelta(hours=hours))
        keys_banned = HistoryBannedKeys.objects.filter(created__range=(start, end)) \
            .annotate(hour=TruncHour('created')).values('hour').annotate(Count('id'))
        if keys_banned.count() == 0:
            return HttpResponse("<h1>Пока история пуста</h1>")
        # UserCommentsVideo.objects.all().annotate(hour=TruncHour('parsed_date')).values('hour').annotate(Count('id'))
        return render(request, 'index.html', {'thead': keys_banned[0], 'results': keys_banned})


async def statisticer(channel):
    subscribers = channel.subscriber_set.count()
    videos = VideoDone.objects.filter(channel_id=channel)
    videos_count = videos.count()

    COMMENTS = PreloadedStatistic.objects.filter(channel_id=channel)[0]
    comments_all = COMMENTS.comments_all_count
    comments_count = COMMENTS.comments_count
    commenters = COMMENTS.commenters_count

    sub_percent = await get_percent(subscribers, channel.subscriber_count)

    video_percent = await get_percent(videos_count, channel.video_count)

    comments_percent = await get_percent(comments_count, comments_all)

    return {
        "name": channel.username,
        "pk": channel.channel_id,
        "viewCount": channel.view_count,
        "subscriberCount": channel.subscriber_count,
        "subscribers": subscribers,
        "videos all": channel.video_count,
        "videos done": videos_count,
        "comments all": comments_all,
        "comments": comments_count,
        "commenters": commenters,
        "subs%": sub_percent,
        "videos%": video_percent,
        "comments%": comments_percent
    }


def statisticer_v2(channel):
    try:
        stat = FinishedStatistic.objects.get(channel_id=channel)
        print('good')
        return {
            "name": channel.username,
            "pk": channel.channel_id,
            "viewCount": channel.view_count,
            "subscriberCount": channel.subscriber_count,
            "subscribers": stat.subscribers,
            "videos all": channel.video_count,
            "videos done": stat.videos_done,
            "comments all": stat.comments_all,
            "comments": stat.comments,
            "commenters": stat.commenters,
            "subs%": f'{stat.sub_percent}%',
            "videos%": f'{stat.video_percent}%',
            "comments%": f'{stat.comment_percent}%'
        }
    except Exception as e:
        print(e)
        return None


def try_except(value):
    try:
        return int(value)
    except:
        return 0


def del_percent(value: str):
    try:
        return float(value.replace("%", ""))
    except:
        return 0


def sum_columns(answers):
    result = {
        "result": "Итого",
        "channels": 0,
        "viewCount": 0,
        "subscriberCount": 0,
        "subscribers": 0,
        "videos all": 0,
        "videos done": 0,
        "comments all": 0,
        "comments": 0,
        "commenters": 0,
        "subs%": 0,
        "videos%": 0,
        "comments%": 0,
    }
    t = 0
    subs = 0
    videos = 0
    comments = 0
    for i in answers:
        t += 1
        result["viewCount"] += try_except(i["viewCount"])
        result["subscriberCount"] += try_except(i["subscriberCount"])
        result["subscribers"] += try_except(i["subscribers"])
        result["videos all"] += try_except(i["videos all"])
        result["videos done"] += try_except(i["videos done"])
        result["comments all"] += try_except(i["comments all"])
        result["comments"] += try_except(i["comments"])
        result["commenters"] += try_except(i["commenters"])

        subs += del_percent(i['subs%'])
        videos += del_percent(i['videos%'])
        comments += del_percent(i['comments%'])

    result["channels"] = t
    result['subs%'] = f"{round(subs / t, 1)}%"
    result['videos%'] = f"{round(videos / t, 1)}%"
    result['comments%'] = f"{round(comments / t, 1)}%"
    return result


class HistoryView(View):
    def get(self, request):
        channels = Channel.objects.all()
        return render(request, 'list.html', {'channels': channels})


class DetailView(View):
    def get(self, request, pk):
        channel = Channel.objects.get(pk=pk)

        comments = 0
        subscribers = 0
        videos = 0

        preloads = PreLoadedHourStatistic.objects.filter(channel_id_id=channel.id)
        return render(request, 'detail.html', {'preloads': preloads})
