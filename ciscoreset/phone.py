from ciscoreset.axl import CUCM
from ciscoreset.credentials import get_credentials
from ciscoreset.xml import XMLPhone
from ciscoreset.vision import get_list_position, get_menu_position
from bs4 import BeautifulSoup
import requests
import re
from time import sleep
from pathlib import Path
from icecream import ic

SUPPORTED_PHONE_MODELS = [
    "8811",
    "8841",
    "8845",
    "8851",
    "8851NR",
    "8861",
    "8865",
    "8865NR",
]


RESET_CONFIRM_BUTTON: dict = {
    dev: "Soft3"
    for dev in [
        "8811",
        "8841",
        "8845",
        "8851",
        "8851NR",
        "8861",
        "8865",
        "8865NR",
        "8832",
    ]
}


class PhoneConnection:
    def __init__(self, phone_ip: str, verbose=False) -> None:
        if not verbose:
            ic.disable()
        self.verbose = verbose

        self.username, self.password = get_credentials()
        self.device_ip = phone_ip
        self.ucm: CUCM = CUCM(self.username, self.password)

        # get device name from phone's web gui
        recv = BeautifulSoup(
            requests.get("http://" + self.device_ip).text, "html.parser"
        ).find(string=re.compile(r"^(SEP\w{12})"))
        if recv is None:
            raise Exception(f"Cannot get device name at {self.device_ip}")
        else:
            self.device_name = str(recv)

        # get device model to set up XML
        self.device_model = self.ucm.get_phone_model(self.device_name)
        if self.device_model not in SUPPORTED_PHONE_MODELS:
            raise Exception(
                f"Sorry, Cisco {self.device_model} is not yet supported by this program."
            )

        self.xml: XMLPhone = XMLPhone(
            phone_ip, self.username, self.password, self.device_model
        )

        # add device to user's controlled devices, unless already there
        self.admin_devices = self.ucm.get_user_devices(self.username)
        if self.device_name not in self.admin_devices:
            self.ucm.update_user_devices(
                self.username, self.admin_devices + [self.device_name]
            )
            self.cleanup = True
        else:
            self.cleanup = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self.cleanup:
            print("Removing used device from admin profile...")
            self.ucm.update_user_devices(self.username, self.admin_devices)

    def _screenshot(self, append="", full_name="") -> str:
        safe_ip_str = self.device_ip.replace(".", "-")
        if append:
            if not append.startswith("-"):
                safe_ip_str += "-" + append
            else:
                safe_ip_str += append
        elif full_name:
            safe_ip_str = full_name
        return self.xml.download_screenshot(filepath=f"tmp/{safe_ip_str}.bmp")

    def _wait_until_reachable(self) -> None:
        while True:
            try:
                # print("trying...")
                resp = requests.get(
                    f"http://{self.device_ip}/CGI/Screenshot",
                    auth=requests.auth.HTTPBasicAuth(self.username, self.password),
                )
            except requests.exceptions.ConnectionError:
                sleep(1)
                continue
            else:
                return None

    def __find_pos(self, item: str, f) -> int:
        if self.verbose:
            screenshot = self._screenshot(append=item.lower().replace(" ", "-"))
        else:
            screenshot = self._screenshot()
        pos = f(item, self.device_model, screenshot)
        if pos == -1:
            raise Exception(f"Cannot find {item}")
        return pos

    def _find_menu_pos(self, menu_item: str) -> int:
        return self.__find_pos(menu_item, get_menu_position)

    def _find_list_pos(self, list_item: str) -> int:
        return self.__find_pos(list_item, get_list_position)

    def _goto_menu_item(self, menu_item: str) -> None:
        self.xml.send_key(f"KeyPad{self._find_menu_pos(menu_item)}")

    def _goto_list_item(self, list_item: str) -> None:
        self.xml.send_key(f"KeyPad{self._find_list_pos(list_item)}")

    def _to_home(self) -> None:
        print("Navigating back to home menu... ", end="", flush=True)
        self.xml.send_keys(["NavBack"] * 6)
        if self.verbose:
            self._screenshot("-home")
        print("done")

    def _to_applications(self, menu="") -> None:
        self._to_home()
        print("Opening applications... ", end="", flush=True)
        self.xml.send_key("Applications")
        if self.verbose:
            self._screenshot("-applications")
        print("done")
        if menu:
            print(f"Navigating to {menu} menu... ", end="", flush=True)
            self._goto_menu_item(menu)
            # if self.verbose:
            #     self._screenshot(f"-{menu}-menu")
            print("done")

    def _to_admin_settings_menu(self) -> None:
        self._to_applications()
        print("Opening admin settings menu... ", end="", flush=True)
        if self.verbose:
            print("")

        self.xml.send_key(f"KeyPad{self._find_menu_pos('Admin Settings')}")
        # if self.verbose:
        #     self._screenshot("-admin-settings")
        print("done")

    def _to_reset_settings_menu(self) -> None:
        self._to_admin_settings_menu()
        print("Opening reset menu... ", end="", flush=True)
        if self.verbose:
            print("")

        self.xml.send_key(f"KeyPad{self._find_list_pos('Reset Settings')}")
        if self.verbose:
            self._screenshot("-reset-settings")
        print("done")

    def send_reset(self, reset_type: str, dry_run=False) -> None:
        reset_commands = {
            "device": "Reset Device",
            "settings": "All Settings",
            "network": "Network Settings",
            "service": "Service Mode",
            "service mode": "Service Mode",
            "security": "Security Settings",
        }
        if reset_type not in reset_commands:
            raise Exception(f"{reset_type} is not a valid reset type")

        self._to_reset_settings_menu()

        print(f"Sending {reset_type.title()} reset... ", end="", flush=True)
        self._goto_list_item(reset_commands[reset_type])
        # if self.verbose:
        # self._screenshot("-reset-select")

        if dry_run:
            print("dry-run complete")
            sleep(1)
            self._to_home()
        else:
            self.xml.send_key(RESET_CONFIRM_BUTTON[self.device_model])
            print("done")
            if reset_type in ["security"]:
                self._to_home()
                if self.verbose:
                    self._screenshot("-finished-home")
            elif reset_type == "network":
                self._wait_until_reachable()

    def interactive_mode(self) -> None:
        self.verbose = False
        print("Enter commands, either one at a time, or separated by commas.")
        print(f"Make sure to be viewing {self._screenshot()} at the same time.")
        print("([enter] a blank line to exit)\n")

        def send_cmds(cmds):
            if cmds:
                self.xml.send_keys(cmds)
            self._screenshot()

        def set_font(fontsize: str) -> str:
            sizes: dict = {
                "1": "tiny",
                "2": "small",
                "3": "regular",
                "4": "large",
                "5": "huge",
            }
            if fontsize not in sizes:
                print(f"Invalid font size of {fontsize}")
                return "invalid"
            else:
                self._to_applications()
                self._goto_menu_item("Settings")
                print(f"Setting font size to {sizes[fontsize]}... ", end="", flush=True)
                self.xml.send_keys(["KeyPad5", f"KeyPad{fontsize}", "Soft2"])
                self._screenshot()
                print("done")
                return sizes[fontsize]

        while (input_keys := input("-> ")) != "":
            cmds: list[str] = replace_key_shortcuts(
                input_keys.replace(",", " ").replace("  ", " ").split(" ")
            )
            if cmds == ["screenshot"]:
                self._screenshot()
            elif "goHome" in cmds:
                cmds.remove("goHome")
                self._to_home()
                send_cmds(cmds)
            elif "goApps" in cmds:
                cmds.remove("goApps")
                self._to_applications()
                send_cmds(cmds)
            elif "goAdmin" in cmds:
                cmds.remove("goAdmin")
                self._to_admin_settings_menu()
                send_cmds(cmds)
            elif "goReset" in cmds:
                cmds.remove("goReset")
                self._to_reset_settings_menu()
                send_cmds(cmds)
            elif cmds[0].startswith("setFont"):
                set_font(cmds[0][-1])
            elif cmds == ["getFontScreenshots"]:
                for size in ["1", "2", "3", "4", "5"]:
                    size_name = set_font(size)
                    self._to_applications("Admin Settings")
                    self._screenshot(full_name=f"admin_{size_name}")
                    self.xml.send_key("KeyPad5")
                    self._screenshot(full_name=f"reset_{size_name}")
                    print(f"({size_name} screenshots complete!)\n")
            elif cmds:
                send_cmds(cmds)


def replace_key_shortcuts(key_list: list[str]) -> list[str]:
    shortcuts: dict = {
        "down": "NavDwn",
        "up": "NavUp",
        "left": "NavLeft",
        "right": "NavRight",
        "select": "NavSelect",
        "back": "NavBack",
        "apps": "Applications",
    }

    correct_list: list[str] = []
    for key in key_list:
        if key in shortcuts:
            correct_list.append(shortcuts[key])
        elif key.isnumeric() and len(key) == 1:
            correct_list.append(f"KeyPad{key}")
        else:
            correct_list.append(key)
    return correct_list
