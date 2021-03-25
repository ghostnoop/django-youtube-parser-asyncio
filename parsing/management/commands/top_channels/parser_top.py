import requests

STATIC_URL = "https://www.youtube.com/channel/{}"
KEY = "AIzaSyCIfbOs9VyodOp6Adu7TY2eqW_f9QOr2aA"
URL = "https://www.googleapis.com/youtube/v3/"

page_token = ""
count = 0
while count < 5000:
    URI = f'search?part=snippet&order=rating&regionCode=ru&channelType=any&relevanceLanguage=ru&type=channel&maxResults=50{page_token}'

    final_url = f'{URL}{URI}&key={KEY}'
    resp = requests.get(final_url).json()
    if 'error' in resp:
        print(resp)
        KEY = input("give key!!!!!")
        continue

    print(final_url)
    page_token = "&pageToken=" + resp['nextPageToken']
    s = ""
    # for item in resp['items']:
    #     channel_id = item['id']['channelId']
    #     s += STATIC_URL.format(channel_id) + "\n"

    # with open('youtube_top.csv', 'a', encoding='utf-8') as f:
    #     f.write(s)

    print(count)
    count += 50
