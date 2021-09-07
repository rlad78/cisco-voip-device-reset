from ciscoreset.axl import CUCM
from ciscoreset.credentials import get_credentials
from ciscoreset.xml import XMLPhone
from ciscoreset.vision import get_list_position, get_menu_position
from bs4 import BeautifulSoup
import requests
import re
from time import sleep
from pathlib import Path
import subprocess

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
    def __init__(self, phone_ip: str) -> None:
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

    def _screenshot(self) -> str:
        safe_ip_str = self.device_ip.replace(".", "-")
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
        pos = f(item, self.device_model, self._screenshot())
        if pos == -1:
            raise Exception(f"Cannot find {item}")
        else:
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
        print("done")

    def _to_settings(self) -> None:
        self._to_home()
        print("Opening settings menu... ", end="", flush=True)
        self.xml.send_key("Applications")
        print("done")

    def _to_admin_settings_menu(self) -> None:
        self._to_settings()
        print("Opening admin settings menu... ", end="", flush=True)

        # admin_settings_pos = get_menu_position(
        #     "Admin Settings", self.device_model, self._screenshot()
        # )
        # if admin_settings_pos == -1:
        #     raise Exception("Cannot find Admin Settings menu")

        # go to admin menu
        self.xml.send_key(f"KeyPad{self._find_menu_pos('Admin Settings')}")
        print("done")

    def _to_reset_settings_menu(self) -> None:
        self._to_admin_settings_menu()
        print("Opening reset menu... ", end="", flush=True)

        # reset_settings_pos = get_list_position(
        #     "Reset Settings", self.device_model, self._screenshot()
        # )
        # if reset_settings_pos == -1:
        #     raise Exception("Cannot find Reset Settings menu")

        # go to reset menu
        self.xml.send_key(f"KeyPad{self._find_list_pos('Reset Settings')}")
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
        if dry_run:
            sleep(3)
            self._to_home()
        else:
            self.xml.send_key(RESET_CONFIRM_BUTTON[self.device_model])
            if reset_type in ["security"]:
                self._to_home()
            elif reset_type == "network":
                self._wait_until_reachable()
        print("done")
