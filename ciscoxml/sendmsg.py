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

from stdiomask import getpass
import cv2
import pytesseract
from pathlib import Path
from typing import Union

# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


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

    exit(0)


SUPPORTED_PHONE_MODELS = ["8845", "8865"]


class PhoneMessenger:
    def __init__(self, ip: str, model: str, username: str, password: str) -> None:
        # generate arg pattern for this phone
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

    def _dl_screenshot(self, savepath="") -> str:
        if not savepath:
            savepath = f"tmp/{self.ip}.bmp"
        elif savepath[-4:] != ".bmp":
            savepath += ".bmp"

        err_code: int = os.system(
            f"mkdir -p tmp && wget --user={self.user} --password={self.password} http://{self.ip}/CGI/Screenshot -O {savepath}"
        )
        if err_code:
            raise Exception("Screenshot wget returned err code of " + str(err_code))

        p = Path(savepath)

        if not p.is_file():
            raise FileNotFoundError(f'Could not find "tmp/{self.ip}.bmp"')

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
            print(f"Running: {arg_list}")
            run(arg_list)

    def send_keys(self, *args):
        new_args = ["Key:" + a for a in args]
        self.send_commands(*new_args)

    def _8800_reset(self, reset_type: str):
        self.send_keys("Applications")
        admin_key = self.get_menu_position("Admin", grid=True)
        self.send_keys(f"KeyPad{admin_key}", "KeyPad5")

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

    def factory_reset(self) -> None:
        if self.model in ["8841", "8845", "8865"]:
            self._8800_reset(reset_type="factory")
            self.save_screenshot("tmp/factory_reset_complete.bmp")


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


if __name__ == "__main__":
    # run()

    # img_file = Path("admin.png")
    # img = cv2.imread(str(img_file))
    # bw_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # th, th_img = cv2.threshold(bw_img, 171, 255, cv2.THRESH_OTSU)
    # new_img_file = img_file.with_stem(img_file.stem + "_bin")
    # cv2.imwrite(str(new_img_file), th_img)
    # img_text = pytesseract.image_to_string(th_img, config=r"--psm 4")
    # print(re.findall(r"(\d+)\W+Network", img_text))
    # print(img_text)

    # lookingfor = "Bluetooth"
    # print(
    #     f"{lookingfor} is in slot number "
    #     + regex_image("s.bmp", r"(\d+)\W+" + lookingfor)
    # )
    mine = PhoneMessenger("10.12.4.231", "8845", "rcarte4", "WorkArfWork@93")
    mine.factory_reset()

    # for arg in sys.argv[1:]:
    #     print(arg)
