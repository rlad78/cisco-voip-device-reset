from PySimpleGUI.PySimpleGUI import DEFAULT_TEXT_COLOR
from ciscoreset.credentials import get_credentials
import PySimpleGUI as sg
from ciscoreset.utils import image_to_base64, make_dpi_aware, should_exit
from ciscoreset.gui_popups import popups_credentials_group
from ciscoreset import __version__, PhoneConnection
from icecream import ic
from pathlib import Path
import asyncio


def create_title() -> list:
    title = sg.Text("Cisco VoIP Device Reset", font="Any 20")
    version = sg.Text(__version__, font="Any 10")
    return [[title, version]]


def create_ip_entry() -> list:
    return [
        [sg.Text("IP Address of device:")],
        [
            sg.In("", size=(18, 1), key="-IP-"),
            sg.Button("Connect", bind_return_key=True),
        ],
        [sg.Text("", key="-STATUS-")],
    ]


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


def create_reset_menu() -> list:
    return [
        [sg.Text("Reset Phone")],
        [sg.Button("Soft Reset"), sg.Button("Device Settings")],
        [sg.Button("Network"), sg.Button("Service Mode"), sg.Button("Security")],
    ]


def create_navigation_menu() -> list:
    directional_buttons = [
        [sg.Button("↑", key="navUp", tooltip="Up", button_color=("white", "black"))],
        [
            sg.Button(
                "←", key="navLeft", tooltip="Left", button_color=("white", "black")
            ),
            sg.Button(
                "o", key="navSelect", tooltip="Select", button_color=("black", "silver")
            ),
            sg.Button(
                "→", key="navRight", tooltip="Right", button_color=("white", "black")
            ),
        ],
        [
            sg.Button(
                "↓", key="navDown", tooltip="Down", button_color=("white", "black")
            ),
        ],
    ]

    def dial_factory(num_string: str) -> list[sg.Button]:
        return [
            sg.Button(c, key=f"dial{c}", button_color=("white", "black"))
            for c in num_string
        ]

    dial_pad = [dial_factory(chars) for chars in ["123", "456", "789", "*0#"]]

    return [
        [
            sg.Button(
                "⮌", key="navBack", tooltip="Back", button_color=("white", "black")
            ),
            sg.Column(
                directional_buttons,
                pad=(20, 0),
                element_justification="c",
                vertical_alignment="center",
            ),
            sg.Button(
                "🕽", key="endCall", tooltip="Hang Up", button_color=("red", "black")
            ),
        ],
        [
            sg.Column(
                dial_pad,
                pad=(0, 5),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
            )
        ],
    ]


def main_window_blueprint() -> sg.Window:
    win_top = create_title()

    enter_ip = create_ip_entry()
    screenshot_viewer = create_screenshot_viewer()

    reset_menu = create_reset_menu()
    nav_menu = create_navigation_menu()

    layout = [
        [sg.Column(win_top, justification="center")],
        [
            sg.Column(
                enter_ip,
                pad=(100, 15),
                justification="center",
                vertical_alignment="center",
            ),
            sg.VSeparator(),
            sg.Column(screenshot_viewer, pad=(15, 15)),
        ],
        [sg.HSeparator(pad=(0, 5), key="-MENU_SEP-")],
        [
            sg.Column(
                reset_menu,
                pad=(20, 15),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
                # visible=False,
                key="-RESET_MENU-",
            ),
            sg.Column(
                nav_menu,
                pad=(20, 15),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
                # visible=False,
                key="-NAV_MENU-",
            ),
        ],
    ]

    return sg.Window(f"Cisco VoIP Device Reset {__version__}", layout)


async def update_screenshot(phone: PhoneConnection, gui_element: sg.Image) -> None:
    ic("downloading screenshot")
    img = image_to_base64(phone._screenshot(), (400, 240))
    ic("screenshot downloaded")
    gui_element.update(img)


def run() -> None:
    make_dpi_aware()

    url, port, username, password = popups_credentials_group()
    if not url:
        return None

    window = main_window_blueprint()
    phone = None
    try:
        while True:
            event, values = window.read()
            if should_exit(event):
                break
            if event == "Connect":
                window["-STATUS-"].update(
                    "Connecting...", text_color=DEFAULT_TEXT_COLOR
                )
                window.refresh()
                try:
                    phone = PhoneConnection(
                        values["-IP-"], username=username, password=password
                    )
                except Exception as e:
                    err_msg = str(e)
                    phone = None
                else:
                    err_msg = ""

                if err_msg:
                    window["-STATUS-"].update(err_msg, text_color="orange")
                else:
                    window["-STATUS-"].update(
                        f"Cisco {phone.device_model}"
                        + "\n"
                        + phone.device_name
                        + "\n"
                        + phone.get_phone_desc()
                        + "\n"
                        + phone.get_phone_dn(),
                        text_color=DEFAULT_TEXT_COLOR,
                    )
                    window.refresh()
                    get_screenshot = asyncio.create_task(
                        update_screenshot(phone, window["-SCREENSHOT-"])
                    )

    finally:
        if "phone" in locals():
            if phone is not None:
                phone.close()
        temp_dir: Path = Path().cwd() / "tmp"
        for pic_path in temp_dir.glob("**/*"):
            pic_path.unlink()
