import random
import time
from time import timezone

from django.db import models


# Create your models here.
class Channel(models.Model):
    username = models.CharField(max_length=200, default="", blank=True)
    channel_id = models.CharField(max_length=200, default="", blank=True, unique=True)
    parsed = models.BooleanField(default=False)
    view_count = models.CharField(max_length=200, default="--", blank=True, null=True)
    subscriber_count = models.CharField(max_length=200, default="--", blank=True, null=True)
    video_count = models.CharField(max_length=200, default="--", blank=True, null=True)

    class Meta:
        unique_together = (("username", "channel_id"),)


def get_count():
    return int(round(time.time() * 1000)) * 100 + random.randint(0, 100)


class Subscriber(models.Model):
    # class Meta:
    #     unique_together = (("subscriber_id", "channel_pk"),)

    custom_id = models.CharField(default="_", max_length=200)
    subscriber_id = models.CharField(max_length=200, primary_key=True)
    fullname = models.CharField(max_length=300)
    description = models.TextField()
    keywords = models.TextField()
    country = models.CharField(max_length=300)
    view_count = models.CharField(max_length=300)
    subscriber_count = models.CharField(max_length=300)
    video_count = models.CharField(max_length=300)
    custom_url = models.CharField(max_length=300)
    published_at = models.CharField(max_length=300)
    channel_pk = models.ForeignKey(Channel, on_delete=models.SET(0), null=True)
    vk = models.CharField(max_length=300, default="")
    instagram = models.CharField(max_length=300, default="")
    telegram = models.CharField(max_length=300, default="")
    facebook = models.CharField(max_length=300, default="")
    twitter = models.CharField(max_length=300, default="")
    others_links = models.TextField(default="")
    parsed_date = models.DateTimeField(auto_now_add=True)


class JobTasker(models.Model):
    name = models.CharField(max_length=200)
    started = models.DateTimeField(auto_now_add=True)


class UserCommentsVideo(models.Model):
    comment_id = models.CharField(max_length=200, unique=True, default="")
    user_id = models.CharField(max_length=200, default="")
    name = models.CharField(max_length=200, default="")
    comment = models.TextField(default="", )
    comment_original = models.TextField(default="")
    video_id = models.CharField(max_length=255, default="")
    like_count = models.IntegerField(default=0)
    published = models.CharField(max_length=200, default="")
    channel_id = models.ForeignKey(Channel, on_delete=models.SET(0), default=1)
    parsed_date = models.DateTimeField(auto_now_add=True)


class YoutubeKey(models.Model):
    token = models.CharField(max_length=255, unique=True)
    alive = models.BooleanField(default=True)
    banned = models.CharField(max_length=100, default="", blank=True)


class CommentPerVideo(models.Model):
    comment_count = models.CharField(max_length=255)
    like_count = models.CharField(max_length=200)
    dislike_count = models.CharField(max_length=200)
    view_count = models.CharField(max_length=200)
    video_id = models.CharField(max_length=200,unique=True)
    channel_id = models.ForeignKey(Channel, on_delete=models.SET(0))
    parsed_date = models.DateTimeField(auto_now_add=True)


class PreloadedStatistic(models.Model):
    channel_id = models.ForeignKey(Channel, on_delete=models.CASCADE, unique=True)
    comments_count = models.BigIntegerField(default=0)
    comments_all_count = models.BigIntegerField(default=0)
    commenters_count = models.BigIntegerField(default=0)


class PreLoadedHourStatistic(models.Model):
    channel_id = models.ForeignKey(Channel, on_delete=models.CASCADE)
    comments = models.BigIntegerField(default=0)
    subscribers = models.BigIntegerField(default=0)
    videos = models.BigIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)


class SubscriberWithoutChannel(models.Model):
    subscriber_id = models.CharField(max_length=200, unique=True)
    from_channel_id = models.ForeignKey(Channel, on_delete=models.SET(0))
    processed = models.BooleanField(default=False)


class HistoryBannedKeys(models.Model):
    key = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)


class VideoDone(models.Model):
    video_id = models.CharField(max_length=255, unique=True, primary_key=True)
    channel_id = models.ForeignKey(Channel, on_delete=models.CASCADE)
    comments_parsed = models.BooleanField(default=True)
    parsed_date = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def is_exist(video_id, channel_id):
        video = VideoDone.objects.filter(video_id=video_id, channel_id=channel_id)
        if video.exists():
            return True
        else:
            # VideoDone.objects.create(video_id=video_id, channel_id=channel_id)
            return False


class TestClasser(models.Model):
    text = models.CharField(max_length=200)
