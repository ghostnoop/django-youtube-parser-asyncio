import time

import requests

URL = "https://www.googleapis.com/youtube/v3/"


def check_speed_url(url: str):
    print(url)
    st = time.monotonic()
    resp = requests.get(url).json()
    print(time.monotonic() - st)


start = time.monotonic()
check_speed_url(
        f"{URL}playlistItems?playlistId=UUcGVrf54UcSyIFKlJic8T8A&part=snippet&maxResults=100&key=AIzaSyADhw8EuHcroH5AvYo0FRSeU1wWAwjQ9FE")

check_speed_url(f"{URL}commentThreads?part=snippet&videoId={'YEQ3T0s_utM'}&maxResults=100&order=relevance&key=AIzaSyDyIbkGEOqSv3QEfrooQoQcK488yLWDrj8")

check_speed_url(f"{URL}commentThreads?part=snippet&videoId={'YEQ3T0s_utM'}&maxResults=100&order=relevance&key=AIzaSyDyIbkGEOqSv3QEfrooQoQcK488yLWDrj8")
print("end", time.monotonic() - start)
