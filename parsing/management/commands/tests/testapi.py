import requests

URL = "https://www.googleapis.com/youtube/v3/"
key = "AIzaSyCvue1ZT5v4xKdOMK404uq5ZZWUbMcvOis"
# https://www.googleapis.com/youtube/v3/comments?key=AIzaSyCvue1ZT5v4xKdOMK404uq5ZZWUbMcvOis&part=snippet&id=UgwJ1SYYkjg44Qb3c-F4AaABAg

next_page = ""
count = 0
s = ""
kkkk=set()
while True:
    url = "{}commentThreads?part=snippet&videoId=E56Egr4fQBY&maxResults=100&key={}{}" \
          "".format(URL, key, next_page)

    data = requests.get(url).json()
    for i in data['items']:
        kkkk.add(i['id'])

    print('nextPageToken' in data)
    if 'nextPageToken' in data:
        s = data['nextPageToken']
        next_page = f"&pageToken={data['nextPageToken']}"
    else:
        print(s)
        break

    # print(len(data['items']))
    count = len(kkkk)
    print(count)
# &part=replies
next_page = ""
while True:
    url = "{}commentThreads?part=snippet&videoId=E56Egr4fQBY&maxResults=100&key={}{}&part=replies" \
          "".format(URL, key, next_page)

    data = requests.get(url).json()
    for i in data['items']:
        kkkk.add(i['id'])

    print('nextPageToken' in data)
    if 'nextPageToken' in data:
        s = data['nextPageToken']
        next_page = f"&pageToken={data['nextPageToken']}"
    else:
        print(s)
        break

    # print(len(data['items']))
    count = len(kkkk)
    print(count)
