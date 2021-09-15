from typing import Tuple
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import DEFAULT_TEXT_COLOR
from ciscoreset.credentials import (
    get_base_url,
    get_credentials,
    write_credentials,
    validate_ucm_server,
    validate_axl_auth,
)
from ciscoreset.utils import make_dpi_aware, should_exit


def popup_get_ucm_server() -> Tuple[str, int]:
    # make_dpi_aware()
    layout = [
        [sg.Text("Please enter your CUCM url")],
        [
            sg.In(key="-UCM-", size=(35, 1)),
            sg.Text("Port", pad=((5, 0), (0, 0))),
            sg.In("8443", size=(5, 1), key="-PORT-"),
        ],
        [sg.Text("", key="-STATUS-")],
        [sg.Button("Enter", bind_return_key=True), sg.Button("Cancel")],
    ]
    window = sg.Window("Enter CUCM Server", layout)

    while True:
        event, values = window.read()
        if should_exit(event, "Cancel"):
            window.close()
            return "", 0
        if event == "Enter":
            window["-STATUS-"].update("Connecting...", text_color=DEFAULT_TEXT_COLOR)
            window.refresh()

            url, port = (values["-UCM-"], values["-PORT-"])
            if err_resp := validate_ucm_server(url, port):
                window["-STATUS-"].update(err_resp, text_color="orange")
                continue  # just here for visual purposes
            else:
                window.close()
                return get_base_url(url), port


def popup_get_credentials(ucm_url: str, port: int) -> Tuple[str, str]:
    creds: tuple = get_credentials(enable_manual_entry=False)
    is_auth: bool = validate_axl_auth(
        ucm_url, port, *creds
    )  # ! will return False if part of creds is not there

    if not is_auth:
        # make_dpi_aware()
        layout = [
            [sg.Text("Please enter your CUCM credentials", pad=((0, 10), (0, 5)))],
            [sg.Text("Username:", pad=((0, 10), (0, 0))), sg.In(key="-USERNAME-")],
            [
                sg.Text("Password:", pad=((0, 10), (0, 0))),
                sg.In(key="-PASSWORD-", password_char="*"),
            ],
            [sg.Text("", key="-RESPONSE-")],
            [
                sg.Button("Enter", bind_return_key=True),
                sg.Button("Back"),
                sg.Button("Cancel"),
                sg.Checkbox("Remember credentials", key="-REMEMBER-"),
            ],
        ]
        window = sg.Window("CUCM Credentials", layout)

        while True:
            event, values = window.read()
            if should_exit(event, "Cancel"):
                window.close()
                return "", ""
            if event == "Back":
                window.close()
                return "back", "back"
            if event == "Enter":
                username, password = (values["-USERNAME-"], values["-PASSWORD-"])
                window["-RESPONSE-"].update(
                    "Connecting...", text_color=DEFAULT_TEXT_COLOR
                )
                window.refresh()

                if validate_axl_auth(ucm_url, port, username, password):
                    window.close()
                    if values["-REMEMBER-"] == True:
                        write_credentials(username, password)
                    return username, password
                else:
                    window["-RESPONSE-"].update(
                        "Could not connect to AXL, please check your user permissions",
                        text_color="orange",
                    )

    else:
        return creds  # username, password


def popups_credentials_group() -> Tuple[str, int, str, str]:
    while True:
        url, port = popup_get_ucm_server()
        if url and port:
            username, password = popup_get_credentials(url, port)
            if username == "back" and password == "back":
                pass
            elif not username and not password:
                return "", 0, "", ""
            else:
                return url, port, username, password
        else:
            return "", 0, "", ""
