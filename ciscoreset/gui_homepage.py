import PySimpleGUI as sg
from ciscoreset.utils import image_to_base64
from ciscoreset.gui_popups import popup_get_password, popup_get_username
from ciscoreset import __version__, PhoneConnection
from icecream import ic


def create_title() -> list:
    title = sg.Text("Cisco VoIP Device Reset", font="Any 20")
    version = sg.Text(__version__, font="Any 10")
    return [[title, version]]


def create_ip_entry() -> list:
    return [
        [sg.Text("IP Address of device:")],
        [sg.In("", size=(18, 1), key="-IP-"), sg.Button("Connect")],
        [sg.Text("", key="-STATUS-")],
    ]


def create_screenshot_viewer() -> list:
    return [
        [
            sg.Image(
                image_to_base64("tmp/screenshot.bmp", (400, 240)),
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


def draw_main_window() -> sg.Window:
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
            # sg.Column(
            #     [[sg.Text("Waiting for phone connection...", text_color="blue")]],
            #     justification="center",
            #     element_justification="center",
            #     vertical_alignment="center",
            #     key="-MENU_PLACEHOLDER-",
            #     pad=(0, 100),
            # ),
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


def run() -> None:
    if not (username := popup_get_username()):
        raise Exception("No username provided")
    if not (password := popup_get_password()):
        raise Exception("No password provided")

    window = draw_main_window()
    phone = None
    try:
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "Exit"):
                break
            if event == sg.WIN_CLOSED or event == "Exit":
                break
            if event == "Connect":
                window["-STATUS-"].update("Connecting...")
                window.refresh()
                phone = PhoneConnection(
                    values["-IP-"], username=username, password=password
                )
                window["-STATUS-"].update(
                    f"Cisco {phone.device_model}"
                    + "\n"
                    + phone.device_name
                    + "\n"
                    + phone.get_phone_desc()
                    + "\n"
                    + phone.get_phone_dn()
                )
    finally:
        if phone is not None:
            phone.close()

    # window["-RESET_MENU-"].update(visible=True)
    # window["-NAV_MENU-"].update(visible=True)
    # window["-MENU_PLACEHOLDER-"].update(visible=False)
