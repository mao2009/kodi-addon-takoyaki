import os
import sys
import re
from urllib.parse import urljoin, urlencode, parse_qs, urlparse
from xml.dom.minidom import Element
import requests

from bs4 import BeautifulSoup

import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
import xbmcplugin

from enum import Enum


class Takoyaki(object):
    def __init__(self, name):
        self.SEARCH_URL = self.abs_url("?s={}")

    class ImageSet(Enum):
        ICON = "icon"
        THUMB = "thumb"
        FANART = "fanart"

    class LogLevel(Enum):
        DEBUG = xbmc.LOGDEBUG
        INFO = xbmc.LOGINFO
        # NOTICE = xbmc.LOGNOTICE
        WARNING = xbmc.LOGWARNING
        ERROR = xbmc.LOGERROR
        # SEVERE = xbmc.LOGSEVERE
        FATAL = xbmc.LOGFATAL
        NONE  = xbmc.LOGNONE     

    __base__url = sys.argv[0]
    __handle__ = int(sys.argv[1])
    __addon__ = xbmcaddon.Addon()
    __takoyaki_id = 'script.module.takoyaki'
    __addon_id__ = __addon__.getAddonInfo('id')

    def __init__(self):

        self.__addon_user_data__ = xbmcvfs.translatePath(self.path_join('special://userdata/addon_data', self.__addon_id__))
        self.params = self.parse_parameter()
        self.is_login = self.__addon__.getSetting('login')
        if self.is_login:
            self.password = self.__addon__.getSetting('password')
            self.username = self.__addon__.getSetting('username')
        self.session = self.open_session()

    def set_basic_auth(self, user, password):
        self.session.auth = (user, password)

    def open_session(self):
        session = requests.Session()
        headers = {'user_agent': self.USER_AGENT}
        session.headers.update(headers)
        return session

    def run(self):
        modes = None
        self.select_mode(modes)

    def select_mode(self, modes, default_mode='top_menu'):
        mode = self.params.get('mode', default_mode)
        selected_mode = modes.get(mode)
        selected_mode()

    def login(self, login_url, query, mode='post'):

        if mode == 'get' or mode == 'g':
            self.session.get(login_url,  params=query)
        elif mode == 'post' or mode == 'p':
            self.session.post(login_url,  data=query)
        else:
            raise ValueError('Unexpected mode')

    @classmethod
    def path_join(cls, path, *paths):
        return os.path.join(path, *paths).replace('\\', '/')

    @classmethod
    def url_join(cls, base, *urls):
        jointed_url = base
        for url in urls:
            jointed_url = urljoin(jointed_url,url)
        return jointed_url

    @classmethod
    def abs_url(cls, *urls):

        url = cls.url_join("", *urls)
        base = cls.BASE_URL.rstrip("/")
        url = url.replace(base, "")

        return cls.url_join(cls.BASE_URL, url)

    @classmethod
    def build_url(cls, query):
        return sys.argv[0] + '?' + urlencode(query)

    @classmethod
    def parse_parameter(cls):
        params = parse_qs(sys.argv[2][1:])
        return {key: value[0] for key, value in params.items()}

    def download_html(self, url, mode='get', query={}):

        if mode == 'get' or mode == 'g':
            return self.session.get(url, params=query).text
        elif mode == 'post' or mode == 'p':
            return self.session.post(url, data=query).text

        raise ValueError('Unexpected mode')

    def parse_html(self, string):
        if len(urlparse(string).scheme) >= 1:
            html = self.download_html(string)
        else:
            html = string
        return BeautifulSoup(html)

    def end_of_directory(self, mode=None):
        if mode is not None:
            xbmcplugin.setContent(self.__handle__, mode)
        xbmcplugin.endOfDirectory(self.__handle__)

    def add_directory(self, param, list_item, images=None):
        li = xbmcgui.ListItem(**list_item)
        if images is not None:
            li.setArt(images)

        param_url = self.build_url(param)
        xbmcplugin.addDirectoryItem(handle=self.__handle__, url=param_url, listitem=li, isFolder=True)

    def add_media_file(self, url, list_item, images=None, info=None, properties=None):
        li = xbmcgui.ListItem(**list_item)
        if images is not None:
            li.setArt(images)
        if info is not None:
            li.setInfo(*info)
        if properties is not None:
            li.setProperty(*properties)
        xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=li, isFolder=False)

    @classmethod
    def play_media(cls, item, list_item, info=None, properties=None):

        li = xbmcgui.ListItem(**list_item)
        if info is not None:
            li.setInfo(*info)
        if properties is not None:
            li.setProperty(*properties)
        xbmc.Player().play(item=item, listitem=li)

    @classmethod
    def log(cls, message, log_level):
        xbmc.log(message, log_level.value)

    @classmethod
    def get_search_string(cls, message='', heading=''):
        search_string = None
        keyboard = xbmc.Keyboard(message, heading)
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_string = keyboard.getText()
        return search_string

    USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    BASE_URL =""
    SEARCH_URL = ""
    ICON_URL = ""
    
    ENTRY_SELECTOR = "articl"
    SERIES_SELECTOR = ENTRY_SELECTOR
    EPISODE_SELECTOR = ENTRY_SELECTOR


    @classmethod
    def get_entry_url(cls, entry):
        if len(entry.select("a")) >= 1:
            element = entry.a
        else:
            element = entry

        url = element.get("href", None)
        if url is not None:
            return cls.abs_url(url)
        url = element.get("href", None)
        if url is None:
            return None
        return cls.abs_url(url)

    @classmethod
    def get_entry_title(cls, entry):
        if len(entry.select("a")) >= 1:
            element = entry.a
        else:
            element = entry

        title = element.get("title", None)
        if title is None:
            title = element.text.strip()

        return title if  title != "" else None

    @classmethod
    def get_entry_imag_url(cls, entry):
        if entry.img is None:
            element = entry
        else:
            element = entry.img

        img_url = element.get("data-src", None)
        if img_url is None:
            img_url = element.get("src", None)
        
        if img_url is None:
            return None
        return cls.abs_url(img_url)

    def add_default_directory(self, mode, link, title, img_url):
        params = {'mode': mode, 'link': link,'title': title, 'img_url': img_url, 'site': self.SITE}
        images = { 
            self.ImageSet.ICON.value: img_url,
            self.ImageSet.FANART.value: img_url
        }

        list_item = {"label" : title}
        self.add_directory(params, list_item, images)
    
    @classmethod
    def get_next_page_url(cls, parser):
        next_page = parser.select('.next')
        if len(next_page) == 0:
            next_page = parser.select('[rel="next"]')[0]["href"]
        else:
            next_page = next_page[0]["href"]

        return cls.abs_url(next_page)

    def add_next_directory(self, parser):
        next_page = self.get_next_page_url
        
        params = {'mode': 'entry', 'link': next_page, 'site': self.SITE}
        images = { 
            self.ImageSet.ICON.value: self.ICON_URL,
            self.ImageSet.FANART.value: self.ICON_URL
        }

        list_item = {'label': 'Next'}
        self.add_directory(params, list_item, images)
        

    def entry_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        entries = parser.select(self.ENTRY_SELECTOR)

        for entry in entries:
            link = self.get_entry_url(entry)

            title = self.get_entry_title(entry)
            
            img_url = self.get_entry_imag_url(entry)


            if link is None or title is None or img_url is None:
                continue

            self.add_default_directory('play_list', link, title, img_url)

        try:
            next_page = self.get_next_page_url(parser)
            self.add_default_directory("entry", next_page, "Next", self.ICON_URL)
        except (AttributeError, IndexError):
            pass
        
        self.end_of_directory()

    TAG_LIST_SELECTOR = ".tagcloud a"
    TAG_MODE = "entry"

    @classmethod
    def get_tag_url(cls, entry): return cls.get_entry_url(entry)
    @classmethod
    def get_tag_title(cls, entry): return cls.get_entry_title(entry)
    @classmethod
    def get_tag_img_url(cls, entry):
         return cls.ICON_URL
    
    def tag_list_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        tags =  parser.select(self.TAG_LIST_SELECTOR)
            
        for tag in tags:
            link = self.get_tag_url(tag)
            title = self.get_tag_title(tag)
            img_url = self.get_tag_img_url(tag)

            self.add_default_directory(self.TAG_MODE, link, title, img_url)
        self.end_of_directory()

    LETTER_MODE = "letter_item"
    LETTER_URL_SUFFIX =""
    def get_letter_url(self, letter ):
        url_suffix = "0-9" if letter == "#" else letter
        url = self.url_join(self.BASE_URL, self.LETTER_URL_SUFFIX + url_suffix)
        return url

    def letter_mode(self):
        letters = ["#","A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
                        "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

        for letter in letters:
            url = self.get_letter_url(letter)
  
            self.add_default_directory(self.LETTER_MODE, url, letter, self.ICON_URL)

        self.end_of_directory()
    
    LETTER_SELECTOR = "li"
    LETTER_ITEM_MODE = "series"
    @classmethod
    def get_letter_item_url(cls, entry): return cls.get_entry_url(entry)
    @classmethod
    def get_letter_item_title(cls, entry): return cls.get_entry_title(entry)
    
    @classmethod
    def get_item_list_by_letter(cls,letter, items):
        items = [item for item in items if item["title"] is not None]
        if letter == "#":
            return [item for item in items if item["title"][0] >= "0" and item["title"][0] <= "9" ]
        else:
            return [item for item in items if item["title"][0].upper() == letter]

    def letter_item_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        entries = parser.select(self.LETTER_SELECTOR)
        letter = self.params["title"]
        items = [{"link": self.get_letter_item_url(item),
                "title": self.get_letter_item_title(item)}
                for item in entries]
        items = self.get_item_list_by_letter(letter, items)
        for item in items:
            link = item["link"]
            title = item["title"]

            self.add_default_directory(self.LETTER_ITEM_MODE, link, title, "")
        self.end_of_directory()
    
    @classmethod
    def get_series_url(cls, entry): return cls.get_entry_url(entry)
    @classmethod
    def get_series_title(cls, entry): return cls.get_entry_title(entry)
    @classmethod
    def get_series_img_url(cls, entry): return cls.get_entry_imag_url(entry)

    def series_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        entries = parser.select(self.ENTRY_SELECTOR)

        for entry in entries:
            link = self.get_series_url(entry)

            title = self.get_series_title(entry)
            
            img_url = self.get_series_img_url(entry)


            if link is None or title is None or img_url is None:
                continue

            self.add_default_directory('episode', link, title, img_url)

        try:
            next_page = self.get_next_page_url(parser)
            self.add_default_directory("series", next_page, "Next", self.ICON_URL)
        except (AttributeError, IndexError):
            pass
        
        self.end_of_directory()

    
    @classmethod
    def get_episode_url(cls, entry): return cls.get_entry_url(entry)
    @classmethod
    def get_episode_title(cls, entry): return cls.get_entry_title(entry)
    @classmethod
    def get_episode_img_url(cls, entry): return cls.get_entry_imag_url(entry)
    def episode_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        entries = parser.select(self.EPISODE_SELECTOR)

        for entry in entries:
            link = self.get_episode_url(entry)

            title = self.get_episode_title(entry)
            
            img_url = self.get_episode_img_url(entry)


            if link is None or title is None or img_url is None:
                continue

            self.add_default_directory('play_list', link, title, img_url)

        try:
            next_page = self.get_next_page_url(parser)
            self.add_default_directory("episode", next_page, "Next", self.ICON_URL)
        except (AttributeError, IndexError):
            pass
        
        self.end_of_directory()


    @classmethod
    def normalaze_query(cls, query):
        return query.strip().replace(" ", "+")

    def search(self):

        query = self.get_search_string()
        query = self.normalaze_query(query)
        
        url = self.params['link'].format(query)
        mode = self.params.get("target_mode", "entry")
    
        params = {'mode': mode, 'site': self.SITE, 'link': url}
        list_item = {'label': query}
        self.add_directory(params, list_item)
        self.end_of_directory()

    def get_media_url_list(self, url):
        reg = re.compile('file"? ?: ?"(.+?)"')
        media_url_list = []

        html = self.download_html(url)
        result = reg.findall(html)
        if len(result) >= 1:
            for item in result:
                url = self.abs_url(item.replace("\\", ""))
                media_url_list.append(url)
            return media_url_list
        
        parser = self.parse_html(html)
        sources = parser.select("source")
        if len(sources) >= 1:
            for source in sources:
                media_url_list.append(self.abs_url(source["src"]))
            return media_url_list

        raise ValueError("Not found source.")

    def play_list(self):
        link = self.params['link']
        meida_url_lsit = self.get_media_url_list(link)
        if len(meida_url_lsit) == 1:
            self.play_media(meida_url_lsit[0], {"label": self.params["title"]})
            return

        for i, url in enumerate(meida_url_lsit, 1):
            self.add_default_directory("play", url, "Source " + str(i), self.params["imag_url"])

    def play(self):
        link = self.params['link']
        self.play_media(link, {"label": self.params["title"]})


    def get_top_menus(self):
        menus = [
            {'title': 'Home',
                'mode': 'entry',
                'link': self.BASE_URL},
            {'title': 'Search',
                'mode': "search",
                'target_mode': "entrys",
                "link": self.SEARCH_URL}
        ]

        return menus

    def top_menu(self):
        menus = self.get_top_menus()

        for menu in menus:

            self.add_default_directory(menu["mode"], menu["link"], menu['title'],"")
        self.end_of_directory()

    def run(self):
        modes = {
                'top_menu': self.top_menu,
                'entry': self.entry_mode,
                'play_list': self.play_list,
                'play': self.play,
                'letters': self.letter_mode,
                'letter_item': self.letter_item_mode,
                'series': self.series_mode,
                'episode': self.episode_mode,
                'tag_list': self.tag_list_mode,
                'search': self.search,
            }

        self.select_mode(modes)
    
    def open(self):
        self.run()
      