import sys
import re
from urllib.parse import urlparse
import requests
import importlib
from typing import List, Dict, Optional, Union

from bs4 import BeautifulSoup

import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
import xbmcplugin

from takoyaki.utilites import (PresetMode, ImageSet, LogLevel,
                                log, path_join, url_join, build_url,
                                parse_parameter, normalaze_query, get_page_index)


class Takoyaki(object):

    __base__url:str = sys.argv[0]
    __handle__ = int(sys.argv[1])
    __addon__ = xbmcaddon.Addon()
    __takoyaki_id = 'script.module.takoyaki'
    __addon_id__: str = __addon__.getAddonInfo('id')

    PresetMode = PresetMode
    ImageSet = ImageSet
    LogLevel = LogLevel
    log = log
    path_join = path_join
    url_join = url_join
    build_url = build_url
    parse_parameter = parse_parameter
    normalaze_query = normalaze_query
    get_page_index = get_page_index()

    USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    
    BASE_URL =""
    ICON_URL = ""
    __DEFAULT_SELECTOR = "article"
    def __init__(self):
        self.__addon_user_data__: str = xbmcvfs.translatePath(path_join('special://userdata/addon_data', self.__addon_id__))
        self.params = parse_parameter()
        self.MODULE_NAME = self.params.get("module_name")

        self.is_login = self.__addon__.getSetting('login')

        if self.is_login:
            self.password: str = self.__addon__.getSetting('password')
            self.username: str = self.__addon__.getSetting('username')
        self.session = self.open_session()

    def set_basic_auth(self, user, password):
        self.session.auth = (user, password)

    def open_session(self):
        session = requests.Session()
        headers = {'user_agent': self.USER_AGENT}
        session.headers.update(headers)
        return session

    
    def import_module(self):
        module_name = self.params.get('module_name')
        if module_name is None:
            self.module_list_mode()
        else:
            importlib.import_module(module_name).open()

    def select_mode(self, modes: Dict[str, object], default_mode='top_menu'):
        mode = self.params.get('mode', default_mode)
        selected_mode = modes.get(mode)
        selected_mode()

    def login(self, login_url: str, query: Dict[str, str], mode='post'):

        if mode == 'get' or mode == 'g':
            self.session.get(login_url,  params=query)
        elif mode == 'post' or mode == 'p':
            self.session.post(login_url,  data=query)
        else:
            raise ValueError('Unexpected mode')

    def download_html(self, url: str, mode='get', query: Dict[str, str] ={}) -> str: 

        if mode == 'get' or mode == 'g':
            return self.session.get(url, params=query).text
        elif mode == 'post' or mode == 'p':
            return self.session.post(url, data=query).text

        raise ValueError('Unexpected mode')

    def parse_html(self, string: str) -> BeautifulSoup:
        if len(urlparse(string).scheme) >= 1:
            html = self.download_html(string)
        else:
            html = string
        return BeautifulSoup(html)

    def end_of_directory(self, mode=None):
        if mode is not None:
            xbmcplugin.setContent(self.__handle__, mode)
        xbmcplugin.endOfDirectory(self.__handle__)

    def add_directory(self, param: Dict[str, str], list_item: Dict[str, str], images: Dict[str, str]=None):
        li = xbmcgui.ListItem(**list_item)
        if images is not None:
            li.setArt(images)

        param_url = build_url(param)
        xbmcplugin.addDirectoryItem(handle=self.__handle__, url=param_url, listitem=li, isFolder=True)

    def add_media_file(self, url: str, list_item: Dict[str, str], images: Dict[str, str]=None, info: Dict[str, str]=None, properties: Dict[str, str]=None):
        li = xbmcgui.ListItem(**list_item)
        if images is not None:
            li.setArt(images)
        if info is not None:
            li.setInfo(*info)
        if properties is not None:
            li.setProperty(*properties)
        xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=li, isFolder=False)

    @classmethod
    def play_media(cls, item: str, list_item: Dict[str, str], images: Dict[str, str]=None, info: Dict[str, str]=None, properties: Dict[str, str]=None):

        li = xbmcgui.ListItem(**list_item)
        if info is not None:
            li.setInfo(*info)
        if properties is not None:
            li.setProperty(*properties)
        if images is not None:
            li.setArt(images)
        xbmc.Player().play(item=item, listitem=li)

    @classmethod
    def abs_url(cls, *urls: str) -> str:
        url = url_join("", *urls)

        if url is None:
            return

        if len(urlparse(url).scheme) >= 1:
            return url
        
        if url.startswith("//"):
            scheme = urlparse(cls.BASE_URL).scheme
            return scheme + ":" + url

        return url_join(cls.BASE_URL, url)

    @classmethod
    def get_search_string(cls, message='', heading='') -> str:
        search_string: str = None
        keyboard = xbmc.Keyboard(message, heading)
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_string = keyboard.getText()
        return search_string
    
    entry_selector = __DEFAULT_SELECTOR
    seriese_selector = __DEFAULT_SELECTOR
    episode_selector = __DEFAULT_SELECTOR

    @classmethod
    def get_entry_url(cls, element: BeautifulSoup) -> Optional[str]:

        url = cls.get_href(element)
        if url is None:
            None
        
        return cls.abs_url(url)

    @classmethod
    def get_entry_title(cls, element: BeautifulSoup) -> Optional[str]:

        if element.name == "a":
            a = element
        elif cls.exists(element.a):
            a = element.a
        else:
            a = None

        if cls.exists(a):
            title = a.get("title", a.text.strip())
        else:
            title = ""

        if title != "":
            return title

        if element.name == "img":
            img = element
        elif cls.exists(element.img):
            img = element.img
        else:
            img = None

        if cls.exists(img):
            return img.get("alt")
        
        return None

    @classmethod
    def get_entry_img_url(cls, element: BeautifulSoup):
        if element.img is not None:
            element = element.img

        img_url = element.get("data-src", None)
        if img_url is None:
            img_url = element.get("src", None)
        
        if img_url is None:
            return None
        return cls.abs_url(img_url)

    def add_default_directory(self, mode: str, link: str, title: str, img_url: str, **ex_params):
        params = {'mode': mode, 'link': link,'title': title, 'img_url': img_url, 'module_name': self.MODULE_NAME}
        images = { 
            self.ImageSet.ICON: img_url,
            self.ImageSet.FANART: img_url,
            self.ImageSet.THUMB: img_url
        }

        list_item = {"label" : title}

        if len(ex_params) >= 1:
            params.update(ex_params)
             
        self.add_directory(params, list_item, images)
    
    def exclud_default_params(self, params) -> Dict[str, str]:
        return {key: value for key, value  in params.items() if not key in ("mode", "link", "title", "img_url", "module_name")}

    NEXT_PAGE_ERROR_LIST = (KeyError, AttributeError, IndexError)

    next_page_selector = ".next"

    def get_next_page_url(self, parser: BeautifulSoup) -> Optional[str]:
        def get_url(selector):
            elements = parser.select(selector)
            if len(elements) >= 1:
                element = elements[0]
                next_page = self.get_href(element)
                if self.exists(next_page):
                    return self.abs_url(next_page)
            return None

        next_page = get_url(self.next_page_selector)
        if self.exists(next_page):
            return next_page

        next_page = get_url(".next")
        if self.exists(next_page):
            return next_page

        next_page = get_url("[rel='next']")
        if self.exists(next_page):
            return next_page
        return None

    @classmethod
    def get_href(cls, element: BeautifulSoup) -> Optional[str]:
        if element.has_attr("href"):
            return element["href"]

        if element.name == "a":
            a = element
        elif cls.exists(element.a):
            a = element.a
        else:
            return None
        
        return a.get("href")

    @classmethod
    def exists(cls, obj) -> bool:
        return obj is not None

    def add_next_directory(self, parser: BeautifulSoup):
        next_page = self.get_next_page_url(parser)
        if next_page is None:
            return

        params = {'mode': 'entry', 'link': next_page, 'module_name': self.MODULE_NAME}
        images = self.get_default_images()

        list_item = {'label': 'Next'}
        self.add_directory(params, list_item, images)
        
    entry_directory_mode = "play_list"
    def entry_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        elements = parser.select(self.entry_selector)

        for element in elements:
            link = self.get_entry_url(element)

            title = self.get_entry_title(element)
            
            img_url = self.get_entry_img_url(element)
           
            if link is None or title is None or img_url is None:
                continue
            
            self.add_default_directory(self.entry_directory_mode, link, title, img_url, media_title=title)

        try:
            next_page = self.get_next_page_url(parser)
            self.add_default_directory("entry", next_page, "Next", self.ICON_URL)
        except self.NEXT_PAGE_ERROR_LIST as ex:
            pass
        
        self.end_of_directory()

    tag_selector = ".tagcloud a"
    tag_directory_mode = "entry"

    @classmethod
    def get_tag_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_url(element)
    @classmethod
    def get_tag_title(cls, element: BeautifulSoup) -> str: return cls.get_entry_title(element)
    @classmethod
    def get_tag_img_url(cls, element: BeautifulSoup) -> str:
         return cls.ICON_URL
    
    def tag_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        elements =  parser.select(self.tag_selector)

        for element in elements:
            link = self.get_tag_url(element)
            title = self.get_tag_title(element)
            img_url = self.get_tag_img_url(element)

            self.add_default_directory(self.tag_directory_mode, link, title, img_url)
        self.end_of_directory()

    tag_list_selector = ".tagcloud a"
    tag_list_directory_mode = "entry"

    @classmethod
    def get_tag_list_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_url(element)
    @classmethod
    def get_tag_list_title(cls, element: BeautifulSoup) -> str: return cls.get_entry_title(element)
    @classmethod
    def get_tag_list_img_url(cls, element: BeautifulSoup) -> str:
         return cls.ICON_URL
    
    def tag_list_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        elements =  parser.select(self.tag_list_selector)

        for element in elements:
            link = self.get_tag_url(element)
            title = self.get_tag_title(element)
            img_url = self.get_tag_img_url(element)

            self.add_default_directory(self.tag_list_directory_mode, link, title, img_url)
        self.end_of_directory()

    genre_selector = "article"
    genre_directory_mode = "entry"
    
    classmethod
    def get_genre_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_url(element)
    @classmethod
    def get_genre_title(cls, element: BeautifulSoup) -> str: return cls.get_entry_title(element)
    @classmethod
    def get_genre_img_url(cls, element: BeautifulSoup) -> str:
         return cls.ICON_URL

    def genre_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        elements =  parser.select(self.genre_selector)
            
        for element in elements:
            link = self.get_genre_url(element)
            title = self.get_genre_title(element)
            img_url = self.get_genre_img_url(element)

            self.add_default_directory(self.genre_directory_mode, link, title, img_url)


        self.end_of_directory()

    catetgory_selector = "artcle"
    category_directory_mode = "entry"
    
    classmethod
    def get_category_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_url(element)
    @classmethod
    def get_category_title(cls, element: BeautifulSoup) -> str: return cls.get_entry_title(element)
    @classmethod
    def get_category_img_url(cls, element: BeautifulSoup) -> str:
         return cls.ICON_URL

    def category_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        elements =  parser.select(self.catetgory_selector)
            
        for elemnt in elements:
            link = self.get_category_url(elemnt)
            title = self.get_category_title(elemnt)
            img_url = self.get_category_img_url(elemnt)

            self.add_default_directory(self.category_directory_mode, link, title, img_url)
        self.end_of_directory()      
        
    letter_directory_mode = "letter_item"
    letter_url_suffix =""
    letters =  ["#","A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
                        "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

    def get_letter_url(self, letter: str) -> str:
        return self.params["link"]

    def letter_mode(self):

        for letter in self.letters:
            url = self.get_letter_url(letter)

            self.add_default_directory(self.letter_directory_mode, url, letter, self.ICON_URL)

        self.end_of_directory()
    
    letter_item_selector = "li"
    letter_item_directory_selector = "series"

    @classmethod
    def get_letter_item_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_url(element)
    @classmethod
    def get_letter_item_title(cls, element: BeautifulSoup) -> str: return cls.get_entry_title(element)
    
    @classmethod
    def get_item_list_by_letter(cls, letter: str, items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        
        items = [item for item in items if item["title"] is not None]
        if letter == "#":
            return [item for item in items if item["title"][0].upper() < "A" or item["title"][0].upper() > "Z"]
        else:
            return [item for item in items if item["title"][0].upper() == letter.upper()]

    def letter_item_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        entries = parser.select(self.letter_item_selector)
        letter = self.params["title"]
        items = [{"link": self.get_letter_item_url(item),
                "title": self.get_letter_item_title(item)}
                for item in entries]

        items = self.get_item_list_by_letter(letter, items)
        for item in items:
            link = item["link"]
            title = item["title"]

            self.add_default_directory(self.letter_item_directory_selector, link, title, "", letter=letter)
        self.end_of_directory()

    series_directory_mode = "episode"
    @classmethod
    def get_series_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_url(element)
    @classmethod
    def get_series_title(cls, element: BeautifulSoup) -> str: return cls.get_entry_title(element)
    @classmethod
    def get_series_img_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_img_url(element)

    def series_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        elements = parser.select(self.seriese_selector)

        for element in elements:
            link = self.get_series_url(element)

            title = self.get_series_title(element)
            
            img_url = self.get_series_img_url(element)


            if link is None or title is None or img_url is None:
                continue

            self.add_default_directory(self.series_directory_mode, link, title, img_url, series_title=title)

        try:
            next_page = self.get_next_page_url(parser)
            self.add_default_directory("series", next_page, "Next", self.ICON_URL)
        except self.NEXT_PAGE_ERROR_LIST:
            pass
        
        self.end_of_directory()

    episode_directory_mode = "play_list"

    @classmethod
    def get_episode_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_url(element)
    @classmethod
    def get_episode_title(cls, element: BeautifulSoup) -> str: return cls.get_entry_title(element)
    @classmethod
    def get_episode_img_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_img_url(element)

    def episode_mode(self):
        link = self.params['link']
        parser = self.parse_html(link)
        elements = parser.select(self.episode_selector)
        series_title = self.params.get("series_title")
        for element in elements:
            link = self.get_episode_url(element)

            title = self.get_episode_title(element)
            
            img_url = self.get_episode_img_url(element)


            if link is None or title is None or img_url is None:
                continue
            
            self.add_default_directory(self.episode_directory_mode, link, title, img_url, series_title=series_title, episode_title=title)

        try:
            next_page = self.get_next_page_url(parser)
            self.add_default_directory("episode", next_page, "Next", self.ICON_URL)
        except self.NEXT_PAGE_ERROR_LIST:
            pass
        
        self.end_of_directory()

    def search(self):

        query = self.get_search_string()
        query = normalaze_query(query)
        
        url = self.params['link'].format(query)
        mode = self.params.get("target_mode", "entry")
    
        params = {'mode': mode, 'module_name': self.MODULE_NAME, 'link': url}
        list_item = {'label': query}
        self.add_directory(params, list_item)
        self.end_of_directory()

    def get_media_url_list(self, url) -> Union[List[str], List[Dict[str, str]]]:
        reg = re.compile('file"? ?: ?"(.+?)"')
        media_url_list: list[str] = []

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

    def get_default_images(self) -> Dict[str, str]:
        img_url = self.params.get("img_url", self.ICON_URL)
        images = { 
            self.ImageSet.ICON: img_url,
            self.ImageSet.FANART: img_url,
            self.ImageSet.THUMB: img_url}
        return images

    def get_media_title(self):
        if "media_title" in self.params:
            return self.params["media_title"]
       
        series_title = self.params["series_title"] if "series_title" in self.params else ""
        episode_title = self.params["episode_title"] if "episode_title" in self.params else ""

        media_title = series_title

        if media_title != "" and episode_title != "":
            media_title += " - "
        else:
            return self.params["title"]
        
        media_title += episode_title
        
        return media_title

    def play_list(self):
        link = self.params['link']
        meida_url_lsit = self.get_media_url_list(link)
        images = self.get_default_images()
        title = self.get_media_title()
        
        if len(meida_url_lsit) == 1:
            meida_url = meida_url_lsit[0]
            if type(meida_url) is str:
                self.play_media(meida_url, {"label": title}, images)

            elif type(meida_url) is dict:
                url = meida_url["src"]
                self.play_media(url, {"label": title}, images)
                
            return

        for i, meida_url in enumerate(meida_url_lsit, 1):
            if type(meida_url) is str:
                self.add_default_directory("play", meida_url, "Source " + str(i))

            elif type(meida_url) is dict:
                url = meida_url["src"]
                label = meida_url["label"]
                self.add_default_directory("play", url, label)

        self.end_of_directory()

    def play(self):
        title = title = self.get_media_title()
        
        link = self.params['link']
        self.play_media(link, {"label": title})


    media_file_selector = "article"
    @classmethod
    def get_media_file_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_url(element)
    @classmethod
    def get_media_file_title(cls, element: BeautifulSoup) -> str: return cls.get_entry_title(element)
    @classmethod
    def get_media_file_img_url(cls, element: BeautifulSoup) -> str: return cls.get_entry_img_url(element)

    def media_file_mode(self):
        link = self.params['link']
        
        parser = self.parse_html(link)
        elements = parser.select(self.media_file_selector)
        for element in elements:
            link = self.get_media_file_url(element)
            title = self.get_media_file_title(element)
            if title is None:
                title = "Page " + str(next(self.get_page_index))

            if link is None:
                continue

            img_url = self.get_media_file_img_url(element)
            list_item = {'label': title}
            images = {self.ImageSet.THUMB: img_url}
            self.add_media_file(link, list_item=list_item, images=images)
        self.end_of_directory()

    def get_top_menus(self) -> List[Dict[str, str]]:
        menus = [
            {'title': 'Home',
                'mode': 'entry',
                'link': self.BASE_URL},
            {'title': 'Search',
                'mode': "search",
                'target_mode': "entry",
                "link": self.search_url}
        ]

        return menus

    def get_module_list(self) -> List[Dict[str, str]]: return []

    def module_list_mode(self):
        for module in self.get_module_list():
            list_item = {'label' : module['title']}
            images = { self.ImageSet.ICON: module.get('img_url', None), 
                       self.ImageSet.FANART: module.get('fanart', None)}
                       
            self.add_directory(module, list_item, images)

        self.end_of_directory()

    def top_menu(self):
        menus = self.get_top_menus()

        for menu in menus:
            excluded =self.exclud_default_params(menu)
            self.add_default_directory(menu["mode"], menu["link"], menu['title'],"", **excluded)
        self.end_of_directory()

    def get_mode_list(self) -> dict:
            return {
                self.PresetMode.TOP_MENU: self.top_menu,
                self.PresetMode.ENTRY: self.entry_mode,
                self.PresetMode.PLAY_LIST: self.play_list,
                self.PresetMode.PLAY: self.play,
                self.PresetMode.MEDIA_FILE: self.media_file_mode,
                self.PresetMode.LETTER: self.letter_mode,
                self.PresetMode.LETTER_ITME: self.letter_item_mode,
                self.PresetMode.SERIES: self.series_mode,
                self.PresetMode.EPISODE: self.episode_mode,
                self.PresetMode.TAG: self.tag_mode,
                self.PresetMode.TAG_LIST: self.tag_list_mode,
                self.PresetMode.GENRE: self.genre_mode,
                self.PresetMode.CATEGORY: self.category_mode,
                self.PresetMode.SEARCH: self.search,
            }
            
    def run(self):
        modes = self.get_mode_list()
        self.select_mode(modes)
    
    def open(self):
        self.run()
