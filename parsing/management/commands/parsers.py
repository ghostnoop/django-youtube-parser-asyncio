from parsing.management.commands.keys import keys
from parsing.management.commands.youtube_parsing import *


def start_parsing(channel, lock):
    try:
        Youtube(channel=channel, lock=lock)
    except Exception as e:
        print(e)


def func(x, lock):
    lock.acquire()
    a = x()
    lock.release()
    return a


def get_path():
    print(os.getcwd())


def key_load():
    key_per = keys()
    for i in key_per:
        try:
            YoutubeKey.objects.create(token=i, alive=True, banned="")
            print("added")
        except Exception as e:
            print(e)
            print("error")


LINKS = ['vk', 'instagram', 'tg', 'facebook', 'twitter']


def create_path_and_folder(image):
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


def download_image(image: str, user_id):
    img = requests.get(image, allow_redirects=True)
    path = create_path_and_folder(img)
    try:
        with open(os.path.join(path, str(user_id) + ".png"), "wb") as f:
            f.write(img.content)
    except:
        pass


def get_info_scrapy(subscriber_id, sub):
    resp = ""
    try:
        r = requests.get(f"https://www.youtube.com/channel/{subscriber_id}/about")
        resp = f"{r.status_code},   {r.text}"
        r = r.text
        start = r',"selected":true,'
        end = r',"statsLabel"'
        text = "{" + r.split(start)[1].split(end)[0].replace(" ", "") + "}}]}}]}}}"

        data = json.loads(text)
        data = data['content']['sectionListRenderer']['contents'][0]
        data = data['itemSectionRenderer']['contents'][0]['channelAboutFullMetadataRenderer']

        description = data['description']['simpleText'] if 'description' in data else ""

        links = data['primaryLinks'] if 'primaryLinks' in data else ""

        def subs_count(text: str):
            if text.find('"subscriberCountText":{"simpleText":"') >= 0:
                return text.split('"subscriberCountText":{"simpleText":"')[1].split('подписч')[0]
            else:
                return ""

        def clear_url(url: str):
            if url.find("q=") >= 0:
                return url.split("q=")[1].replace("%2F", "/").replace("%3A", ":")
            else:
                return url.replace("%2F", "/").replace("%3A", ":")

        def get_custom_url(url: str):
            if url.find("user") >= 0:
                return url.split("user/")[1]
            else:
                return ""

        vk = ""
        instagram = ""
        telegram = ""
        facebook = ""
        twitter = ""
        other_links = ""

        if links != "":
            for link in links:
                url = clear_url(link['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url'])
                bl = False
                for l in LINKS:
                    if url.__contains__(l):
                        bl = True
                        break
                if bl:
                    if url.find("vk") >= 0:
                        vk = url
                    elif url.find("instagram") >= 0:
                        instagram = url
                    elif url.find("telegram") >= 0:
                        telegram = url
                    elif url.find("twitter") >= 0:
                        twitter = url
                else:
                    other_links += f"{url}\n"
        # try:
        #     image = data['avatar']['thumbnails'][-1]['url']
        #     download_image(image, subscriber_id)
        # except Exception as e:
        #     print("img", e)

        view_count = data['viewCountText']['simpleText'].split(" ")[0] if 'viewCountText' in data else ""
        published_at = data['joinedDateText']['runs'][1]['text'] if 'joinedDateText' in data else ""
        fullname = data['title']['simpleText'] if 'title' in data else ""
        country = data['country']['simpleText'] if 'country' in data else ""
        custom_url = get_custom_url(data['canonicalChannelUrl']) if 'canonicalChannelUrl' in data else ""
        subscriber_count = subs_count(r)

        try:
            sub: Subscriber
            sub.fullname = fullname
            sub.description = description
            sub.country = country
            sub.view_count = view_count
            sub.subscriber_count = subscriber_count
            sub.custom_url = custom_url
            sub.published_at = published_at
            sub.vk = vk
            sub.instagram = instagram
            sub.telegram = telegram
            sub.facebook = facebook
            sub.twitter = twitter
            sub.others_links = other_links
            sub.save()

            return True

        except Exception as e:
            print("db", e)
        time.sleep(10)
    except Exception as e:
        if resp.find('automatically detects requests') >= 0:
            time.sleep(60 * 60 * 5)
        print("scrapy\n", resp, e)
        pass


def internal_def_v1(channels):
    print("get")
    st = time.monotonic()
    comments_all = UserCommentsVideo.objects.all()
    print("donee")

    try:
        print(comments_all.count())
    except Exception as e:
        print(e)
    print(time.monotonic() - st)
    print("done get")
    data_preload = {}
    data_comments = {}
    data_commenters = {}
    for channel in channels:
        try:
            PreloadedStatistic.objects.create(channel_id=channel)
        except Exception as e:
            pass
        preload = PreloadedStatistic.objects.get(channel_id=channel)
        data_preload[channel.id] = preload
        data_comments[channel.id] = 0
        data_commenters[channel.id] = set()

    st = time.monotonic()
    for cc in comments_all:
        data_comments[cc.channel_id_id] += 1
        data_commenters[cc.channel_id_id].add(cc.user_id)
    print(time.monotonic() - st, "done all comments")

    for channel in channels:
        st = time.monotonic()
        d = data_preload[channel.id]
        per_video = list(CommentPerVideo.objects.filter(channel_id=channel).values_list('comment_count', flat=True))
        count_per_video_comments = 0
        for per in per_video:
            try:
                count_per_video_comments += per if per != '' else 0
            except:
                pass

        d.comments_all_count = count_per_video_comments
        d.comments_count = data_comments[channel.id]
        d.commenters_count = data_commenters[channel.id]
        d.save()
        print(d.comments_all_count, d.comments_count, d.commenters_count, channel.id)
        print(time.monotonic() - st)


def internal_def(channels):
    global_count=0
    for channel in channels:
        print("get")
        comments_all = list(
            UserCommentsVideo.objects.filter(channel_id_id=channel.id).values_list('user_id', flat=True))

        print("done")
        try:
            PreloadedStatistic.objects.create(channel_id=channel)
        except Exception as e:
            pass
        preload = PreloadedStatistic.objects.get(channel_id=channel)
        per_video = list(CommentPerVideo.objects.filter(channel_id=channel).values_list('comment_count', flat=True))
        count_per_video_comments = 0
        print("per video")
        for per in per_video:
            try:
                if per != "":
                    count_per_video_comments += int(per)
            except:
                pass
        counter = len(comments_all)
        commenters = len(set(comments_all))
        print("all done go to save",counter,count_per_video_comments,commenters,channel.id)
        preload.comments_all_count = count_per_video_comments
        preload.commenters_count=commenters
        preload.comments_count=counter
        preload.save()
        print("done save")
        global_count+=counter
        print(global_count,"preeee")
    print(global_count,"finished")
    print("done all")
