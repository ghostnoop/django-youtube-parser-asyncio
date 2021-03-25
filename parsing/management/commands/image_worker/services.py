import time
from datetime import datetime

import requests
from django.db.models import Q

from parsing.models import  YoutubeKey



def get_response(url: str):
    while True:
        keys = YoutubeKey.objects.filter(alive=True)[:1]
        if keys.exists():
            key = keys[0]
            ff_url=url + f"&key={key.token}"
            response = requests.get(ff_url).json()
            if 'error' in response:
                print("error",response)
                key.banned = datetime.strftime(datetime.today(), '%d.%m.%Y')
                key.save()
                continue
            else:
                return response

            pass
        else:
            keys = YoutubeKey.objects.filter(~Q(banned__contains=datetime.strftime(datetime.today(), '%d.%m.%Y')))
            print("need key")
            time.sleep(100)

            for key in keys:
                key: YoutubeKey
                key.alive = True
                key.save()
            continue
