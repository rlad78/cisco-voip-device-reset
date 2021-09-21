from ciscoreset.utils import image_to_base64, make_dpi_aware, should_exit
from ciscoreset.gui_popups import popup_get_login_details, popup_not_supported
from ciscoreset.gui_bgtasks import BGTasks
from ciscoreset import __version__, PhoneConnection
from ciscoreset.configs import ROOT_DIR
from ciscoreset.keys import KEY_SUPPORT
from PySimpleGUI.PySimpleGUI import DEFAULT_TEXT_COLOR
import PySimpleGUI as sg
from PIL import UnidentifiedImageError
from pathlib import Path
from concurrent.futures import Future
import re


GUI_SUPPORTED_PHONES = (
    "8811",
    "8841",
    "8845",
    "8851",
    "8851NR",
    "8861",
    "8865",
    "8865NR",
)


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
            sg.Button("Refresh"),
        ],
        [sg.Text("", key="-INFO-")],
        [sg.Text("", key="-STATUS-")],
        [sg.Text("", key="-DL_STATUS-", text_color="orange")],
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
        [
            sg.Button("Soft Reset", key="resetDevice"),
            sg.Button("Device Settings", key="resetSettings"),
        ],
        [
            sg.Button("Network", key="resetNetwork"),
            sg.Button("Service Mode", key="resetService"),
            sg.Button("Security", key="resetSecurity"),
        ],
    ]


def create_navigation_menu() -> list:
    soft_keys = [
        [
            sg.Button(
                "        ",
                key=f"Soft{n}",
                tooltip=f"Softkey {n}",
                button_color=("white", "black"),
                pad=(10, 0),
                metadata="nav",
            )
            for n in range(1, 5, 1)
        ]
    ]

    directional_buttons = [
        [
            sg.Button(
                "↑",
                key="NavUp",
                tooltip="Up",
                button_color=("white", "black"),
                metadata="nav",
            )
        ],
        [
            sg.Button(
                "←",
                key="NavLeft",
                tooltip="Left",
                button_color=("white", "black"),
                metadata="nav",
            ),
            sg.Button(
                "o",
                key="NavSelect",
                tooltip="Select",
                button_color=("black", "silver"),
                metadata="nav",
            ),
            sg.Button(
                "→",
                key="NavRight",
                tooltip="Right",
                button_color=("white", "black"),
                metadata="nav",
            ),
        ],
        [
            sg.Button(
                "↓",
                key="NavDwn",
                tooltip="Down",
                button_color=("white", "black"),
                metadata="nav",
            ),
        ],
    ]

    def dial_factory(num_string: str) -> list[sg.Button]:
        def digit(n) -> str:
            if n.isnumeric():
                return n
            elif n == "*":
                return "Star"
            elif n == "#":
                return "Pound"
            else:
                raise Exception(f"dial factory: digit issue with {n}")

        return [
            sg.Button(
                c,
                key=f"KeyPad{digit(c)}",
                tooltip=f"KeyPad{digit(c)}",
                button_color=("white", "black"),
                metadata="nav",
            )
            for c in num_string
        ]

    dial_pad = [dial_factory(chars) for chars in ["123", "456", "789", "*0#"]]

    left_pane = [
        [
            sg.Button(
                "Voicemail",
                key="Messages",
                tooltip="Voicemail",
                button_color=("white", "black"),
                metadata="nav",
            )
        ],
        [
            sg.Button(
                "Settings",
                key="Applications",
                tooltip="Settings",
                button_color=("white", "black"),
                metadata="nav",
            ),
            sg.Button(
                "Directory",
                key="Directories",
                tooltip="Directory",
                button_color=("white", "black"),
                metadata="nav",
            ),
        ],
        [
            sg.Button(
                " +           ",
                key="VolUp",
                tooltip="Volume Up",
                button_color=("white", "black"),
                pad=((0, 0), (20, 0)),
                metadata="nav",
            ),
            sg.Button(
                "           - ",
                key="VolDwn",
                tooltip="Volume Down",
                button_color=("white", "black"),
                pad=((0, 0), (20, 0)),
                metadata="nav",
            ),
        ],
    ]

    right_pane = [
        [
            sg.Button(
                "Hold",
                key="Hold",
                tooltip="Hold",
                button_color=("white", "black"),
                metadata="nav",
            )
        ],
        [
            sg.Button(
                "Transfer",
                key="FixedFeature1",
                tooltip="Transfer",
                button_color=("white", "black"),
                metadata="nav",
            ),
            sg.Button(
                "Conference",
                key="FixedFeature2",
                tooltip="Conference",
                button_color=("white", "black"),
                metadata="nav",
            ),
        ],
        [
            sg.Button(
                "Headset",
                key="Headset",
                tooltip="Headset",
                button_color=("white", "black"),
                pad=((0, 0), (20, 0)),
                metadata="nav",
            ),
            sg.Button(
                "Speaker",
                key="Speaker",
                tooltip="Speaker",
                button_color=("white", "black"),
                pad=((0, 0), (20, 0)),
                metadata="nav",
            ),
        ],
        [
            sg.Button(
                "Mute",
                key="Mute",
                tooltip="Mute",
                button_color=("white", "black"),
                metadata="nav",
            )
        ],
    ]

    return [
        [
            sg.Column(
                soft_keys,
                element_justification="c",
                vertical_alignment="center",
                pad=((0, 0), (0, 10)),
            )
        ],
        [
            sg.Button(
                "⤺",
                key="NavBack",
                tooltip="Back",
                button_color=("white", "black"),
                metadata="nav",
            ),
            sg.Column(
                directional_buttons,
                pad=(20, 0),
                element_justification="c",
                vertical_alignment="center",
            ),
            sg.Button(
                "END",
                key="Release",
                tooltip="Hang Up",
                button_color=("red", "black"),
                metadata="nav",
            ),
        ],
        [
            sg.Column(
                left_pane,
                pad=(0, 5),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
            ),
            sg.Column(
                dial_pad,
                pad=(15, 5),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
            ),
            sg.Column(
                right_pane,
                pad=(0, 5),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
            ),
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

    return sg.Window(f"Cisco VoIP Device Reset", layout)


def run() -> None:
    make_dpi_aware()

    url, port, username, password = popup_get_login_details()
    if not url:
        return None

    window: sg.Window = main_window_blueprint()
    phone: PhoneConnection = None
    bg: BGTasks = BGTasks(window)

    def reload_screenshot(scr_path="", dl_msg=True) -> None:
        if scr_path:
            window["-SCREENSHOT-"].update(image_to_base64(scr_path, (400, 240)))
        else:
            window["-SCREENSHOT-"].update()

        if dl_msg:
            window["-DL_STATUS-"].update("Updating screenshot")
        else:
            window["-DL_STATUS-"].update("")

        window.refresh()

    def clear_tmp_dir() -> None:
        temp_dir: Path = ROOT_DIR / "tmp"
        for pic_path in temp_dir.glob("**/*"):
            pic_path.unlink()

    def gen_button_list(model: str) -> list[str]:
        s_list = KEY_SUPPORT[model]["standard"]
        n_list = []

        for n_set in KEY_SUPPORT[model]["numeric"]:
            parts = n_set.split("-")
            start = int(parts[0][-1])
            stop = int(parts[-1])
            name = parts[0][:-1]
            for i in range(start, stop + 1, 1):
                n_list.append(f"{name}{i}")

        return s_list + n_list

    def disable_unsupported_buttons(buttons: list[str], w: sg.Window):
        for key, element in w.AllKeysDict.items():
            if element.metadata == "n/a" and key in buttons:
                # element.update(disabled=False)
                element.metadata = "nav"
            elif (
                type(element) == sg.Button
                and element.metadata == "nav"
                and key not in buttons
            ):
                element.update(disabled=True)
                element.metadata = "n/a"

    def disable_resets(enable=False):
        for key, element in window.AllKeysDict.items():
            if type(element) == sg.Button and key.startswith("reset"):
                if enable:
                    element.metadata = ""
                    # element.update(disabled=False)
                else:
                    element.metadata = "no reset"
                    element.update(disabled=True)

    refresh_screenshot = False
    dl_fut: Future = None
    dl_path: str = ""
    r_ip = re.compile(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$")

    button_list: list[str] = []

    try:
        while True:
            if refresh_screenshot:
                if dl_fut.done():
                    reload_screenshot(dl_path, dl_msg=False)
                    refresh_screenshot = False
                    dl_fut = None
                elif Path(dl_path).is_file():
                    try:
                        reload_screenshot(dl_path)
                    except UnidentifiedImageError:
                        pass

            event, values = window.read(timeout=10)

            if should_exit(event):
                break

            if event == "Refresh" and phone is not None:
                bg.disable_buttons()
                bg.update_screenshot(phone)
                window["-DL_STATUS-"].update("Updating screenshot")
                window.refresh()

            elif event == "Connect":
                if not r_ip.match(values["-IP-"]):
                    window["-STATUS-"].update(
                        "Please enter an IP address", text_color="orange"
                    )
                    continue

                window["-INFO-"].update("", text_color=DEFAULT_TEXT_COLOR)
                window["-STATUS-"].update(
                    "Connecting...", text_color=DEFAULT_TEXT_COLOR
                )
                bg.disable_buttons()
                window.refresh()
                try:
                    phone = None
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
                    bg.disable_buttons(enable=True)
                else:
                    if phone.device_model not in GUI_SUPPORTED_PHONES:
                        if not popup_not_supported(phone.device_model):
                            phone = None
                            window["-STATUS-"].update("", text_color=DEFAULT_TEXT_COLOR)
                            bg.disable_buttons(enable=True)
                            window.refresh()
                            continue
                        else:
                            disable_resets()
                    else:
                        disable_resets(enable=True)

                    reload_screenshot()
                    clear_tmp_dir()

                    window["-INFO-"].update(
                        f"Cisco {phone.device_model}"
                        + "\n"
                        + phone.device_name
                        + "\n"
                        + phone.get_phone_desc()
                        + "\n"
                        + phone.get_phone_dn(),
                        text_color=DEFAULT_TEXT_COLOR,
                    )
                    window["-STATUS-"].update("", text_color=DEFAULT_TEXT_COLOR)
                    window.refresh()

                    button_list = gen_button_list(phone.device_model)
                    disable_unsupported_buttons(button_list, window)
                    dl_fut: Future = bg.update_screenshot(phone)
                    dl_path = str(
                        ROOT_DIR / "tmp" / (phone.device_ip.replace(".", "-") + ".bmp")
                    )

            elif phone is not None and event in button_list:
                print("button pressed")
                bg.disable_buttons()
                reload_screenshot()
                bg_fut = bg.send_key(phone, event)
                dl_fut = bg.update_screenshot(phone)

            elif phone and event.startswith("reset"):
                print("reset pressed")
                bg.disable_buttons()
                reload_screenshot(dl_msg=False)
                window["-STATUS-"].update(
                    f"Sending {event.removeprefix('reset')} reset...", text_color="blue"
                )
                dl_fut = bg.send_reset(phone, event.removeprefix("reset"))
                refresh_screenshot = True

    finally:
        if "phone" in locals():
            if phone is not None:
                phone.close()
        temp_dir: Path = ROOT_DIR / "tmp"
        for pic_path in temp_dir.glob("**/*"):
            pic_path.unlink()
