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
from ciscoreset.utils import should_exit
from ciscoreset.configs import ROOT_DIR
from pathlib import Path


def popup_get_login_details() -> Tuple[str, int, str, str]:
    def manage_server_save(remember: bool, server: str, svr_port: str) -> None:
        save_file: Path = ROOT_DIR / "user" / "cucm.txt"
        if not save_file.parent.exists():
            save_file.parent.mkdir(parents=True)

        if remember:
            save_file.write_text(f"{server}|{svr_port}")
        else:
            save_file.unlink()

    saved_server_file: Path = ROOT_DIR / "user" / "cucm.txt"
    saved_server = ""
    saved_port = "8443"
    saved = False
    if saved_server_file.is_file():
        saved = True
        try:
            saved_server, saved_port = saved_server_file.read_text().split("|")
        except ValueError:
            saved_server = ""
            saved_port = ""
            saved = False

    layout = [
        [sg.Text("Please enter your CUCM URL")],
        [
            sg.In(saved_server, key="-UCM-", size=(35, 1)),
            sg.Text("Port", pad=((5, 0), (0, 0))),
            sg.In(saved_port, size=(5, 1), key="-PORT-"),
        ],
        [sg.Text("", key="-STATUS-")],
        [
            sg.Button("Enter", bind_return_key=True),
            sg.Button("Cancel"),
            sg.Checkbox("Remember URL", key="remember", default=saved),
        ],
    ]
    window = sg.Window("Enter CUCM Server", layout)

    while True:
        event, values = window.read()
        if should_exit(event, "Cancel"):
            window.close()
            return "", 0, "", ""
        if event == "Enter":
            window["-STATUS-"].update("Connecting...", text_color=DEFAULT_TEXT_COLOR)
            window.refresh()

            url, port = (values["-UCM-"], values["-PORT-"])
            if err_resp := validate_ucm_server(url, port):
                window["-STATUS-"].update(err_resp, text_color="orange")
                continue  # just here for visual purposes
            else:
                base_url = get_base_url(url)
                creds: tuple = get_credentials(enable_manual_entry=False)
                if all(creds):
                    window["-STATUS-"].update(
                        "Attempting to use stored credentials to log in...",
                        text_color=DEFAULT_TEXT_COLOR,
                    )
                    window.refresh()
                if all(creds) and validate_axl_auth(base_url, port, *creds):
                    window.close()
                    manage_server_save(values["remember"], url, port)
                    return base_url, port, *creds
                else:
                    window.close()
                    creds = popup_get_credentials(base_url, port)
                    if creds == ("back", "back"):
                        return popup_get_login_details()
                    elif not any(creds):
                        return "", 0, *creds
                    else:
                        manage_server_save(values["remember"], url, port)
                        return base_url, port, *creds


def popup_get_credentials(ucm_url: str, port: int) -> Tuple[str, str]:
    creds: tuple = get_credentials(enable_manual_entry=False)
    is_auth: bool = validate_axl_auth(
        ucm_url, port, *creds
    )  # ! will return False if part of creds is not there

    if not is_auth:
        # make_dpi_aware()
        layout = [
            [sg.Text("Please enter your CUCM credentials", pad=((0, 10), (0, 5)))],
            [
                sg.Text("Username:", pad=((0, 10), (0, 0)), size=10),
                sg.In(key="-USERNAME-"),
            ],
            [
                sg.Text("Password:", pad=((0, 10), (0, 0)), size=10),
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


def popup_not_supported(device_type: str) -> bool:
    prompt = (
        f"Cisco {device_type}'s are not fully supported by this program. "
        + "You will not be able to run reset commands on this phone, but "
        + "you can still operate it using the navigation buttons provided.\n\n"
        + "Do you wish to continue connecting to this phone?"
    )

    return (
        True
        if sg.PopupYesNo(prompt, title="Unsupported Device", modal=True) == "Yes"
        else False
    )
