from datetime import datetime

import requests
from aiohttp import ClientSession

from parsing.models import *

URL = "https://www.googleapis.com/youtube/v3/"


def check_subscribers():
    channels = Channel.objects.all()

    for channel in channels:
        filter_subs(channel)


def check_subscribing(subscriber_id, channel):
    try:
        url = f"{URL}subscriptions?part=snippet&channelId={subscriber_id}&forChannelId={channel.channel_id}"
        response = get_response(url)
        return len(response['items']) >= 0
    except Exception as e:
        return False


async def get_subs_info(sub, channel, session):
    try:
        url = f"{URL}subscriptions?part=snippet&channelId={sub}&forChannelId={channel.channel_id}"
        response = await get_response_v2(url, session)
        return len(response['items']) >= 0
    except:
        return False


def save_sub(sub_id, channel):
    try:
        Subscriber.objects.create(subscriber_id=sub_id, fullname="", description="",
                                  keywords="", country="", view_count="",
                                  subscriber_count="", video_count="", custom_url="",
                                  published_at="", channel_pk=channel, vk="",
                                  instagram="", telegram="", facebook="", twitter="",
                                  others_links="")
    except Exception as e:
        pass


def pre_save_sub_check_sub_request(sub, channel):
    if check_subscribing(sub, channel):
        save_sub(sub, channel)


def get_response(url: str):
    key = get_key()
    while True:
        response = requests.get(url + f"&key={key.token}")
        if response.status_code == 403:
            if "quota" in str(response.json()['error']['message']):
                print("quota")
                ban_key(key)
                update_key()

                continue
            if "the requested subscriptions" in str(response.json()['error']['message']):
                pass
        return response.json()


async def get_response_v2(url: str, session):
    session: ClientSession
    key = get_key()
    while True:
        async with session.get(url) as resp:
            response = await resp.json()
            if response.status == 403:
                if "quota" in str(response['error']['message']):
                    print("quota")
                    ban_key(key)
                    update_key()
                    continue
                if "the requested subscriptions" in str(response.json()['error']['message']):
                    pass

        return response


def get_key():
    keys = YoutubeKey.objects.filter(alive=True)

    if keys.exists():
        rdn = random.randint(0, len(keys) - 1)
        return keys[rdn]
    else:
        return None


def waiting_key():
    key = get_key()
    if key is None:
        while True:
            print("need key")
            time.sleep(30)
            key = get_key()
            if key is not None:
                return key
    else:
        return key


def ban_key(key):
    try:
        key.alive = False
        key.banned = datetime.strftime(datetime.today(), '%d.%m.%Y')
        key.save()
        try:
            HistoryBannedKeys.objects.create(key=key.token)
        except:
            pass
        return True
    except:

        return False


def update_key():
    return waiting_key()


def x(st):
    print(time.monotonic() - st)


def filter_subs(channel):
    st = time.monotonic()
    user_comments = list(UserCommentsVideo.objects.filter(channel_id=channel).values_list('user_id', flat=True))
    x(st)
    print("after user comments")

    st = time.monotonic()
    user_without_sub = list(
        SubscriberWithoutChannel.objects.filter(from_channel_id=channel).values_list('subscriber_id', flat=True))
    x(st)
    print("after user_without_sub")

    st = time.monotonic()
    user_subs = list(Subscriber.objects.filter(channel_pk=channel).values_list('subscriber_id', flat=True))
    x(st)
    print("after user_subs")

    st = time.monotonic()
    users_to_check = set(user_comments) - set(user_without_sub)
    x(st)
    print("after users_to_check")

    st = time.monotonic()
    users_to_check = users_to_check - set(user_subs)
    print(len(users_to_check))
    for sub in users_to_check:
        pre_save_sub_check_sub_request(sub, channel)
    print("after")
    x(st)
    print("after users_to_check")
