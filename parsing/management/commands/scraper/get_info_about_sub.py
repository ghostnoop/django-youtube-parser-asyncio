import asyncio
import json

import aiohttp

from parsing.models import Subscriber

proxies = [
    "http://6lbUAx:ODVBNzAbQV@188.130.219.53:5500",
    "http://6lbUAx:ODVBNzAbQV@45.145.119.192:5500",
    "http://6lbUAx:ODVBNzAbQV@45.151.145.105:5500",
    "http://6lbUAx:ODVBNzAbQV@45.134.253.194:5500"
]
LINKS = ['vk', 'instagram', 'tg', 'facebook', 'twitter']

cc = [0]


async def worker():
    main_list = list(Subscriber.objects.filter(published_at="")[:])
    size = len(main_list) // 4
    a = main_list[:size]
    b = (main_list[size:size * 2])
    c = (main_list[size * 2:size * 3])
    d = (main_list[size * 3:])
    tasks = [parser_from_youtube(a, proxies[0]),
             parser_from_youtube(b, proxies[1]),
             parser_from_youtube(c, proxies[2]),
             parser_from_youtube(d, proxies[3])]

    await asyncio.gather(*tasks)


def starter_getter_info():
    loop = asyncio.new_event_loop()
    loop.create_task(worker())
    loop.run_forever()


# todo with queue where queue put in requests, queue get in scraper

async def parser_from_youtube(subs, proxy):
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    loop.create_task(producer(queue, len(subs)))

    async with aiohttp.ClientSession() as session:
        for sub in subs:
            sub: Subscriber
            async with session.get(f"https://www.youtube.com/channel/{sub.subscriber_id}/about", proxy=proxy) as resp:
                text = await resp.text()
                if text.find('automatically detects requests') >= 0:
                    print("detect bot")
                    await asyncio.sleep(60 * 60)
                else:
                    print("suda")
                    await queue.put(dict(response=text, sub=sub))


async def producer(queue, length):
    count = 0
    print("producer")
    while count < length - 1:
        data = await queue.get()
        count += 1
        await get_info_scrapy(data['response'], data['sub'])


async def get_info_scrapy(response, sub):
    try:
        r = response
        start = r',"selected":true,'
        end = r',"statsLabel"'
        text = "{" + r.split(start)[1].split(end)[0].replace(" ", "") + "}}]}}]}}}"

        data = json.loads(text)
        data = data['content']['sectionListRenderer']['contents'][0]
        data = data['itemSectionRenderer']['contents'][0]['channelAboutFullMetadataRenderer']

        description = data['description']['simpleText'] if 'description' in data else ""

        links = data['primaryLinks'] if 'primaryLinks' in data else ""

        def subs_count(text: str):
            if text.find('"subscriberCountText":{"simpleText":"') >= 0:
                return text.split('"subscriberCountText":{"simpleText":"')[1].split('подписч')[0]
            else:
                return ""

        def clear_url(url: str):
            if url.find("q=") >= 0:
                return url.split("q=")[1].replace("%2F", "/").replace("%3A", ":")
            else:
                return url.replace("%2F", "/").replace("%3A", ":")

        def get_custom_url(url: str):
            if url.find("user") >= 0:
                return url.split("user/")[1]
            else:
                return ""

        vk = ""
        instagram = ""
        telegram = ""
        facebook = ""
        twitter = ""
        other_links = ""

        if links != "":
            for link in links:
                url = clear_url(link['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url'])
                bl = False
                for l in LINKS:
                    if url.__contains__(l):
                        bl = True
                        break
                if bl:
                    if url.find("vk") >= 0:
                        vk = url
                    elif url.find("instagram") >= 0:
                        instagram = url
                    elif url.find("telegram") >= 0:
                        telegram = url
                    elif url.find("twitter") >= 0:
                        twitter = url
                else:
                    other_links += f"{url}\n"
        # try:
        #     image = data['avatar']['thumbnails'][-1]['url']
        #     download_image(image, subscriber_id)
        # except Exception as e:
        #     print("img", e)

        view_count = data['viewCountText']['simpleText'].split(" ")[0] if 'viewCountText' in data else ""
        published_at = data['joinedDateText']['runs'][1]['text'] if 'joinedDateText' in data else ""
        fullname = data['title']['simpleText'] if 'title' in data else ""
        country = data['country']['simpleText'] if 'country' in data else ""
        custom_url = get_custom_url(data['canonicalChannelUrl']) if 'canonicalChannelUrl' in data else ""
        subscriber_count = subs_count(r)

        try:
            sub: Subscriber
            sub.fullname = fullname
            sub.description = description
            sub.country = country
            sub.view_count = view_count
            sub.subscriber_count = subscriber_count
            sub.custom_url = custom_url
            sub.published_at = published_at
            sub.vk = vk
            sub.instagram = instagram
            sub.telegram = telegram
            sub.facebook = facebook
            sub.twitter = twitter
            sub.others_links = other_links
            sub.save()
            print("saved")
            cc[0] += 1
            print(cc[0])
            return True

        except Exception as e:
            print("db", e)
    except Exception as e:
        print(e)
        pass
