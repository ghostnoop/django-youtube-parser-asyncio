import asyncio


async def long_time_runner(name,queue):
    i = 0
    while True:
        # print("while name")
        i += 1
        await queue.put(f"{i}, {name}")
        await asyncio.sleep(1)





async def main():
    queue = asyncio.Queue()
    names = [
        "q",
        "w",
        "e",
        "r",
        "t",
        "y",
        "u",
        "i",
        "o",
        "p",
        "[",
        "]",
        "k",
        "j",
        "h",
        "z",
        "b",
    ]
    for name in names:
        asyncio.create_task(long_time_runner(name,queue))

    # await asyncio.create_task(*[queue_returner(name, queue) for name in names])
    while True:
        data = await queue.get()
        print(data,"data")
        queue.task_done()
        print("done")

asyncio.run(main())
