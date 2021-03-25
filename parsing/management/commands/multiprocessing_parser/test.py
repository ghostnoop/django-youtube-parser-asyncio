a = "a{}"


def formater(url: str, *args):
    b = url.format(*args)
    print(b)

formater(a,1)
