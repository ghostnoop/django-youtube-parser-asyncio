import asyncio
import hashlib
import os
from datetime import datetime

import requests

from parsing.models import *
import random

URL = "https://www.googleapis.com/youtube/v3/"
LINKS = ['vk', 'instagram', 'telegram', 'facebook', 'twitter']


class CONFIG:
    download_need = True


class Worker:
    def __init__(self, channel):
        self.channel = channel

    async def async_init(self):
        self.key = await self.waiting_key()
        await self.get_channel()

    async def get_key(self):
        keys = YoutubeKey.objects.filter(alive=True)

        if keys.exists():
            rdn = random.randint(0, len(keys) - 1)
            return keys[rdn]
        else:
            return None

    async def waiting_key(self):
        key = await self.get_key()
        if key is None:
            while True:
                print("need key")
                await asyncio.sleep(30)
                key = await self.get_key()
                if key is not None:
                    return key
        else:
            return key

    async def get_response(self, url: str):
        while True:
            await asyncio.sleep(0.05)
            response = requests.get(url + f"&key={self.key.token}")
            if response.status_code == 403:
                if "quota" in str(response.json()['error']['message']):
                    print("quota")
                    await self.ban_key()
                    await self.update_key()

                    continue
                if "the requested subscriptions" in str(response.json()['error']['message']):
                    # print("request not allow")
                    # print(url)
                    pass
            return response.json()

    async def ban_key(self):
        try:
            self.key.alive = False
            self.key.banned = datetime.strftime(datetime.today(), '%d.%m.%Y')
            self.key.save()
            return True
        except:
            return False

    async def update_key(self):
        self.key = await self.waiting_key()

    async def get_channel(self):
        if self.channel.channel_id == "":
            url = f"{URL}channels?part=contentDetails&part=statistics&part=snippet&forUsername={self.channel.username}"
        else:
            url = f"{URL}channels?part=contentDetails&part=statistics&part=snippet&id={self.channel.channel_id}"
        response = await self.get_response(url)
        self.upload_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        try:
            custom = response['items'][0]['snippet']
            if 'title' in custom:
                self.channel.username = custom['title']

            temp = response['items'][0]['statistics']
            if 'viewCount' in temp:
                self.channel.view_count = temp['viewCount']
            if 'subscriberCount' in temp:
                self.channel.subscriber_count = temp['subscriberCount']
            if 'videoCount' in temp:
                self.channel.video_count = temp['videoCount']
            self.channel.save()
        except Exception as e:
            print("a", e)
            print(response)

        if self.channel.channel_id == "":
            try:
                self.channel.channel_id = response['items'][0]['id']
                self.channel.save()
                return True
            except:
                return False

        await self.get_videos_v2()

    async def get_stat_from_video(self, st, video_id):
        viewCount = ""
        if 'viewCount' in st:
            viewCount = st['viewCount']
        likeCount = ""
        if 'likeCount' in st:
            likeCount = st['likeCount']
        dislikeCount = ""
        if 'dislikeCount' in st:
            dislikeCount = st['dislikeCount']
        commentCount = ""
        if 'commentCount' in st:
            commentCount = st['commentCount']

        try:
            return CommentPerVideo(video_id=video_id, like_count=likeCount, dislike_count=dislikeCount,
                                   view_count=viewCount, comment_count=commentCount, channel_id=self.channel)

        except Exception as e:
            if "exist" not in str(e):
                print("db", e)
            return None

    async def get_videos(self, next_page=""):
        print("worker", self.channel.channel_id, "video")
        if next_page != "":
            next_page = "&pageToken=" + next_page

        url = f"{URL}playlistItems?playlistId={self.upload_id}&part=snippet&maxResults=100{next_page}"
        response = await self.get_response(url)
        for item in response['items']:
            video = item['snippet']['resourceId']['videoId']
            video_url = f"{URL}videos?id={video}&part=statistics"

            resp = await self.get_response(video_url)
            st = resp['items'][0]['statistics']
            await self.get_stat_from_video(st, video)

            try:
                boolean = VideoDone.is_exist(video_id=video, channel_id=self.channel)
            except:
                boolean = True

            if boolean:
                continue
            else:
                # print("get comments", self.channel.channel_id)
                task = asyncio.create_task(self.get_comments_by_video_v2(video))

                await asyncio.sleep(0.20)

        try:
            if 'nextPageToken' in response and response['nextPageToken'] is not None:
                await self.get_videos(next_page=response['nextPageToken'])
        except Exception as e:
            print(e)

    async def get_videos_v2(self):
        url = "{}playlistItems?playlistId={}&part=snippet&maxResults=100{}"
        next_page = ""
        response = await self.get_response(url.format(URL, self.upload_id, next_page))
        while 'nextPageToken' in response:
            print("page", self.channel.channel_id)
            stats = []
            tasks = []
            for item in response['items']:
                video = item['snippet']['resourceId']['videoId']
                video_url = f"{URL}videos?id={video}&part=statistics"

                resp = await self.get_response(video_url)
                try:
                    st = resp['items'][0]['statistics']
                except Exception as e:
                    print("items", e)
                    continue
                await self.get_stat_from_video(st, video)

                try:
                    boolean = VideoDone.objects.get(video_id=video, channel_id=self.channel)
                except:
                    boolean = False

                if boolean:
                    continue
                else:
                    print("not exist")
                    task = asyncio.create_task(self.get_comments_by_video_v2(video))
                    tasks.append(task)

                if len(tasks) > 20:
                    print("in tasks")
                    for task in tasks:
                        await task
                    tasks.clear()

            if len(tasks) > 0:
                for task in tasks:
                    await task
                tasks.clear()

            try:
                CommentPerVideo.objects.bulk_create(stats, ignore_conflicts=True)
            except Exception as e:
                print("commentPerVideo", e)

    async def get_comments_by_video_v2(self, video_id):
        print("get comments")
        next_page = ""
        url = "{}commentThreads?part=snippet&videoId={}&maxResults=100{}&order=relevance"
        response = await self.get_response(url.format(URL, video_id, next_page))
        if "error" in response:
            print("error response",video_id,response)
            return

        subs_new = set()
        while 'nextPageToken' in response:
            print("hello")
            comments = []
            for item in response['items']:
                try:
                    subscriber_id = item['snippet']['topLevelComment']['snippet']['authorChannelId']['value']
                    subs_new.add(subscriber_id)
                except:
                    continue
                c = self.get_comment(item, video_id)
                if c is not None:
                    comments.append(c)
            a=UserCommentsVideo.objects.bulk_create(comments, ignore_conflicts=False)
            print("tut",a)
            comments.clear()

            next_page = response['nextPageToken']
            url = "{}commentThreads?part=snippet&videoId={}&maxResults=100{}&order=relevance"
            response = await self.get_response(url.format(URL, video_id, next_page))
        subs_new = list(subs_new)
        subs_to_add = []
        while subs_new:
            try:
                sub_new = subs_new.pop()
                try:
                    Subscriber.objects.get(subscriber_id=sub_new)
                except Subscriber.DoesNotExist:
                    check_sub = await self.check_subscribing(subscriber_id=sub_new)
                    if check_sub:
                        t = Subscriber(subscriber_id=sub_new, fullname="", description="",
                                       keywords="", country="", view_count="",
                                       subscriber_count="", video_count="", custom_url="",
                                       published_at="", channel_pk=self.channel, vk="",
                                       instagram="", telegram="", facebook="", twitter="",
                                       others_links="")
                        subs_to_add.append(t)

            except Exception as e:
                print("error")
        try:
            Subscriber.objects.bulk_create(subs_to_add, ignore_conflicts=True)
        except Exception as e:
            print("add", e)
        print("video done", self.channel.channel_id)

        VideoDone.objects.create(video_id=video_id, channel_id=self.channel, comments_parsed=True)

    async def get_comments_by_video(self, video_id, next_page="", count=0):
        if next_page != "":
            next_page = "&pageToken=" + next_page
        url = f"{URL}commentThreads?part=snippet&videoId={video_id}&maxResults=100{next_page}&order=relevance"
        response = await self.get_response(url)
        if "error" in response:
            # print("disabled comments", video_id, response['error'])
            pass
        else:
            for item in response['items']:
                try:
                    subscriber_id = item['snippet']['topLevelComment']['snippet']['authorChannelId']['value']
                except:
                    continue
                await self.save_comment(item, video_id)

                try:
                    boolean = Subscriber.objects.get(subscriber_id=subscriber_id)
                    return True
                except:
                    boolean = True

                if boolean:
                    continue
                try:
                    check_sub = await self.check_subscribing(subscriber_id=subscriber_id)
                    # print(check_sub, self.channel.channel_id)
                    if check_sub:
                        print("add", subscriber_id)
                        await self.set_sub(sub_id=subscriber_id)

                except Exception as e:
                    print("err", e)

        try:
            if 'nextPageToken' in response and response['nextPageToken'] is not None and count < 1000000:
                await self.get_comments_by_video(video_id, next_page=response['nextPageToken'], count=count + 1)
            else:
                print("videodone")
                try:
                    VideoDone.objects.create(video_id=video_id, channel_id=self.channel)
                except Exception as e:
                    if "exist" not in str(e):
                        print("video", e)

                return True
        except:
            print("videodone expect")
            try:
                VideoDone.objects.create(video_id=video_id, channel_id=self.channel)
            except Exception as e:
                if "exist" not in str(e):
                    print("video", e)
                pass

    def get_comment(self, item, video_id):
        comment_id = item['id']
        item = item['snippet']['topLevelComment']['snippet']
        user_id = item['authorChannelId']['value']
        user_name = item['authorDisplayName']
        comment = item['textDisplay']
        comment_original = item['textOriginal']
        like_count = item['likeCount']
        published = item['publishedAt']

        try:
            return UserCommentsVideo(comment_id=comment_id, user_id=user_id, name=user_name,
                                     comment=comment,
                                     comment_original=comment_original, like_count=like_count,
                                     published=published, video_id=video_id, channel_id=self.channel)

        except Exception as e:
            if "exist" not in str(e):
                print("db", e)
            return None

    async def set_sub(self, sub_id):
        print("sub create", self.channel.channel_id)
        try:
            Subscriber.objects.create(subscriber_id=sub_id, fullname="", description="",
                                      keywords="", country="", view_count="",
                                      subscriber_count="", video_count="", custom_url="",
                                      published_at="", channel_pk=self.channel, vk="",
                                      instagram="", telegram="", facebook="", twitter="",
                                      others_links="")
            return True

        except Exception as e:
            if "exist" not in str(e):
                print("db", e)
            return False

    async def check_subscribing(self, subscriber_id):
        try:
            url = f"{URL}subscriptions?part=snippet&channelId={subscriber_id}&forChannelId={self.channel.channel_id}"
            response = await self.get_response(url)
            return len(response['items']) >= 0
        except Exception as e:
            return False

    async def get_full_info(self, subscriber_id):
        url = f"{URL}channels?&part=statistics&part=brandingSettings&part=snippet&id={subscriber_id}"
        user_data = await self.get_response(url)

        user_data = user_data['items'][0]
        full_name = user_data['snippet']['title']
        # image = self.get_image(user_data['snippet']['thumbnails'])

        snippet = user_data['snippet']
        description = snippet['description'] if 'description' in snippet else ""
        custom_url = snippet['customUrl'] if 'customUrl' in snippet else ""
        published_at = snippet['publishedAt'] if 'publishedAt' in snippet else ""

        brandingSettings = user_data['brandingSettings']['channel']
        keywords = brandingSettings['keywords'] if 'keywords' in brandingSettings else ""
        country = brandingSettings['country'] if 'country' in brandingSettings else ""

        statistics = user_data['statistics']
        view_count = statistics['viewCount'] if 'viewCount' in statistics else ""
        subscriber_count = statistics['subscriberCount'] if 'subscriberCount' in statistics else ""
        video_count = statistics['videoCount'] if 'videoCount' in statistics else ""

        try:
            Subscriber.objects.create(subscriber_id=subscriber_id, fullname=full_name, description=description,
                                      custom_url=custom_url,
                                      published_at=published_at, keywords=keywords, country=country,
                                      view_count=view_count, subscriber_count=subscriber_count,
                                      video_count=video_count, channel_pk=self.channel)
            return True
        except:
            return False

        # if CONFIG.download_need:
        #     self.download_image(image, subscriber_id)
