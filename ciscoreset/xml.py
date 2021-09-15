from collections import defaultdict
import requests
import requests.auth
import requests.adapters
from lxml import etree
from html import escape
from time import sleep
from pathlib import Path
import re
from .keys import KEY_SUPPORT, get_range


cgi_errors = {
    "1": "Error parsing CiscoIPPhone object",
    "2": "Error framing CiscoIPPhone object",
    "3": "Internal file error",
    "4": "Authentication error",
}


class HTTPSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs["assert_hostname"] = False
        super().init_poolmanager(*args, **kwargs)


class ProgramError(Exception):
    pass


r_ip = re.compile(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$")


class XMLPhone:
    def __init__(self, ip_addr: str, username: str, password: str, model: str) -> None:
        ip_addr = ip_addr.removeprefix("http://")
        if not r_ip.match(ip_addr):
            raise Exception(f"{ip_addr} is not a valid IP address")
        if model not in KEY_SUPPORT:
            raise Exception(f"Phone model '{model}' is not supported by this program.")
        self.ip: str = ip_addr
        self.username: str = username
        self.password: str = password
        self.model = model

    def send_key(self, key: str) -> None:
        if verify_keys(self.model, [key]):
            if not key.startswith("Key:"):
                key = "Key:" + key
            send_xml(self.ip, self.username, self.password, [key])

    def send_keys(self, keys: list[str]) -> None:
        if verify_keys(self.model, keys):
            key_payloads = defaultdict(list)
            for i, key in enumerate(keys):
                if not key.startswith("Key:"):
                    good_key = "Key:" + key
                else:
                    good_key = key
                # * distribute keys three at a time (XML max payload)
                key_payloads[str(i // 3)].append(good_key)
            for payload in key_payloads.values():
                send_xml(self.ip, self.username, self.password, payload)
        else:
            print(f"Bad key(s) in {keys}")

    def dial_number(self, phone_number: str) -> None:
        if phone_number:
            send_xml(self.ip, self.username, self.password, [f"Dial:{phone_number}"])

    def download_screenshot(self, filepath="tmp/screenshot.bmp") -> str:
        sleep(0.75)
        if not filepath:
            filepath = f"tmp/{self.ip}.bmp"
        elif filepath[-4:] != ".bmp":
            filepath += ".bmp"

        p = Path(filepath)
        if not p.parent.exists():
            p.parent.mkdir(parents=True)

        with open(str(p), "wb") as target:
            resp = requests.get(
                f"http://{self.ip}/CGI/Screenshot",
                auth=requests.auth.HTTPBasicAuth(self.username, self.password),
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
                },
            )

            if not resp.ok:
                raise Exception("Issue downloading screenshot: " + str(resp))

            for block in resp.iter_content(4096):
                if block:
                    target.write(block)

        if not p.is_file():
            raise FileNotFoundError(f'Could not find "{str(p)}"')

        return str(p)


def verify_keys(model: str, keys: list[str]) -> bool:
    """Verifies keys are supported by device.

    Args:
        model (str): Model number only, no other words

        keys (list[str]): List of keys to check. Works with 'Key:' or without.

    Returns:
        bool: False if a key or the device model is not supported, True otherwise
    """
    if (key_pack := KEY_SUPPORT.get(model, None)) is None:
        print(f"Model '{model}' is not supported at this time")
        return False
    else:
        for key in keys:
            key_action = key.removeprefix("Key:")

            # check to see if it's a numeric option
            if any([c.isnumeric() for c in key_action]):
                key_word = "".join([c for c in key_action if not c.isnumeric()])
                key_num = int("".join([c for c in key_action if c.isnumeric()]))
                for valid_key in key_pack["numeric"]:
                    if valid_key.startswith(key_word):
                        # match found, check range
                        lower, upper = get_range(valid_key)
                        if key_num > upper or key_num < lower:
                            print(
                                f"Key:{key_action} is not within valid range ({lower}, {upper})"
                            )
                            return False
                        else:
                            break  # meets criteria
                    else:
                        pass  # not match, keep looking
                else:
                    print(
                        f"Key:{key_action} is not a valid numeric key for Cisco {model}"
                    )
                    return False
            elif key_action not in key_pack["standard"]:  # non-numeric, simple search
                print(f"Key:{key_action} is not a valid key for Cisco {model}")
                return False
        else:  # all checks passed
            return True


# r_url = re.compile(
#     r"(?x) ^ (?: (?: Dial | EditDial) : [0-9*]+"  add a pound back between 9 and *
#     r" | (?: Key | SoftKey | Init) : [a-zA-Z0-9]+"
#     r" | Play : [a-zA-Z0-9._\-]+"
#     r" | Display : (?: Off | On | Default) (: [0-9]+)?"
#     r" | https? :// [^ ]+) $"
# )


# def verify_urls(urls: list[str]) -> bool:
#     for url in urls:
#         if not r_url.search(url):
#             print(f"Invalid URL: {url}")
#             return False
#     else:
#         return True


def send_xml(ip_addr: str, username: str, password: str, commands: list[str]):
    # cancel operation if there's an invalid url
    # if not verify_urls(commands):
    #     return None

    # ? used as legacy for original arguments
    certificate = None
    timeout = 10
    port = 80

    xml = '<?xml version="1.0" encoding="UTF-8"?>' "<CiscoIPPhoneExecute>"

    for url in commands:
        xml += '<ExecuteItem URL="' + escape(url) + '" Priority="' + "0" + '" />'

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
            f"{scheme}://{ip_addr}:{port}/CGI/Execute",
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

        # print(f"{url}: {data}")
