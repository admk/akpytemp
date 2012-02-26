import os

__color_enable = 1

def set_color_enable(enable):
    global __color_enable
    __color_enable = enable

def check_enable(color):
    global __color_enable
    if ('color' in os.environ['TERM']) and __color_enable:
        return color
    else:
        return ''

class Colors(object):
    """A class with terminal colors
    This class defines a set of colors suitable for making colored outputs
    """
    HEADER = check_enable('\033[95m')
    BLUE = check_enable('\033[94m')
    GREEN = check_enable('\033[92m')
    WARNING = check_enable('\033[93m')
    FAIL = check_enable('\033[91m')
    END = check_enable('\033[0m')
