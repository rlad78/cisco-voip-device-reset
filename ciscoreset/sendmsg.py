import html
import sys
import os
import re
import getopt
import traceback
from html import escape

import requests
import requests.auth
import requests.adapters
from lxml import etree
from ciscoaxl import axl
from zeep.exceptions import Fault
from bs4 import BeautifulSoup
import argparse

from stdiomask import getpass
from cryptography.fernet import Fernet, InvalidToken
import json
import cv2
import pytesseract
from pathlib import Path
from typing import Tuple, Union
from time import sleep

# TODO: comments on all


class ProgramError(Exception):
    pass


class HTTPSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs["assert_hostname"] = False
        super().init_poolmanager(*args, **kwargs)


cgi_errors = {
    "1": "Error parsing CiscoIPPhone object",
    "2": "Error framing CiscoIPPhone object",
    "3": "Internal file error",
    "4": "Authentication error",
}


def cgi_execute(hostname, port, timeout, username, password, certificate, urls):
    xml = '<?xml version="1.0" encoding="UTF-8"?>' "<CiscoIPPhoneExecute>"

    for url, priority in urls:
        xml += (
            '<ExecuteItem URL="' + escape(url) + '" Priority="' + str(priority) + '" />'
        )

    xml += "</CiscoIPPhoneExecute>"

    if username != "":
        auth = requests.auth.HTTPBasicAuth(username, password)
    else:
        auth = None

    scheme = "https" if certificate else "http"

    try:
        session = requests.Session()
        session.mount("https://", HTTPSAdapter())

        response = session.post(
            f"{scheme}://{hostname}:{port}/CGI/Execute",
            timeout=timeout,
            auth=auth,
            verify=certificate,
            data={"XML": xml},
        )
        response.raise_for_status()

    except requests.RequestException as error:
        raise ProgramError(error)

    if response.headers["Content-Type"][0:8] != "text/xml":
        raise ProgramError(
            "Unexpected Content-Type: " + response.headers["Content-Type"]
        )

    try:
        document = etree.fromstring(response.content)
    except etree.XMLSyntaxError as error:
        raise ProgramError(error)

    if document.tag == "CiscoIPPhoneError":
        number = document.get("Number")

        raise ProgramError("Error: " + cgi_errors.get(number, f"{number}"))

    for element in document.findall("ResponseItem"):
        url = element.get("URL")
        data = element.get("Data", "")

        print(f"{url}: {data}")


def run(custom_args=""):
    try:
        short_options = "h:t:u:p:c:H"
        long_options = [
            "host=",
            "timeout=",
            "username=",
            "password=",
            "certificate=",
            "help",
        ]

        try:
            if not custom_args:
                options, arguments = getopt.gnu_getopt(
                    sys.argv[1:], short_options, long_options
                )
            else:
                options, arguments = getopt.gnu_getopt(
                    custom_args, short_options, long_options
                )
        except getopt.GetoptError as error:
            raise ProgramError(
                error.msg[0].upper()
                + error.msg[1:]
                + ". Try '"
                + os.path.basename(sys.argv[0])
                + " --help' for more information"
            )

        hostname = None
        port = None
        timeout = 10
        username = ""
        password = ""
        certificate = None
        help = False

        for option, argument in options:
            if option in ("-h", "--host"):
                hostname = argument

                if ":" in hostname:
                    hostname, port = hostname.rsplit(":", maxsplit=1)

                    try:
                        port = int(port)

                        if port < 1 or port > 65535:
                            raise ValueError

                    except ValueError:
                        raise ProgramError(f"Invalid port: {port}")

                if not re.search(
                    r"(?xi) ^ (?: [a-z0-9\-]+ \.)* [a-z0-9\-]+ $", hostname
                ):
                    raise ProgramError(f"Invalid host: {hostname}")

            elif option in ("-t", "--timeout"):
                timeout = argument

                try:
                    timeout = int(timeout)
                except ValueError:
                    raise ProgramError(f"Invalid timeout: {timeout}")

            elif option in ("-u", "--username"):
                username = argument

            elif option in ("-p", "--password"):
                password = argument

            elif option in ("-c", "--certificate"):
                certificate = argument

            elif option in ("-H", "--help"):
                help = True

        if help:
            print(
                "Usage: "
                + os.path.basename(sys.argv[0])
                + " [OPTIONS] URL[@PRIORITY]...\n"
                "Send CGI Execute URLs to a Cisco IP Phone.\n"
                "\n"
                "  -h, --host HOST[:PORT]         host name or IP address and port of the phone\n"
                "  -t, --timeout TIMEOUT          connection timeout in seconds (default 10)\n"
                "  -u, --username USERNAME        authentication username\n"
                "  -p, --password PASSWORD        authentication password\n"
                "  -c, --certificate CERT-FILE    connect using SSL and verify using certificate\n"
                "  -H, --help                     print this help and exit\n"
                "\n"
                "Up to 3 URLs may be specified.\n"
                "URL is one of Dial:, EditDial:, Key:, SoftKey:, Init:, Play:, Display:, http: or https:\n"
                "Optional PRIORITY is either 0 (immediately), 1 (when idle) or 2 (only if idle).\n"
            )

            return

        if not len(arguments):
            raise ProgramError("No URLs specified")

        urls = []

        for argument in arguments:
            url = argument

            if "@" in url:
                url, priority = argument.rsplit("@", maxsplit=1)

                try:
                    priority = int(priority)

                    if priority < 0 or priority > 2:
                        raise ValueError

                except ValueError:
                    raise ProgramError(f"Invalid priority: {priority}")
            else:
                priority = 0

            if not re.search(
                r"(?x) ^ (?: (?: Dial | EditDial) : [0-9#*]+"
                r" | (?: Key | SoftKey | Init) : [a-zA-Z0-9]+"
                r" | Play : [a-zA-Z0-9._\-]+"
                r" | Display : (?: Off | On | Default) (: [0-9]+)?"
                r" | https? :// [^ ]+) $",
                url,
            ):
                raise ProgramError(f"Invalid URL: {url}")

            if len(urls) == 3:
                raise ProgramError("A maximum of 3 URLs can be specified")

            urls.append((url, priority))

        if hostname is None:
            raise ProgramError("No host specified")

        if port is None:
            port = 443 if certificate else 80

        cgi_execute(hostname, port, timeout, username, password, certificate, urls)

    except ProgramError as error:
        print(str(error), file=sys.stderr)
        exit(1)

    except Exception:
        traceback.print_exc(file=sys.stderr)
        exit(1)

    # exit(0)


SUPPORTED_PHONE_MODELS = ["8845", "8865"]


class PhoneMessenger:
    def __init__(
        self, ip: str, model: str, username: str, password: str, axl_connection
    ) -> None:
        # generate arg pattern for this phone
        self.cleanup = False
        self.arg_pattern = "-h " + ip + " -u " + username + " -p " + password + " "
        if model not in SUPPORTED_PHONE_MODELS:
            raise Exception(
                "Sorry, " + model + " is not a supported model of Cisco phone."
            )
        else:
            self.model = model

        self.ip = ip
        self.model = model
        self.user = username
        self.password = password
        self.ucm: UCMConnection = axl_connection

        recv = BeautifulSoup(
            requests.get("http://" + self.ip).text, "html.parser"
        ).find(string=re.compile(r"^(SEP\w{12})"))
        if recv is None:
            raise Exception(f"Cannot get device name at {self.ip}")
        else:
            self.device_name = str(recv)

        self.admin_devices = self.ucm.get_user_devices(self.user)
        if self.device_name not in self.admin_devices:
            self.ucm.update_user_devices(
                self.user, self.admin_devices + [self.device_name]
            )
            self.cleanup = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self.cleanup:
            print("Removing used device from admin profile...")
            self.ucm.update_user_devices(self.user, self.admin_devices)

    def _dl_screenshot(self, savepath="") -> str:
        sleep(0.75)
        if not savepath:
            savepath = f"tmp/{self.ip}.bmp"
        elif savepath[-4:] != ".bmp":
            savepath += ".bmp"

        # err_code: int = os.system(
        #     f"mkdir -p tmp && wget --user={self.user} --password={self.password} http://{self.ip}/CGI/Screenshot -O {savepath}"
        # )
        # if err_code:
        #     raise Exception("Screenshot wget returned err code of " + str(err_code))

        p = Path(savepath)
        if not p.parent.exists():
            p.parent.mkdir(parents=True)

        with open(str(p), "wb") as target:
            resp = requests.get(
                f"http://{self.ip}/CGI/Screenshot",
                auth=requests.auth.HTTPBasicAuth(self.user, self.password),
            )

            if not resp.ok:
                raise Exception("Issue downloading screenshot: " + str(resp))

            for block in resp.iter_content(4096):
                if block:
                    target.write(block)

        if not p.is_file():
            raise FileNotFoundError(f'Could not find "{str(p)}"')

        return str(p)

    def save_screenshot(self, filepath="") -> None:
        if not filepath:
            filepath = "Screenshot_" + self.ip + ".bmp"

    def get_menu_position(self, item: str, grid: bool) -> Union[int, None]:
        screenshot = self._dl_screenshot()
        return int(regex_image(screenshot, r"(\d+)\W+" + item, grid))

    def send_commands(self, *args):
        to_run: list[list[str]] = [[]]
        for cmd in args:
            if len(to_run[-1]) == 3:
                to_run.append([cmd])
            else:
                to_run[-1].append(cmd)

        for payload in to_run:
            arg_list = (self.arg_pattern + " ".join(payload)).split(" ")
            # print(f"Running: {arg_list}")
            run(arg_list)

    def send_keys(self, *args):
        new_args = ["Key:" + a for a in args]
        self.send_commands(*new_args)

    def _8800_reset(self, reset_type: str):
        self.nav_home()
        self.send_keys("Applications")
        admin_key = self.get_menu_position("Admin", grid=True)
        # self.send_keys(f"KeyPad{admin_key}", "KeyPad5")
        self.send_keys(f"KeyPad{admin_key}")
        reset_key = self.get_menu_position("Reset", grid=False)
        self.send_keys(f"KeyPad{reset_key}")

        def hit_reset_number(reset_key: int):
            self.send_keys(f"KeyPad{reset_key}", "Soft3")

        if reset_type.lower() in ["security", "trust", "trust list"]:
            hit_reset_number(5)

        elif reset_type.lower() in ["factory", "device"]:
            hit_reset_number(1)

        elif reset_type.lower() in [
            "service",
            "campus",
            "off campus",
            "on campus",
            "network",
        ]:
            hit_reset_number(4)

        elif reset_type.lower() in [
            "settings",
            "options",
            "user settings",
            "user options",
        ]:
            hit_reset_number(2)

        else:
            raise KeyError(f'"{reset_type}" is not a valid reset_type')

    def _7800_reset(self, reset_type="factory") -> None:
        self.nav_home()
        self.send_keys("Settings")

    def reset(self, reset_type="factory") -> None:
        self.nav_home()
        if self.model in ["8841", "8845", "8865"]:
            self._8800_reset(reset_type)
            self.save_screenshot(f"tmp/{reset_type}_reset_complete.bmp")

    def nav_home(self) -> None:
        self.send_keys("NavBack", "NavBack", "NavBack")

    def interactive_mode(self, screenshot_path="") -> None:
        if not screenshot_path:
            screenshot_path = f"tmp/screenshot.bmp"
        print("Enter commands, either one at a time, or separated by commas.")
        print(f"Make sure to be viewing {screenshot_path} at the same time.")
        print("([enter] a blank line to exit)")
        self._dl_screenshot(screenshot_path)
        while input_keys := input("-> "):
            cmds: list[str] = input_keys.replace(",", " ").replace("  ", " ").split(" ")
            cmd_batch: list[str] = []
            for cmd in cmds:
                cmd_batch.append(cmd)
                if len(cmd_batch) == 3:
                    self.send_keys(*cmd_batch)
                    cmd_batch = []
            if cmd_batch:
                self.send_keys(*cmd_batch)
            self._dl_screenshot(screenshot_path)


def regex_image(
    image_path: str, regex: str, grid=True, return_with="str"
) -> Union[str, list]:
    p = Path(image_path)
    if not p.is_file():
        raise FileNotFoundError(f"Could not find {image_path}")

    _, bw_img = cv2.threshold(
        cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2GRAY),
        171,
        255,
        cv2.THRESH_OTSU,
    )
    image_text = pytesseract.image_to_string(
        bw_img,
        config=r"--psm 4" if grid else r"--psm 6",
    )

    search = re.findall(regex, image_text, re.I | re.M)
    if not search:
        raise Exception(
            "Could not match " + repr(regex).replace("\\\\", "\\") + " to " + image_path
        )
    elif return_with == "str":
        return search[0]
    elif return_with == "list":
        return search
    else:
        raise ValueError('return_with must be either "str" or "list"')


class UCMConnection(axl):
    def __init__(self, username, password):
        cucm = "ucm-01.clemson.edu"
        cucm_version = "11.5"
        super().__init__(username, password, cucm, cucm_version)

    def get_user_devices(self, userid: str) -> list:
        dev_list = self.get_user(userid).associatedDevices.device
        if dev_list is Fault:
            raise Exception(f"Could not get user devices from user {userid}")
        return dev_list

    def update_user_devices(self, userid: str, devices: list) -> None:
        result = self.update_user(
            userid=userid,
            associatedDevices={"device": devices},
        )
        if result is Fault:
            raise Exception(
                f"Could not update user devices from user {userid}:\n{devices}"
            )


def get_credentials() -> Tuple[str, str]:
    key_loc = Path().cwd().parent / "ciscoxml_passkey"
    stored = Path("pass.log")

    if stored.is_file() and key_loc.is_file():
        try:
            with key_loc.open("rb") as k:
                fernet = Fernet(k.read())
            with stored.open("rb") as f:
                d = json.loads(fernet.decrypt(f.read()).decode())
            print("Using stored encrypted passwords from", str(stored.resolve()), "\n")
        except InvalidToken:
            key_loc.unlink()
            stored.unlink()
            return get_credentials()
    else:
        d: dict = {
            "user": input("CUCM username: "),
            "pass": getpass(prompt="CUCM password: "),
            # "tacacs": getpass(prompt="TACACS Password: "),
            # "bang": getpass(prompt='"bang" Password: '),
        }
        key = Fernet.generate_key()
        fernet = Fernet(key)
        with stored.open("wb") as f:
            f.write(fernet.encrypt(json.dumps(d).encode()))
        with key_loc.open("wb") as k:
            k.write(key)
        print("Writing ENCRYPTED passwords to", str(stored.resolve()))
    return d["user"], d["pass"]


def reset_user_interface() -> None:
    test7841 = "10.12.4.118"
    my8865 = "10.12.4.231"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ip",
        # nargs=1,
        type=str,
        help="the ip address of the phone you are trying to reach",
    )
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="manually control the phone"
    )
    parser.add_argument(
        "-r",
        "--reset",
        nargs=1,
        # default="",
        # const="factory",
        type=str,
        help="type of reset you want to perform",
        choices=[
            "security",
            "factory",
            "device",
            "service",
            "network",
        ],
    )
    args = parser.parse_args()

    # if args.reset:
    #     print(args.reset)
    #     sys.exit()

    if args.ip in ["test", "tester", "demo"]:
        address = my8865
    elif args.ip == "7841":
        address = test7841
    # got this regex from: https://stackoverflow.com/a/36760050
    elif not re.match(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$", args.ip):
        raise Exception(f"IP address '{args.ip}' is not a valid IP address")
    else:
        address = args.ip

    # print(args)
    # sys.exit()

    username, password = get_credentials()

    cucm = UCMConnection(username, password)
    with PhoneMessenger(address, "8865", username, password, cucm) as myphone:
        if args.interactive:
            myphone.interactive_mode()
        elif args.reset:
            myphone.reset(args.reset[0])
        else:
            print("Nothing to do...")


def dial_number(number: int, phone: PhoneMessenger) -> None:
    phone.send_commands("Dial:" + str(number))
    # phone._dl_screenshot("tmp/screenshot.bmp")
    # phone.interactive_mode()


if __name__ == "__main__":
    test7841 = "10.12.4.118"
    my8865 = "10.12.4.231"

    reset_user_interface()

    # username, password = get_credentials()
    # ucm = UCMConnection(username, password)
    # phones = [
    #     PhoneMessenger(ip, "8845", username, password, ucm)
    #     for ip in ["10.12.26.162"]  # , "10.12.26.163", "10.12.26.165", "10.12.26.164"]
    # ]
    # try:
    #     for phone in phones:
    #         print(f"Dialing on {phone.ip}...")
    #         dial_number(8644462276, phone)

    #     input("\npress enter to end all calls...")
    #     for phone in phones:
    #         phone.send_keys("Soft2")
    #         phone._dl_screenshot("tmp/screenshot.bmp")
    #         input(f"Confirm {phone.ip} has ended call [press enter]")
    # except KeyboardInterrupt:
    #     print("exiting...")
    # finally:
    #     [p.close() for p in phones]