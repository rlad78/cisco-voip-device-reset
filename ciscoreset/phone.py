from ciscoreset.axl import CUCM
from ciscoreset.credentials import get_credentials
from ciscoreset.xml import XMLPhone
from ciscoreset.vision import get_menu_position
from bs4 import BeautifulSoup
import requests
import re


class PhoneConnection:
    def __init__(self, phone_ip: str) -> None:
        self.username, self.password = get_credentials()
        self.device_ip = phone_ip
        self.ucm: CUCM = CUCM(self.username, self.password)

        # get device name from phone's web gui
        recv = BeautifulSoup(
            requests.get("http://" + self.ip).text, "html.parser"
        ).find(string=re.compile(r"^(SEP\w{12})"))
        if recv is None:
            raise Exception(f"Cannot get device name at {self.ip}")
        else:
            self.device_name = str(recv)

        # get device model to set up XML
        self.device_model = self.ucm.get_phone_model(self.device_name)
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self.cleanup:
            print("Removing used device from admin profile...")
            self.ucm.update_user_devices(self.username, self.admin_devices)
