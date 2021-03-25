import asyncio

from parsing.management.commands.parsing_subs.check_subscribers import get_response_v2
from parsing.models import *

URL = "https://www.googleapis.com/youtube/v3/"


def api_getter_starter_v3():
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()


def get_subs(channel):
    subs_suspense = set(list(
        SubscriberWithoutChannel.objects.filter(from_channel_id_id=channel.id, processed=False)
            .values_list('subscriber_id', flat=True)))

    subs = set(list(Subscriber.objects.all()
                    .values_list('subscriber_id', flat=True)))

    final_list = list(subs_suspense - subs)
    print("leneee", len(final_list))
    return final_list


async def get_subs_info(sub, channel):
    try:
        url = f"{URL}subscriptions?part=snippet&channelId={sub}&forChannelId={channel.channel_id}"
        response = await get_response_v2(url)
        # print(len(response['items']))

        return len(response['items']) >= 0
    except Exception as e:
        # print("ex", e)
        return False


async def main():
    channels = Channel.objects.all()
    for channel in channels:
        final_list = get_subs(channel)
        asyncio.create_task(proccesser(final_list, channel))


async def get_info_about_sub(sub, channel, queue):
    t = await get_subs_info(sub, channel)
    await queue.put(dict(answer=t, sub=sub))


async def temp(final_list, channel, queue):
    for sub in final_list[:200]:
        asyncio.create_task(get_info_about_sub(sub, channel, queue))
    print("added\\\\\\\\\\\\")


async def proccesser(final_list, channel):
    while final_list:
        print("start round")
        queue = asyncio.Queue()
        l = len(final_list[:200]) - 1
        print("len")
        count = 0

        asyncio.create_task(temp(final_list, channel, queue))
        # for sub in final_list[:200]:
        #     await asyncio.create_task(get_info_about_sub(sub, channel, queue))
        subs_to_save = []
        withouts_to_save = []
        while count < l:
            # print(count, l)
            count += 1
            data = await queue.get()
            queue.task_done()
            if data['answer']:
                # print("save")
                try:
                    subs_to_save.append(

                        Subscriber(subscriber_id=data['sub'], fullname="", description="",
                                   keywords="", country="", view_count="",
                                   subscriber_count="", video_count="", custom_url="",
                                   published_at="", channel_pk=channel, vk="",
                                   instagram="", telegram="", facebook="", twitter="",
                                   others_links="")
                    )

                except Exception as e:
                    print(e)
                    pass


            else:
                # print("not in")
                pass

            withouts_to_save.append(data['sub'])
            # try:
            #     save_subq = SubscriberWithoutChannel.objects.get(subscriber_id=data['sub'])
            #     save_subq.processed = True
            #     save_subq.save()
            # except Exception as e:
            #     print(e)
            #     pass
        print("done, next round")
        Subscriber.objects.bulk_create(subs_to_save)
        array_of_washouts = list(SubscriberWithoutChannel.objects.in_bulk(withouts_to_save, field_name='subscriber_id').values())
        for d in array_of_washouts:
            d: SubscriberWithoutChannel
            d.processed = True
        SubscriberWithoutChannel.objects.bulk_update(array_of_washouts,['processed'])

        final_list = final_list[200:]
