import json

from parsing.models import Channel, CommentPerVideo, UserCommentsVideo


def update_channel(channel: Channel, response):
    try:
        custom = response['items'][0]['snippet']
        if 'title' in custom:
            channel.username = custom['title']

        temp = response['items'][0]['statistics']
        if 'viewCount' in temp:
            channel.view_count = temp['viewCount']

        if 'subscriberCount' in temp:
            channel.subscriber_count = temp['subscriberCount']

        if 'videoCount' in temp:
            channel.video_count = temp['videoCount']

        if channel.channel_id == '':
            channel.channel_id = response['items'][0]['id']

    except Exception as e:
        print("update_channel", e)

    return channel


def get_info_about_video(response: json, video_id, channel):
    st = response['items'][0]['statistics']
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

    return CommentPerVideo(video_id=video_id, like_count=likeCount, dislike_count=dislikeCount,
                           view_count=viewCount, comment_count=commentCount, channel_id=channel)

def get_reply_comment_data(item,video_id,channel):
    comment_id = item['id']
    item=item['snippet']
    user_id = item['authorChannelId']['value']
    user_name = item['authorDisplayName']
    comment = item['textDisplay']
    comment_original = item['textOriginal']
    like_count = item['likeCount']
    published = item['publishedAt']
    if channel is None:
        print("\n\n\n\n\n\n\nALARM channel is None\n\n\n\n\\n\n")

    return UserCommentsVideo(comment_id=comment_id, user_id=user_id, name=user_name,
                             comment=comment, comment_original=comment_original, like_count=like_count,
                             published=published, video_id=video_id, channel_id=channel)



def get_comment_data(item, video_id, channel):
    comment_id = item['id']
    item = item['snippet']['topLevelComment']['snippet']
    user_id = item['authorChannelId']['value']
    user_name = item['authorDisplayName']
    comment = item['textDisplay']
    comment_original = item['textOriginal']
    like_count = item['likeCount']
    published = item['publishedAt']
    if channel is None:
        print("\n\n\n\n\n\n\nALARM channel is None\n\n\n\n\\n\n")

    return UserCommentsVideo(comment_id=comment_id, user_id=user_id, name=user_name,
                             comment=comment, comment_original=comment_original, like_count=like_count,
                             published=published, video_id=video_id, channel_id=channel)
