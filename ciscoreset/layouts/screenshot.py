import PySimpleGUI as sg
from pathlib import Path
from ._utils import image_to_base64


def create_screenshot_viewer() -> list:
    screenshot_path = Path("tmp/screenshot.bmp")
    if not screenshot_path.is_file():
        photo = None
    else:
        photo = image_to_base64("tmp/screenshot.bmp", (400, 240))

    return [
        [
            sg.Image(
                photo,
                key="-SCREENSHOT-",
                size=(400, 240),
            )
        ]
    ]
