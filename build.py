import PyInstaller.__main__
from pathlib import Path
import platform
import os

ROOT_DIR = Path(__file__).parent


def __base(target_os: str):
    PyInstaller.__main__.run(
        [
            f"app_{target_os}.spec",
            "--clean",
            "--noconfirm",
            f"-p {str(Path(__file__).parent)}",
        ]
    )


def mac_m1():
    print("Building for macOS (arm64)")
    __base("mac_m1")


def mac():
    print("Building for macOS (Intel)")
    __base("mac")


def windows():
    print("Building for Windows")
    __base("windows")


def other():
    PyInstaller.__main__.run(
        [
            str(ROOT_DIR / "ciscoreset" / "gui.py"),
            "--onefile",
            "-n Cisco VoIP Device Reset"
            f"p {str(ROOT_DIR)}",
            "--collect data ciscoreset",
            "--collect-data ciscoaxl",
            f"--add-data pyproject.toml{os.pathsep}."
            "--clean",
            "--noconfirm",
        ]
    )


def auto():
    sys_os = platform.system()
    sys_arch = platform.processor()

    if sys_os == "Darwin" and sys_arch == "arm":
        mac_m1()
    elif sys_os == "Darwin" and sys_arch == "i386":
        mac()
    elif sys_os == "Windows":
        windows()
    else:
        other()


# pathex=[str(Path(__file__).parent)],
