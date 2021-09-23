import PyInstaller.__main__
from pathlib import Path
import platform


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


def auto():
    sys_os = platform.system()
    sys_arch = platform.processor()

    if sys_os == "Darwin" and sys_arch == "arm":
        mac_m1()
    elif sys_os == "Darwin" and sys_arch == "i386":
        mac()
    elif sys_os == "Windows":
        windows()
    elif sys_os == "Linux":
        print("Sorry, Linux is not yet supported")
    else:
        print(f"Unknown OS type: {sys_os}{'_' + sys_arch if sys_arch else ''}")


# pathex=[str(Path(__file__).parent)],
