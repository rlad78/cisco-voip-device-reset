class PhoneConnectException(Exception):
    pass


class UnsupportedDeviceError(Exception):
    pass


class PhoneNavError(Exception):
    pass


class ResetException(Exception):
    pass


phone_exceptions = (
    PhoneNavError,
    PhoneConnectException,
    UnsupportedDeviceError,
    ResetException,
)


def is_phone_exception(e) -> bool:
    """Checks if the given exception is an exception used in the PhoneConnection class

    Parameters
    ----------
    e : Exception
        The exception to check against

    Returns
    -------
    bool
        True if it's a phone exception, False otherwise
    """
    for exc in phone_exceptions:
        if type(exc) == type(e):
            return True
    else:
        return False
