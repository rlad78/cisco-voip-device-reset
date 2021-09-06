from pathlib import Path
from stdiomask import getpass
from cryptography.fernet import Fernet, InvalidToken
import json
from typing import Tuple


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
