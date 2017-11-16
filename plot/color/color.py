import random


def get_color(n):
    if n < 0.01:
        return "rgb(0, 204, 0)"
    else:
        return "rgb(255, 0, 0)"


def convert_to_color(string):
    hash_ = str(hash(string))
    if len(hash_) >= 9:
        r, g, b = int(hash_[-9:-6]) % 255, int(hash_[-6:-3]) % 255, int(hash_[-3:]) % 255
        return "rgb({}, {}, {})".format(r, b, g)
    else:
        return "rgb({}, {}, {})".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

