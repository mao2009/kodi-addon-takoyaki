import xbmc

DEBUG = 1
INFO = 2
NOTICE = 3
WARNING = 4
ERROR = 5
SEVERE = 5
FATAL = 7
NONE = 8


def log(message, log_lavel=None):
    if log_lavel is None:
        xbmc.log(message)
    else:
        xbmc.log(message, log_lavel)