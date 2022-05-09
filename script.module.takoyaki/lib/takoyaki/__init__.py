# codec: utf-8

import os
import sys
import pickle
from urllib.parse import urljoin, urlencode, parse_qs, urlparse
import requests

from bs4 import BeautifulSoup

import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
import xbmcplugin

from enum import Enum


class Takoyaki(object):

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
        
    USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

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

