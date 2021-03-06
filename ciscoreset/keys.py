from typing import Tuple


# Key lists are located at:
# https://www.cisco.com/c/en/us/td/docs/voice_ip_comm/cuipph/all_models/xsi/9-1-1/CUIP_BK_P82B3B16_00_phones-services-application-development-notes/CUIP_BK_P82B3B16_00_phones-services-application-development-notes_chapter_0101.html#CUIP_RF_K24B887F_00

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


keys_7832 = {
    "standard": [
        "KeyPadPound",
        "KeyPadStar",
        "Mute",
        "NavDwn",
        "NavSelect",
        "NavUp",
        "Speaker",
        "VolDwn",
        "VolUp",
    ],
    "numeric": [
        "KeyPad0-9",
        "Soft1-4",
    ],
}

keys_7800_standard = {
    "standard": keys_7832["standard"]
    + [
        "Applications",
        "Directories",
        "Headset",
        "Hold",
        "Info",
        "Messages",
        "Services",
        "Settings",
    ],
    "numeric": keys_7832["numeric"]
    + [
        "Line1-120",
    ],
}

KEY_SUPPORT["7832"] = keys_7832
for dev in ["7811", "7821", "7841", "7861"]:
    KEY_SUPPORT[dev] = keys_7800_standard
