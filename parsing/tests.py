# import asyncio
# import threading
#
#
# class NoLike:
#     def __init__(self, qq):
#         self.qq = qq
#
#     def __str__(self):
#         return f"hello {self.qq}"
#
#
# async def async_generator(name, queue, index):
#     for i in range(3):
#         await asyncio.sleep(1)
#         # queue.put_nowait(NoLike(name))
#         # yield i + 23
#         queue.put_nowait(dict(data=None, index=index))
#         return
#
# async def mainq():
#     queue = asyncio.Queue()
#
#     gg = [
#         async_generator("a", queue, 1),
#         async_generator("b", queue, 2),
#         async_generator("c", queue, 3)
#     ]
#     await asyncio.gather(*gg)
#     count = 0
#
#     while count < len(gg):
#         dictionary = await queue.get()
#         data = dictionary['data']
#         index = dictionary['index']
#         # print(mess)
#
#         # print(mess.__str__())
#         if data is None:
#             print(index, "done")
#             # print("end 1")
#             count += 1
#     print("finish", count)
#
#
# asyncio.run(mainq())
from ratelimit import RateLimitException


def log(*msg):
    print()


log(1)

import ratelimit
from backoff import on_exception, expo

class RateLimitCustom(Exception):
    def __init__(self, message, period_remaining):
        pass

@ratelimit.limits(calls=1, period=60)
def test(name):
    print(name)


for i in range(5):
    try:
        test(f"{i}{i}{i}")
    except:
        pass
