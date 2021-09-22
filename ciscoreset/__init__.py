import toml

from .axl import CUCM
from .credentials import get_credentials
from .keys import KEY_SUPPORT
from .vision import get_menu_position, get_list_position
from .xml import XMLPhone
from .phone import PhoneConnection
from .configs import ROOT_DIR

__version__ = toml.load(str(ROOT_DIR.parent / "pyproject.toml"))["tool"]["poetry"][
    "version"
]
