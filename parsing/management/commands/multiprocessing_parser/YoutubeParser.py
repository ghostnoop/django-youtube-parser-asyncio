import asyncio
from typing import List

from django.db.models import QuerySet

from parsing.management.commands.multiprocessing_parser import services
from parsing.management.commands.multiprocessing_parser.extra import URL
from parsing.management.commands.multiprocessing_parser.services import filter_videos
from parsing.models import Channel, YoutubeKey, CommentPerVideo, VideoDone, UserCommentsVideo, SubscriberWithoutChannel


class YoutubeParser:
    channel: Channel
    keys: List[YoutubeKey]

    def __init__(self, channel, LIST):
        self.channel = channel
        self.keys = LIST

    async def start(self):
        # await self.get_new_keys(None)
        await self.get_info_about_channel()

    async def get_new_keys(self, key_token):
        self.keys = await services.get_new_keys_and_ban_current(key_token)

    async def request_yo_youtube(self, url) -> dict:
        return await self.get_response_from_youtube(url)

    async def get_response_from_youtube(self, url) -> dict:
        keys = self.keys
        while True:
            if keys is None:
                keys = await services.get_new_keys_and_ban_current(None)
            response, key = await services.request_worker(keys, url)
            if 'error' in response and 'quota' in response['error']['message']:
                keys = await services.get_new_keys_and_ban_current(key)
                continue
            else:
                self.keys = keys
                return response

    async def get_info_about_channel(self):
        try:
            if self.channel.channel_id == "":
                url = f"{URL}channels?part=contentDetails&part=statistics&part=snippet&forUsername={self.channel.username}"
            else:
                url = f"{URL}channels?part=contentDetails&part=statistics&part=snippet&id={self.channel.channel_id}"

            response = await self.request_yo_youtube(url)
            self.channel = services.update_channel(channel=self.channel, response=response)
            self.channel.save()

            upload_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            await self.get_videos_from_channel(upload_id)
        except Exception as e:
            print('info about channel', e)

    async def get_videos_from_channel(self, upload_id):
        next_page = ""
        while True:
            url = "{}playlistItems?playlistId={}&part=snippet&maxResults=50{}"
            response = await self.request_yo_youtube(url.format(URL, upload_id, next_page))

            comments_per_video = []
            videos_id = []
            count_of_videos = 0
            for item in response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                video_url = f"{URL}videos?id={video_id}&part=statistics"
                video_response = await self.request_yo_youtube(video_url)
                videos_id.append(video_id)
                comments_per_video.append(services.get_info_about_video(video_response, video_id, self.channel))
                count_of_videos += 1

                if count_of_videos > 10:
                    count_of_videos = 0
                    await self.task_manager(videos_id[:], comments_per_video[:])
                    videos_id.clear()
                    comments_per_video.clear()

            if count_of_videos > 0:
                await self.task_manager(videos_id[:], comments_per_video[:])
                print("done task manager")
                videos_id.clear()
                comments_per_video.clear()

            if 'nextPageToken' in response:
                next_page = "&pageToken=" + response['nextPageToken']
            else:
                print("finish video full")
                self.channel.parsed = True
                self.channel.save()
                print('channel done', self.channel.username)
                return
                # break

    async def task_manager(self, videos_id, comments_per_video):
        CommentPerVideo.objects.bulk_create(comments_per_video, ignore_conflicts=True)
        final_videos_id = filter_videos(videos_id)

        queue = asyncio.Queue()
        for final_video_id in final_videos_id:
            asyncio.create_task(self.get_comments_from_video(final_video_id, queue))

        max_length = len(final_videos_id)
        count = 0
        while max_length - 1 > count:
            data = await queue.get()
            comments = data['comments']
            video_id = data['video_id']
            if comments is None:
                queue.task_done()
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
                    print('save comments count:', len(comments))
                    UserCommentsVideo.objects.bulk_create(comments, ignore_conflicts=True)
                    SubscriberWithoutChannel.objects.bulk_create(whs, ignore_conflicts=True)
                except Exception as e:
                    print("user comments error")

    async def get_comments_from_video(self, video_id, queue):
        # print('in comments')
        try:
            next_page = ""
            while True:
                url = "{}commentThreads?part=snippet&videoId={}&maxResults=100{}"
                response = await self.request_yo_youtube(url.format(URL, video_id, next_page))

                if "error" in response:
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
                    comments.append(services.get_comment_data(item, video_id, self.channel))
                    reply_count = item['snippet']['totalReplyCount']
                    if reply_count > 0:
                        reply_ids.append(item['id'])

                await queue.put(
                    dict(comments=comments, subs=subs, video_id=video_id, whs=without, reply_count=reply_ids))

                if 'nextPageToken' in response:
                    next_page = "&pageToken=" + response['nextPageToken']
                else:
                    break

        except Exception as e:
            print("error parse comments", e)
        try:
            VideoDone.objects.get_or_create(video_id=video_id, channel_id=self.channel, comments_parsed=True)
        except Exception as e:
            print("save video")
        await queue.put(dict(comments=None, video_id=video_id, subs=None))

    async def get_reply_comment(self, comment_id, queue, video_id):
        # print("in reply")
        try:
            next_page = ""
            while True:
                url = "{}comments?part=snippet&maxResults=100&parentId={}{}"
                response = await self.request_yo_youtube(url.format(URL, comment_id, next_page))

                if response is None or "error" in response:
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
                    comments.append(services.get_reply_comment_data(item, video_id, self.channel))

                await queue.put(
                    dict(comments=comments, subs=subs, video_id=video_id, whs=without))

                if 'nextPageToken' in response:
                    next_page = "&pageToken=" + response['nextPageToken']
                else:
                    break

        except Exception as e:
            print("get reply", e)
        await queue.put(dict(comments=None, video_id=video_id, subs=None))
