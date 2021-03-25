import asyncio

import asyncpg
import psycopg2
import requests
import os
import multiprocessing
import time

from parsing.models import ImageWithSubscriber


def get_token():
    url = f"https://api.selcdn.ru/auth/v1.0"

    header = {
        'X-Auth-User': '103784_Keri',
        'X-Auth-Key': 'A5pO-}h-m.',
    }

    payload = {}
    response = requests.request("GET", url, headers=header, data=payload)
    return response.headers['x-storage-token']


headers = {
    'X-Auth-Token': f'{get_token()}',
    'X-Delete-After': '9999999999999999999999999'
}


def update_status(item: ImageWithSubscriber):
    try:
        item.uploaded = True
        item.save()
    except Exception as e:
        print(e)


async def photo(data: ImageWithSubscriber):
    item = data
    request = requests.get(item.image_link)
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), f'{item.subscriber_id_id}.jpg')

    with open(path, 'wb') as file:
        file.write(request.content)
    print(item.subscriber_id_id)
    url = f"https://api.selcdn.ru/v1/SEL_103784/Фото Ютуб/{item.subscriber_id_id}.jpg"

    with open(path, 'rb') as f:
        content = f.read()

    payload = {}
    files = [
        (f'{item.subscriber_id_id}.jpg', (f'{item.subscriber_id_id}.jpg', content))
    ]

    response = requests.request("PUT", url, headers=headers, data=payload, files=files)

    if response.status_code == 201:
        print("uploaded")
        os.remove(path)
        update_status(item)


async def upload_starter_async():
    while True:
        select_lists = ImageWithSubscriber.objects.filter(uploaded=False)[:500]
        if len(select_lists) == 0:
            print("len",0)
            await asyncio.sleep(60 * 5)
            continue

        start_time = time.monotonic()
        tasks = []
        for item in select_lists:

            tasks.append(photo(item))

            if len(tasks) == 5:
                await asyncio.gather(*tasks)
                tasks.clear()
        if len(tasks) > 0:
            await asyncio.gather(*tasks)
            tasks.clear()

        print(f"{time.monotonic() - start_time} time")


def upload_starter():
    loop = asyncio.new_event_loop()
    loop.create_task(upload_starter_async())
    loop.run_forever()
