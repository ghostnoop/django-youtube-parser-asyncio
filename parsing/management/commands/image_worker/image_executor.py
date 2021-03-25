import requests

from parsing.management.commands.image_worker.services import get_response
from parsing.models import *

URL = "https://www.googleapis.com/youtube/v3/channels?part=snippet"


def executor():
    while True:
        subscribers = Subscriber.objects.filter(image_executed=False)[:50000]
        print("start")
        count = 0
        list_of_ids = ''
        list_to_update = []
        for subscriber in subscribers:

            list_of_ids += f'&id={subscriber.subscriber_id}'

            subscriber.image_executed = True
            list_to_update.append(subscriber)

            if count == 40:
                print("count",count)
                final_url = URL + list_of_ids
                resp = get_response(final_url)


                imagers = []
                i = 0
                for item in resp['items']:
                    data = item['snippet']['thumbnails']
                    data: dict
                    thumb = list(data.keys())[-1]
                    image = data[thumb]['url']
                    imagers.append(ImageWithSubscriber(subscriber_id=list_to_update[i], image_link=image,uploaded=False))
                    i += 1
                print("save")
                try:
                    ImageWithSubscriber.objects.bulk_create(imagers)
                except Exception as e:
                    print(e)
                try:
                    Subscriber.objects.bulk_update(list_to_update, ['image_executed'])
                except Exception as e:
                    print("e",e)
                list_of_ids = ''
                list_to_update.clear()
                imagers.clear()
                count = 0
                pass

            count += 1
