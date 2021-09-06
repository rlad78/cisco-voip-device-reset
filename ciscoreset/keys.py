from typing import Tuple


KEY_SUPPORT: dict[dict] = {}


def get_range(numeric_key: str) -> Tuple[int, int]:
    first, second = numeric_key.split("-")
    return int(first[-1]), int(second)


keys_8800_standard = {
    "standard": [
        "Applications",
        "Contacts",
        "Directories",
        "Headset",
        "Hold",
        "KemPage",
        "KeyPadPound",
        "KeyPadStar",
        "Messages",
        "Mute",
        "NavDwn",
        "NavLeft",
        "NavRight",
        "NavSelect",
        "NavUp",
        "NavBack",
        "Release",
        "Services",
        "Settings",
        "Speaker",
        "VolDwn",
        "VolUp",
    ],
    "numeric": [
        "Feature1-120",
        "FixedFeature1-3",
        "KeyPad0-9",
        "Line1-120",
        "Session1-6",
        "Soft1-5",
    ],
}

for dev in ["8811", "8841", "8845", "8851", "8851NR", "8861", "8865", "8865NR"]:
    KEY_SUPPORT[dev] = keys_8800_standard

keys_8831 = {
    "standard": [
        "KeyPadPound",
        "KeyPadStar",
        "Speaker",
        "VolDwn",
        "VolUp",
    ],
    "numeric": [
        "KeyPad0-9",
        "Soft1-5",
    ],
}

KEY_SUPPORT["8831"] = keys_8831

keys_8832 = keys_8831.copy()
keys_8832["standard"] += [
    "NavDwn",
    "NavSelect",
    "NavUp",
]

KEY_SUPPORT["8832"] = keys_8832
