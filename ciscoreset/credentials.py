from ciscoreset.configs import ROOT_DIR
from pathlib import Path
from requests.adapters import ConnectTimeout, ConnectionError
from stdiomask import getpass
from cryptography.fernet import Fernet, InvalidToken
import requests
import json
from typing import Tuple
import tldextract
import validators
from urllib.parse import urlparse


KEY_LOC = ROOT_DIR.parent / ".ciscoreset_passkey"
CREDS = ROOT_DIR / "user" / "pass.log"


def get_credentials(enable_manual_entry=True, quiet=True) -> Tuple[str, str]:
    # key_loc = Path().cwd().parent / "ciscoreset_passkey"
    # stored = Path("pass.log")

    if CREDS.is_file() and KEY_LOC.is_file():
        try:
            d = credentials_from_file(quiet=quiet)
        except InvalidToken:
            KEY_LOC.unlink()
            CREDS.unlink()
            return get_credentials(quiet=quiet)
    elif enable_manual_entry:
        d = credentials_from_input(quiet=quiet)
    else:
        return "", ""
    return d["username"], d["password"]


def credentials_from_file(quiet=True) -> dict:
    with KEY_LOC.open("rb") as k:
        fernet = Fernet(k.read())
    with CREDS.open("rb") as f:
        d = json.loads(fernet.decrypt(f.read()).decode())
    if not quiet:
        print("Using stored encrypted passwords from", str(CREDS.resolve()), "\n")
    return d


def credentials_from_input(quiet=True) -> dict:
    d: dict = {
        "username": input("CUCM username: "),
        "password": getpass(prompt="CUCM password: "),
        # "tacacs": getpass(prompt="TACACS Password: "),
        # "bang": getpass(prompt='"bang" Password: '),
    }
    write_credentials(**d)
    if not quiet:
        print("Writing ENCRYPTED passwords to", str(CREDS.resolve()))
    return d


def write_credentials(username: str, password: str, quiet=True) -> None:
    d = {"username": username, "password": password}
    key = Fernet.generate_key()
    fernet = Fernet(key)
    with CREDS.open("wb") as f:
        f.write(fernet.encrypt(json.dumps(d).encode()))
    with KEY_LOC.open("wb") as k:
        k.write(key)
    if not quiet:
        print("Writing ENCRYPTED passwords to", str(CREDS.resolve()))


def get_url_status_code(url: str, username="", password="", timeout=10) -> int:
    if all((username, password)):
        auth = requests.auth.HTTPBasicAuth(username, password)
    else:
        auth = None

    try:
        return requests.get(url, auth=auth, timeout=timeout).status_code
    except ConnectionError:
        return -1
    except ConnectTimeout:
        return 0


def validate_ucm_server(url: str, port: int) -> str:
    fullurl = generate_proper_url(url, port)
    if not validators.url(fullurl):
        return f"{fullurl} is not a valid URL"

    status = get_url_status_code(fullurl, timeout=10)
    if status == 200:
        return ""
    elif status == -1:
        return f"Could not find {url}, please check URL"
    elif status == 0:
        return "Could not connect, please make sure port and URL are correct"


def validate_axl_auth(ucm: str, port: int, username: str, password: str) -> bool:
    fullurl: str = generate_proper_url(ucm, port)
    if not all((username, password)):
        return False

    if fullurl.endswith("/"):
        fullurl += "axl/"
    else:
        fullurl += "/axl/"

    if not validators.url(fullurl):
        raise Exception(f"{fullurl} is not a valid URL")

    status = get_url_status_code(fullurl, username, password, timeout=3)
    if status != 200:
        return False
    else:
        return True


def generate_proper_url(url: str, port=0) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    url_parts = urlparse(url)
    scheme = url_parts.scheme
    netloc = url_parts.netloc
    urlpath = url_parts.path

    # subdomain, domain, suffix = tldextract(url)
    if port == 0:
        return f"{scheme}://{netloc}{urlpath}"
    else:
        return f"{scheme}://{netloc}:{port}{urlpath}"


def get_base_url(url: str) -> str:
    return ".".join(tldextract.extract(generate_proper_url(url)))
