from pathlib import Path
import toml

ROOT_DIR: Path = Path(__file__).parent
TOOL_VERSION: str = toml.load(str(ROOT_DIR.parent / "pyproject.toml"))["tool"][
    "poetry"
]["version"]
USERNAME_MAGIC_KEY: str = "VcBeRIb1Zg92rqORplK0"
URL_MAGIC_KEY: str = "Np06VVPShE1RFTEPnwkk"
DUMMY_KEY: str = "wQiA0iASVqlZqEqnYMGf"
