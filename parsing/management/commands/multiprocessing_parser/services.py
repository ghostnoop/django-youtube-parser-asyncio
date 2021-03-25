import asyncio
import json
import random
from datetime import datetime

import aiohttp
import ratelimit
from django.db.models import Q

from parsing.models import YoutubeKey, Channel, CommentPerVideo, VideoDone, UserCommentsVideo


async def get_new_keys_and_ban_current(key_token):
    try:
        if key_token is not None:
            key_old = YoutubeKey.objects.get(token=key_token)
            key_old.alive = False
            key_old.banned = datetime.strftime(datetime.today(), '%d.%m.%Y')
            key_old.save()
    except:
        pass
    try:
        while True:
            keys = get_new_keys_per_period()
            if len(keys) == 0:
                return keys
            print('need keys')
            await asyncio.sleep(30)

    except Exception as e:
        await asyncio.sleep(10)
        return None


@ratelimit.limits(calls=1, period=60)
def get_new_keys_per_period():
    return list(YoutubeKey.objects.filter(
        ~Q(banned__contains=datetime.strftime(datetime.today(), '%d.%m.%Y'))).values_list('token', flat=True)
                )


def get_random_key(keys) -> str:
    return random.choice(keys)


async def request_worker(keys: list, url: str):
    key = get_random_key(keys)
    final_url = url + f'&key={key}'
    async with aiohttp.ClientSession() as session:
        async with session.get(final_url, timeout=5) as response:
            resp = await response.json()
            await session.close()
            return resp, key


def update_channel(channel: Channel, response):
    try:
        custom = response['items'][0]['snippet']
        if 'title' in custom:
            channel.username = custom['title']

        temp = response['items'][0]['statistics']
        if 'viewCount' in temp:
            channel.view_count = temp['viewCount']

        if 'subscriberCount' in temp:
            channel.subscriber_count = temp['subscriberCount']

        if 'videoCount' in temp:
            channel.video_count = temp['videoCount']

        if channel.channel_id == '':
            channel.channel_id = response['items'][0]['id']

    except Exception as e:
        print("update_channel", e)

    return channel


def get_info_about_video(response: json, video_id, channel):
    st = response['items'][0]['statistics']
    viewCount = ""
    if 'viewCount' in st:
        viewCount = st['viewCount']
    likeCount = ""
    if 'likeCount' in st:
        likeCount = st['likeCount']
    dislikeCount = ""
    if 'dislikeCount' in st:
        dislikeCount = st['dislikeCount']
    commentCount = ""
    if 'commentCount' in st:
        commentCount = st['commentCount']

    return CommentPerVideo(video_id=video_id, like_count=likeCount, dislike_count=dislikeCount,
                           view_count=viewCount, comment_count=commentCount, channel_id=channel)


def filter_videos(videos_id: list):
    final_videos_id = []
    for v_id in videos_id:
        try:
            VideoDone.objects.get(video_id=v_id)
            t = True
        except:
            t = False
            pass
        if not t:
            final_videos_id.append(v_id)

    videos_id.clear()
    return final_videos_id


def get_reply_comment_data(item, video_id, channel):
    comment_id = item['id']
    item = item['snippet']
    user_id = item['authorChannelId']['value']
    user_name = item['authorDisplayName']
    comment = item['textDisplay']
    comment_original = item['textOriginal']
    like_count = item['likeCount']
    published = item['publishedAt']

    return UserCommentsVideo(comment_id=comment_id, user_id=user_id, name=user_name,
                             comment=comment, comment_original=comment_original, like_count=like_count,
                             published=published, video_id=video_id, channel_id=channel)


def get_comment_data(item, video_id, channel):
    comment_id = item['id']
    item = item['snippet']['topLevelComment']['snippet']
    user_id = item['authorChannelId']['value']
    user_name = item['authorDisplayName']
    comment = item['textDisplay']
    comment_original = item['textOriginal']
    like_count = item['likeCount']
    published = item['publishedAt']

    return UserCommentsVideo(comment_id=comment_id, user_id=user_id, name=user_name,
                             comment=comment, comment_original=comment_original, like_count=like_count,
                             published=published, video_id=video_id, channel_id=channel)
