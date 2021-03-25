import asyncio

from parsing.management.commands.parsing_subs.check_subscribers import get_subs_info
from parsing.models import Channel, SubscriberWithoutChannel, Subscriber


def api_getter_starter_v2():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

async def main():
    channels = Channel.objects.all()
    for channel in channels:
        final_list = get_subs(channel)
        if len(final_list) > 0:
            asyncio.create_task(api_getter_v2(final_list, channel))

def get_subs(channel):
    subs_suspense = set(list(
        SubscriberWithoutChannel.objects.filter(from_channel_id_id=channel.id, processed=False)
            .values_list('subscriber_id', flat=True)))

    subs = set(list(Subscriber.objects.all()
                    .values_list('subscriber_id', flat=True)))

    final_list = list(subs_suspense - subs)
    print("return")
    return final_list

async def api_getter_v2(final_list, channel):
    max_ = 25
    count = 0
    tasks = []
    for sub in final_list:
        tasks.append(api_getter_v2_util(sub, channel))
        count += 1
        if count > max_:
            print("tasks")
            await asyncio.gather(*tasks)
            count = 0
            tasks.clear()
    if len(tasks)>0:
        await asyncio.gather(*tasks)
        count = 0
        tasks.clear()


async def api_getter_v2_util(sub, channel):
    print("in task")
    is_subs = await get_subs_info(sub, channel)
    print("sub", is_subs)
    if is_subs:
        print("saved")
        await save_subscribers(sub, channel)
        print("done")
    try:
        save_subq = SubscriberWithoutChannel.objects.get(subscriber_id=sub)
        save_subq.processed = True
        save_subq.save()
    except Exception as e:
        print(e)
        pass

async def save_subscribers(sub_id, channel):
    try:
        Subscriber.objects.create(subscriber_id=sub_id, fullname="", description="",
                                  keywords="", country="", view_count="",
                                  subscriber_count="", video_count="", custom_url="",
                                  published_at="", channel_pk=channel, vk="",
                                  instagram="", telegram="", facebook="", twitter="",
                                  others_links="")
    except Exception as e:
        print(e)
        pass
