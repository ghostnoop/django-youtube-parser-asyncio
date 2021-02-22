import asyncio
import json
import random

import aiohttp
import ratelimit
from ratelimit import sleep_and_retry

from parsing.models import YoutubeKey


async def request_worker(url, key):
    try:
        url = f"{url}&key={key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                resp = await response.json()
            await session.close()
        return resp
    #             # response = await session.request(method='GET', url=url, timeout=5, allow_redirects=False)
    except Exception as e:
        print(e)
        await session.close()
        return None


def get_random_keys(keys: list, count):
    return random.choices(keys, count)


def get_random_key(keys) -> YoutubeKey:
    return random.choice(keys)


@ratelimit.limits(calls=1, period=60)
def get_new_keys():
    return YoutubeKey.objects.filter(alive=True)[0:]


async def check_request(url, key: YoutubeKey):
    response = await request_worker(url, key.token)
    if response is None:
        return 3

    elif 'error' in response:
        if 'quota' in response['error']['message']:
            return 0  # quota
        elif 'been used' in response['error']['message']:
            return 0  # project disabled
        else:
            return response
    else:
        return response


async def check_subscription(self, ids, URL, log):
    new_ids = []
    log("check subs", len(new_ids))
    for pk in ids:
        url = f"{URL}subscriptions?part=snippet&channelId={pk}&forChannelId={self.channel.channel_id}"
        response = "err"
        try:
            response = await self.call_request(url)
            if len(response['items']) >= 0:
                new_ids.append(pk)
        except Exception as e:
            # print("exceptions subs",response)
            pass
    log("done check subs")
    return new_ids
