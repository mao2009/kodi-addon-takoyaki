import os
import sys
from urllib.parse import urljoin, urlencode, parse_qs
from typing import List, Tuple, Dict, Set

import xbmc


class PresetMode(object):
        TOP_MENU = "top_menu"
        ENTRY = "entry"
        PLAY_LIST = "play_list"
        PLAY = "play"
        MEDIA_FILE = "media_file"
        LETTER = "letter"
        LETTER_ITME = "letter_item"
        SERIES = "series"
        EPISODE = "episode"
        TAG = "tag"
        TAG_LIST = "tag_list"
        GENRE = "genre"
        CATEGORY = "category"
        SEARCH = "search"

class LogLevel(object):
        DEBUG: int = xbmc.LOGDEBUG
        INFO: int = xbmc.LOGINFO
        WARNING: int = xbmc.LOGWARNING
        ERROR:int  = xbmc.LOGERROR
        FATAL:int = xbmc.LOGFATAL
        NONE:int  = xbmc.LOGNONE


def log(message: str, log_level: int):
    xbmc.log(message, log_level)


class ImageSet(object):
    ICON = "icon"
    THUMB = "thumb"
    FANART = "fanart"


def path_join(path: str, *paths: str) -> str:
    return os.path.join(path, *paths).replace('\\', '/')


def url_join(base: str, *urls: str) -> str:
    jointed_url = base
    for url in urls:
        jointed_url = urljoin(jointed_url,url)
    return jointed_url


def build_url(query: str) -> str:
    return sys.argv[0] + '?' + urlencode(query)


def parse_parameter() -> Dict[str, str]:
    params = parse_qs(sys.argv[2][1:])
    return {key: value[0] for key, value in params.items()}


def normalaze_query(query) -> str:
    return query.strip().replace(" ", "+")

def get_page_index():
    index = 1
    while True:
        yield index
        index += 1

generate_page_index = get_page_index()