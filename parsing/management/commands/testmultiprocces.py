import multiprocessing
import sys
import time

import requests
from django.core.management import BaseCommand
from django.db import transaction

# from parsing.models import YoutubeKey
import django

django.setup()
from parsing.models import YoutubeKey, TestClasser

COUNT = 1000

qwerty = [0 for i in range(20)]


# @transaction.non_atomic_requests
def mult_testt(q, i):
    a: YoutubeKey = YoutubeKey.objects.first()
    TestClasser.objects.create(text=str(i))
    resp = requests.get(
        'https://www.googleapis.com/youtube/v3/channels?part=statistics&maxResults=50&id=UCzUNay3Y_VPo02yfI-PHCoQ&id=UC7J5G3Dzh-HSbOC84seUpLA&key=AIzaSyCgOm6wUjUt_7vfM5Glf2VIGQj7PL_LL-E')
    # print(a.token)
    print(i, resp.status_code)
    while True:
        # qwerty[i] = 1
        time.sleep(5)

        # print('alive',i)
    # if resp.status_code != 200:
    #     print(resp.json())
    #     sys.exit(1)
    # q.put(i)


# testmultiprocces
class Command(BaseCommand):
    help = 'Imports list of relations to the system'

    def handle(self, *args, file=None, **options):

        queue = multiprocessing.Queue()
        st = time.monotonic()
        for i in range(COUNT):
            process1 = multiprocessing.Process(
                target=mult_testt,
                args=(queue, i)
            )
            process1.start()
        print('------------------------', time.monotonic() - st, '------------------------')

        while True:
            print(sum(qwerty))
        # process1.join()

        # while not queue.empty():
        # #     print(queue.get())
        # while not queue.empty():
        #     # print(queue.get())
        #     pass
