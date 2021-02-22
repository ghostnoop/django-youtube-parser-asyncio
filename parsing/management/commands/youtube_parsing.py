import hashlib
import json
import os
import random
import sys
import threading
import time
from datetime import datetime
import requests

from parsing.models import *

URL = "https://www.googleapis.com/youtube/v3/"
LINKS = ['vk', 'instagram', 'telegram', 'facebook', 'twitter']


class CONFIG:
    download_need = True


class Youtube:
    def __init__(self, channel, lock):
        print("init", channel.channel_id)
        self.lock = lock
        self.channel = channel
        self.key = self.waiting_key()
        self.pool = []
        # self.keys = list(self.get_keys())
        self.get_channel()

    def get_keys(self):
        return YoutubeKey.objects.filter(alive=True)[:50]

    def get_key(self):
        keys = YoutubeKey.objects.filter(alive=True)

        if keys.exists():
            rdn = random.randint(0, len(keys) - 1)
            return keys[rdn]
        else:
            return None

    def lock_for_db(self, x):
        try:
            self.lock.acquire()
            a = x()
            self.lock.release()
            return a
        except Exception as e:
            print("db error", e)
            return None

    def waiting_key(self):
        key = self.lock_for_db(self.get_key)
        if key is None:
            while True:
                print("need key")
                time.sleep(30)
                key = self.lock_for_db(self.get_key)
                if key is not None:
                    return key
        else:
            return key

    def get_response(self, url: str):
        while True:
            response = requests.get(url + f"&key={self.key.token}")
            if response.status_code == 403:
                if "quota" in str(response.json()['error']['message']):
                    print("quota")
                    self.ban_key()
                    self.update_key()

                    continue
                if "the requested subscriptions" in str(response.json()['error']['message']):
                    # print("request not allow")
                    # print(url)
                    pass
            return response.json()

    def get_response_v2(self, url: str):

        rdn = random.randint(0, len(self.keys) - 1)
        cur_key = self.keys[rdn]
        while True:
            if len(self.keys) > 10:
                response = requests.get(url + f"&key={cur_key.token}")
            else:
                response = requests.get(url + f"&key={self.key.token}")

            if response.status_code == 403:
                if "quota" in str(response.json()['error']['message']):
                    print("quota")
                    if len(self.keys) < 10:
                        self.ban_key()
                        self.update_key()
                    else:
                        self.keys: list
                        self.keys.remove(cur_key)

                    continue
                if "the requested subscriptions" in str(response.json()['error']['message']):
                    # print("request not allow")
                    # print(url)
                    pass
            return response.json()

    def ban_key(self):
        def x():
            try:
                self.key.alive = False
                self.key.banned = datetime.strftime(datetime.today(), '%d.%m.%Y')
                self.key.save()
                return True
            except:
                return False

        self.lock_for_db(x)

    def update_key(self):
        self.key = self.waiting_key()

    def get_image(self, json):
        if "maxres" in json:
            return json['maxres']['url']
        elif "standard" in json:
            return json["standard"]['url']
        elif "high" in json:
            return json["high"]['url']
        elif "medium" in json:
            return json["medium"]['url']
        elif "default" in json:
            return json["default"]['url']
        else:
            return ""

    def create_path_and_folder(self, image):
        try:
            md5 = hashlib.md5()
            md5.update(image.content)
            img = md5.hexdigest()
            path = os.path.join("images", img[0], img[1], img[2], img[3:])
            try:
                os.makedirs(path)
            except Exception as e:
                print(e)
                return os.path.join("images", "error")
            return path
        except Exception as e:
            print(e)
            return os.path.join("images", "error")

    def download_image(self, image: str, user_id):
        img = requests.get(image, allow_redirects=True)
        path = self.create_path_and_folder(img)
        try:
            with open(os.path.join(path, str(user_id) + ".png"), "wb") as f:
                f.write(img.content)
        except:
            pass

    def get_channel(self):
        if self.channel.channel_id == "":
            url = f"{URL}channels?part=contentDetails&part=statistics&part=snippet&forUsername={self.channel.username}"
        else:
            url = f"{URL}channels?part=contentDetails&part=statistics&part=snippet&id={self.channel.channel_id}"
        response = self.get_response(url)
        self.upload_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        def xx():
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

        self.lock_for_db(xx)

        if self.channel.channel_id == "":
            def x():
                try:
                    self.channel.channel_id = response['items'][0]['id']
                    self.channel.save()
                    return True
                except:
                    return False

            self.lock_for_db(x)

        self.get_videos_v2()

    def get_stat_from_video(self, st, video_id):
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

        def x():
            try:
                CommentPerVideo.objects.create(video_id=video_id, like_count=likeCount, dislike_count=dislikeCount,
                                               view_count=viewCount,
                                               comment_count=commentCount, channel_id=self.channel)
                video = VideoDone.objects.get(video_id=video_id)
                video.comments_parsed = True
                video.save()

            except Exception as e:
                print("e", e)

        self.lock_for_db(x)

    def get_videos_v2(self):
        start_time = time.monotonic()
        next_page = ""
        url = "{}playlistItems?playlistId={}&part=snippet&maxResults=100{}"
        response = self.get_response(url.format(URL, self.upload_id, next_page))

        while 'nextPageToken' in response:
            for item in response['items']:
                video = item['snippet']['resourceId']['videoId']
                video_url = f"{URL}videos?id={video}&part=statistics"
                resp = self.get_response(video_url)
                try:
                    st = resp['items'][0]['statistics']
                    self.get_stat_from_video(st, video)
                except Exception as e:
                    print("stats", e)

                def x():
                    try:
                        return VideoDone.is_exist(video_id=video, channel_id=self.channel)
                    except:
                        return True

                try:
                    boolean = self.lock_for_db(x)
                except:
                    boolean = True
                print("time before thread",time.monotonic()-start_time)

                if boolean:
                    continue
                else:
                    thread1 = threading.Thread(
                        target=self.get_comments_by_video_v2,
                        args=(video,)
                    )
                    self.pool.append(thread1)

                    if len(self.pool) >= 50:
                        for thread in self.pool:
                            print("thread started")
                            thread.start()
                            thread.join()
                            print("time after 1 thread", time.monotonic() - start_time)
                        self.pool.clear()

                print("end 1 for ", time.monotonic() - start_time)

            print("end 1 full cycle", time.monotonic() - start_time)
            if len(self.pool) > 0:
                for thread in self.pool:
                    print("thread started")
                    thread.start()
                    thread.join()
                self.pool.clear()

            print("video")
            next_page = "&pageToken=" + response['nextPageToken']
            response = self.get_response(url.format(URL, self.upload_id, next_page))

    def get_comment(self, item, video_id):
        comment_id = item['id']
        item = item['snippet']['topLevelComment']['snippet']
        user_id = item['authorChannelId']['value']
        user_name = item['authorDisplayName']
        comment = item['textDisplay']
        comment_original = item['textOriginal']
        like_count = item['likeCount']
        published = item['publishedAt']

        return UserCommentsVideo(comment_id=comment_id, user_id=user_id, name=user_name,
                                 comment=comment, comment_original=comment_original, like_count=like_count,
                                 published=published, video_id=video_id, channel_id=self.channel)

    def set_sub(self, sub_id):
        def x():
            try:
                Subscriber.objects.create(subscriber_id=sub_id, fullname="", description="",
                                          keywords="", country="", view_count="",
                                          subscriber_count="", video_count="", custom_url="",
                                          published_at="", channel_pk=self.channel, vk="",
                                          instagram="", telegram="", facebook="", twitter="",
                                          others_links="")
                return True

            except Exception as e:
                print("db", e)
                return False

        self.lock_for_db(x)

    def get_comments_by_video_v2(self, video_id):
        next_page = ""
        url = "{}commentThreads?part=snippet&videoId={}&maxResults=100{}&order=relevance"
        response = self.get_response(url.format(URL, video_id, next_page))

        if "error" in response:
            print("disabled comments")
            return

        while 'nextPageToken' in response:
            comments = []
            subs = set()
            for item in response['items']:
                try:
                    subscriber_id = item['snippet']['topLevelComment']['snippet']['authorChannelId']['value']
                except:
                    continue
                comments.append(
                    self.get_comment(item, video_id)
                )
                subs.add(subscriber_id)

            def x():
                try:
                    UserCommentsVideo.objects.bulk_create(comments, ignore_conflicts=True)
                except Exception as e:
                    print("bulc", e)

            self.lock_for_db(x)
            sub_2add = []
            for sub in subs:
                if not self.is_exist(sub) and self.check_subscribing(sub):
                    t = Subscriber(subscriber_id=sub, fullname="", description="",
                                   keywords="", country="", view_count="",
                                   subscriber_count="", video_count="", custom_url="",
                                   published_at="", channel_pk=self.channel, vk="",
                                   instagram="", telegram="", facebook="", twitter="",
                                   others_links="")
                    sub_2add.append(t)

            def xx():
                try:
                    Subscriber.objects.bulk_create(sub_2add, ignore_conflicts=True)
                except Exception as e:
                    print("bulc subs", e)

            self.lock_for_db(xx)

            next_page = "&pageToken=" + response['nextPageToken']
            response = self.get_response(url.format(URL, video_id, next_page))

        VideoDone.objects.create(video_id=video_id, channel_id=self.channel)

    def is_exist(self, sub_id):
        def x():
            try:
                Subscriber.objects.get(sub_id)
                return True
            except:
                return False

        return self.lock_for_db(x)

    def check_subscribing(self, subscriber_id):
        try:
            url = f"{URL}subscriptions?part=snippet&channelId={subscriber_id}&forChannelId={self.channel.channel_id}"
            response = self.get_response(url)
            return len(response['items']) >= 0
        except Exception as e:
            return False
