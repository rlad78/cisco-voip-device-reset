import PySimpleGUI as pg
from ciscoreset import get_credentials


def popup_get_username() -> str:
    result = pg.popup_get_text(
        "Please enter your CUCM username", title="Enter your username"
    )
    if result is None:
        return ""
    else:
        return result


def popup_get_password() -> str:
    result = pg.popup_get_text(
        "Enter your password", title="Enter password", password_char="*"
    )
    if result is None:
        return ""
    else:
        return result
