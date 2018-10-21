import re


def reg_find_first(string: str, pattern):
    if type(string) == 'str':
        return re.findall(pattern, string)[0]
    else:
        return  pattern.findall(string)[0]
