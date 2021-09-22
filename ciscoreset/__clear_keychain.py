import keyring
from ciscoreset.configs import URL_MAGIC_KEY, DUMMY_KEY
from ciscoreset.credentials import delete_credentials


def clear_keychain():
    try:
        keyring.delete_password("ciscoreset", DUMMY_KEY)
    except keyring.errors.PasswordDeleteError:
        print("could not delete dummy key")

    try:
        keyring.delete_password("ciscoreset", URL_MAGIC_KEY)
    except keyring.errors.PasswordDeleteError:
        print("could not delete url key")

    delete_credentials()
