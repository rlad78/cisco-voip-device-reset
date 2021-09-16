from ciscoreset import __version__
from ciscoreset.configs import ROOT_DIR
from pathlib import Path


def test_version():
    assert __version__ == "0.1.0"


def test_root_dir():
    root_dir_from_tests: Path = Path(__file__).parent.parent.resolve()
    assert str(root_dir_from_tests) == str(ROOT_DIR.parent.resolve())
