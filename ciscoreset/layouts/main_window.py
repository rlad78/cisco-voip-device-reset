import PySimpleGUI as sg
from ciscoreset.layouts import *
from ciscoreset.configs import TOOL_VERSION


def create_title() -> list:
    title = sg.Text("Cisco VoIP Device Reset", font="Any 20")
    version = sg.Text(TOOL_VERSION, font="Any 10")
    return [[title, version]]


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
