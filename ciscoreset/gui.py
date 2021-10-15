from ciscoreset import PhoneConnection
from ciscoreset.configs import ROOT_DIR
from ciscoreset.gui_popups import popup_get_login_details, popup_not_supported
from ciscoreset.gui_bgtasks import BGTasks
from ciscoreset.keys import KEY_SUPPORT
from ciscoreset.layouts import main_window_blueprint, image_to_base64, should_exit
from ciscoreset.exceptions import *
from PySimpleGUI.PySimpleGUI import DEFAULT_TEXT_COLOR
import PySimpleGUI as sg
from PIL import UnidentifiedImageError
from pathlib import Path
from concurrent.futures import Future
import re
import traceback


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


def run() -> None:
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
                        values["-IP-"],
                        url,
                        port=port,
                        username=username,
                        password=password,
                    )
                except (PhoneConnectException, UnsupportedDeviceError) as e:
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

    except Exception as e:
        tb = traceback.format_exc()
        sg.popup_scrolled(f"An error happened.  Here is the info:\n{e}\n{tb}")
    finally:
        if "phone" in locals():
            if phone is not None:
                phone.close()
        temp_dir: Path = ROOT_DIR / "tmp"
        for pic_path in temp_dir.glob("**/*"):
            pic_path.unlink()


if __name__ == "__main__":
    run()
