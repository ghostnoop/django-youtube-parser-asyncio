import asyncio

import aiohttp
import ratelimit
from aiohttp import ClientSession

from . import services, parse_info
from .utils import URL
from parsing.models import *
import colorama
from colorama import Fore, Back, Style

colorama.init()


def log(*msg):
    print(Fore.RED + f"{msg}")


def logB(*msg):
    print(Fore.BLUE + f"{msg}")


class YoutubeScrapy:
    def __init__(self, channel, keys):
        self.keys: list = keys
        self.channel = channel

    async def wait_for_keys(self):
        while True:
            try:
                keys = services.get_new_keys()
                print(keys.count(), "keys")
                if keys.count() > 0:
                    self.keys = keys
                    break
                else:
                    print("need alive key")
                    await asyncio.sleep(60)
            except:
                print("exp")
                if self.keys.count() > 0:
                    return
                await asyncio.sleep(10)
                pass

    async def change_key(self, key):
        log("change key")
        await self.wait_for_keys()

    async def get_channel_info(self):

        log("get_channel_info")
        if self.channel.channel_id == "":
            url = f"{URL}channels?part=contentDetails&part=statistics&part=snippet&forUsername={self.channel.username}"
        else:
            url = f"{URL}channels?part=contentDetails&part=statistics&part=snippet&id={self.channel.channel_id}"

        response = await self.call_request(url)
        self.channel = parse_info.update_channel(channel=self.channel, response=response)
        self.channel.save()

        upload_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        await self.get_videos_from_channel(upload_id)

    async def get_videos_from_channel(self, upload_id):
        log("get_videos_from_channel")
        next_page = ""
        count = 0
        while True:
            url = "{}playlistItems?playlistId={}&part=snippet&maxResults=50{}"
            response = await self.call_request(url.format(URL, upload_id, next_page))

            comments_per_video = []
            videos_id = []
            count_of_videos = 0
            log("playlist items")
            for item in response['items']:
                count += 1
                video_id = item['snippet']['resourceId']['videoId']
                video_url = f"{URL}videos?id={video_id}&part=statistics"
                video_response = await self.call_request(video_url)
                videos_id.append(video_id)
                comments_per_video.append(parse_info.get_info_about_video(video_response, video_id, self.channel))
                count_of_videos += 1
                if count_of_videos > 10:
                    count_of_videos = 0
                    await self.task_manager(videos_id[:], comments_per_video[:])
                    print("done task manager")
                    videos_id.clear()
                    comments_per_video.clear()

            if count_of_videos > 0:
                await self.task_manager(videos_id[:], comments_per_video[:])
                print("done task manager")
                videos_id.clear()
                comments_per_video.clear()

            log("after all video in playlist", count, self.channel.channel_id)

            print("100 video done")
            if 'nextPageToken' in response:
                next_page = "&pageToken=" + response['nextPageToken']
            else:
                print("finish video full")
                break

            # response = await self.call_request(url.format(URL, upload_id, next_page))

    async def task_manager(self, videos_id, comments_per_video):
        CommentPerVideo.objects.bulk_create(comments_per_video, ignore_conflicts=True)
        final_videos_id = []
        for v_id in videos_id:
            try:
                VideoDone.objects.get(video_id=v_id)
                t = True
            except:
                t = False
                pass
            if not t:
                final_videos_id.append(v_id)
        print(len(final_videos_id))

        videos_id.clear()

        queue = asyncio.Queue()
        for final_video_id in final_videos_id:
            asyncio.create_task(self.get_comments_from_video(final_video_id, queue))

        max_length = len(final_videos_id)
        count = 0
        while max_length - 1 > count:
            data = await queue.get()
            print("get data", time.time())
            comments = data['comments']
            video_id = data['video_id']
            subs = data['subs']
            if comments is None:
                try:
                    print("save video")
                    VideoDone.objects.create(video_id=video_id, channel_id=self.channel, comments_parsed=True)
                except Exception as e:
                    print(e)
                queue.task_done()
                print("task done", count, "----", max_length)
                count += 1
            else:
                whs = data['whs']
                if 'reply_count' in data:
                    reply_ids = data['reply_count']
                    if len(reply_ids):
                        max_length += len(reply_ids)

                        for reply in reply_ids:
                            asyncio.create_task(self.get_reply_comment(reply, queue, video_id))

                try:
                    UserCommentsVideo.objects.bulk_create(comments, ignore_conflicts=True)
                    SubscriberWithoutChannel.objects.bulk_create(whs, ignore_conflicts=True)
                except Exception as e:
                    print("user comments")

    async def get_reply_comment(self, comment_id, queue, video_id):
        print("in reply")
        try:
            next_page = ""
            while True:
                url = "{}comments?part=snippet&maxResults=100&parentId={}{}"
                response = await self.call_request(url.format(URL, comment_id, next_page))

                if "error" in response:
                    log("disabled comments", video_id)
                    await queue.put(dict(comments=None, video_id=video_id, subs=None))
                    return
                comments = []
                subs = set()
                without = []
                for item in response['items']:
                    without.append(
                        SubscriberWithoutChannel(
                            subscriber_id=item['snippet']['authorChannelId']['value'],
                            from_channel_id=self.channel
                        )
                    )
                    comments.append(parse_info.get_reply_comment_data(item, video_id, self.channel))

                await queue.put(
                    dict(comments=comments, subs=subs, video_id=video_id, whs=without))

                if 'nextPageToken' in response:
                    next_page = "&pageToken=" + response['nextPageToken']
                else:
                    break
        except Exception as e:
            print("get reply", e)
        await queue.put(dict(comments=None, video_id=video_id, subs=None))

    async def get_comments_from_video(self, video_id, queue):
        try:
            next_page = ""
            while True:
                url = "{}commentThreads?part=snippet&videoId={}&maxResults=100{}"
                response = await self.call_request(url.format(URL, video_id, next_page))

                if "error" in response:
                    log("disabled comments", video_id)
                    await queue.put(dict(comments=None, video_id=video_id, subs=None))
                    return

                comments = []
                subs = set()
                without = []
                reply_ids = []
                for item in response['items']:
                    try:
                        item['snippet']['topLevelComment']['snippet']['authorChannelId']['value']
                    except:
                        continue
                    without.append(
                        SubscriberWithoutChannel(
                            subscriber_id=item['snippet']['topLevelComment']['snippet']['authorChannelId']['value'],
                            from_channel_id=self.channel
                        )
                    )
                    comments.append(parse_info.get_comment_data(item, video_id, self.channel))
                    reply_count = item['snippet']['totalReplyCount']
                    if reply_count > 0:
                        reply_ids.append(item['id'])

                await queue.put(
                    dict(comments=comments, subs=subs, video_id=video_id, whs=without, reply_count=reply_ids))

                if 'nextPageToken' in response:
                    next_page = "&pageToken=" + response['nextPageToken']
                else:
                    break

            print("done", video_id)
        except Exception as e:
            print("error parse comments", e)
        try:
            print("save video from func")
            VideoDone.objects.create(video_id=video_id, channel_id=self.channel, comments_parsed=True)
        except Exception as e:
            print("save video e", e)
        await queue.put(dict(comments=None, video_id=video_id, subs=None))

    async def call_request(self, url):
        if self.keys.count() == 0:
            self.keys = await self.wait_for_keys()
        while True:
            key = services.get_random_key(self.keys)
            code = await services.check_request(url, key)
            if code == 3:
                continue
            elif code == 0:
                key.alive = False
                try:
                    HistoryBannedKeys.objects.create(key=key.token)
                except:
                    pass
                key.save()
                await self.change_key(key)
            else:
                return code
