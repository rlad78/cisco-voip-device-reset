from ciscoreset.configs import ROOT_DIR, USERNAME_MAGIC_KEY
from requests.adapters import ConnectTimeout, ConnectionError
from stdiomask import getpass
from cryptography.fernet import Fernet, InvalidToken
import requests
import json
from typing import Tuple
import tldextract
import validators
from urllib.parse import urlparse
import keyring
import keyring.errors


KEY_LOC = ROOT_DIR.parent / ".ciscoreset_passkey"
CREDS = ROOT_DIR / "user" / "pass.log"


def get_credentials(enable_manual_entry=True, quiet=True) -> Tuple[str, str]:
    if (username := keyring.get_password("ciscoreset", USERNAME_MAGIC_KEY)) is None:
        if enable_manual_entry:
            return credentials_from_input(quiet)
        else:
            return "", ""
    elif (password := keyring.get_password("ciscoreset", username)) is None:
        if enable_manual_entry:
            return credentials_from_input(quiet)
        else:
            return username, ""
    else:
        return username, password


def credentials_from_input(quiet=True) -> Tuple[str, str]:
    username = (input("CUCM username: "),)
    password = (getpass(prompt="CUCM password: "),)
    write_credentials(username, password)
    if not quiet:
        print("Writing ENCRYPTED passwords to system keyring")
    return username, password


def write_credentials(username: str, password: str, quiet=True) -> None:
    keyring.set_password("ciscoreset", USERNAME_MAGIC_KEY, username)
    keyring.set_password("ciscoreset", username, password)


def delete_credentials() -> None:
    username, password = get_credentials(enable_manual_entry=False)
    if username:
        try:
            keyring.delete_password("ciscoreset", USERNAME_MAGIC_KEY)
        except keyring.errors.PasswordDeleteError:
            print("could not delete username key")
    if password:
        try:
            keyring.delete_password("ciscoreset", username)
        except keyring.errors.PasswordDeleteError:
            print("could not delete password key")


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
