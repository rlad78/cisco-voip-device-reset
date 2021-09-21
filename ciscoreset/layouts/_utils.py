import PIL.Image
from PIL import ImageFile
import io
import base64
import ctypes
import platform
from PySimpleGUI import WIN_CLOSED

"""
    Demo for displaying any format of image file.

    Normally tkinter only wants PNG and GIF files.  This program uses PIL to convert files
    such as jpg files into a PNG format so that tkinter can use it.

    The key to the program is the function "convert_to_bytes" which takes a filename or a 
    bytes object and converts (with optional resize) into a PNG formatted bytes object that
    can then be passed to an Image Element's update method.  This function can also optionally
    resize the image.

    Copyright 2020 PySimpleGUI.org
"""

ImageFile.LOAD_TRUNCATED_IMAGES = True


def image_to_base64(file_or_bytes, resize=None):
    """
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    """
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height / cur_height, new_width / cur_width)
        img = img.resize(
            (int(cur_width * scale), int(cur_height * scale)), PIL.Image.ANTIALIAS
        )
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()


def make_dpi_aware():
    if platform.system() == "Windows" and int(platform.release().split(".")[0]) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)


def should_exit(event, *exit_events) -> bool:
    if event in (WIN_CLOSED, "Exit", *exit_events):
        return True
    else:
        return False
