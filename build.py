import PyInstaller.__main__
from pathlib import Path


def __base(arch: str, target_os: str):
    PyInstaller.__main__.run(
        [
            f"app_{target_os}.spec",
            "--clean",
            "--noconfirm",
            f"-p {str(Path(__file__).parent)}",
            # f"--target-architecture {arch}" if target_os == "mac" else "",
        ]
    )


def mac_m1():
    __base("arm64", "mac")


def mac():
    __base("x86_64", "mac")


def windows():
    __base("", "windows")


# pathex=[str(Path(__file__).parent)],
