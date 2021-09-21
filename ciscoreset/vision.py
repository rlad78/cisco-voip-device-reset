from ciscoreset.configs import ROOT_DIR
from cv2 import (
    imread,
    cvtColor,
    Canny,
    minMaxLoc,
    matchTemplate,
    TM_CCOEFF_NORMED,
    COLOR_BGR2GRAY,
)
import numpy as np
from pathlib import Path
from typing import Any, Tuple
from collections import namedtuple

# from icecream import ic


ICONS_DIR: Path = ROOT_DIR / "icons"
MENUS_DIR: Path = ROOT_DIR / "menus"


def imread_edges(img_path: str) -> Any:
    return Canny(cvtColor(imread(img_path), COLOR_BGR2GRAY), 50, 200)


def get_coords(subimage_path: str, main_image_path: str) -> Tuple[int, int]:
    main_img = imread(main_image_path)
    sub_img = imread(subimage_path)
    result = matchTemplate(main_img, sub_img, TM_CCOEFF_NORMED)
    return np.unravel_index(result.argmax(), result.shape)


def guess_best_coords(subimages_dir: str, main_image_path: str) -> Tuple[int, int, str]:
    main_img = imread_edges(main_image_path)
    Image = namedtuple("Image", ["correlation", "name", "x", "y"])
    winner = Image(0, "", 0, 0)
    for sub_path in [p for p in Path(subimages_dir).iterdir() if p.suffix == ".png"]:
        sub_img = imread_edges(str(sub_path))
        result = matchTemplate(main_img, sub_img, TM_CCOEFF_NORMED)
        _, bestVal, _, coords = minMaxLoc(result)
        if bestVal > winner.correlation:
            winner = Image(bestVal, sub_path.stem, coords[0], coords[1])
    return winner.x, winner.y, winner.name


def get_menu_position(menu_item: str, model: str, screenshot_path: str) -> int:
    if (menu_data := MENU_SUPPORT.get(model, None)) is None:
        raise Exception(f"{model} is not supported for menu auto-navigation")
    if (icon := find_subimage_file(menu_item, "icons", model)) == "":
        raise Exception(f"{menu_item} is not a valid menu item.")
    row, col = get_coords(icon, screenshot_path)
    # ic(menu_item)
    # ic((col, row))

    menu_cols: tuple[int] = menu_data["coordinates"]["columns"]
    menu_rows: tuple[int] = menu_data["coordinates"]["rows"]

    for x in range(5):
        if col >= menu_cols[x] and col <= menu_cols[x + 1]:
            for y in range(4):
                if row >= menu_rows[y] and row <= menu_rows[y + 1]:
                    # print(f"({x+1}, {y+1})")
                    return (x + 1) + (4 * (y))
    else:
        return -1


def get_list_position(list_item: str, model: str, screenshot_path: str) -> int:
    if model not in MENU_SUPPORT:
        raise Exception(f"Cisco {model} not supported for list auto-navigation")

    sub_images_dir: str = find_subimage_folder(list_item, "menus", model)
    x, y, fontsize = guess_best_coords(sub_images_dir, screenshot_path)

    # menu_img_file = find_subimage_file(entry, "menus", model)
    # y, x = get_coords(menu_img_file, screenshot_path)
    # ic(list_item)
    # ic((x, y, fontsize))

    # ic(entry)
    for i, height in enumerate(MENU_SUPPORT[model]["list_heights"]):
        if y <= height:
            return i + 1
    else:
        raise Exception(f"Could not find list item '{list_item}'")


def find_subimage_folder(wanted: str, image_type: str, model: str) -> str:
    if (menu_data := MENU_SUPPORT.get(model, None)) is None:
        raise Exception(f"Cisco {model} does not have subimage files")
    if (img_folder := menu_data.get(image_type, None)) is None:
        raise Exception(f"{image_type} is not a valid image type for Cisco {model}")
    possible_dirs: list[Path] = [
        dir for dir in Path(img_folder).iterdir() if dir.is_dir()
    ]

    wanted_stem = wanted.lower().replace(" ", "_")
    for folder in possible_dirs:
        if wanted_stem == folder.stem:
            return str(folder.resolve())
    else:
        return ""


def find_subimage_file(wanted: str, image_type: str, model: str) -> str:
    if (menu_data := MENU_SUPPORT.get(model, None)) is None:
        raise Exception(f"Cisco {model} does not have subimage files")
    if (img_folder := menu_data.get(image_type, None)) is None:
        raise Exception(f"{image_type} is not a valid image type for Cisco {model}")
    possible_files: list[Path] = list(Path(img_folder).glob("**/*"))

    wanted_stem = wanted.lower().replace(" ", "_")
    for filepath in possible_files:
        if wanted_stem == filepath.stem:
            return str(filepath.resolve())
    else:
        return ""


menu_data_8800_standard: dict = {
    "icons": str(ICONS_DIR / "8800"),
    "menus": str(MENUS_DIR / "8800"),
    "coordinates": {
        "columns": (0, 250, 400, 525, 700),
        "rows": (0, 90, 210, 350),
    },
    "list_heights": (100, 175, 250, 315, 400),
}

MENU_SUPPORT: dict = {
    dev: menu_data_8800_standard
    for dev in ["8811", "8841", "8845", "8851", "8851NR", "8861", "8865", "8865NR"]
}

# results = defaultdict(list)
# screenshot: str = "/home/rcarte4/devel/cisco-voip-device-reset/tmp/screenshot.bmp"
# for n in range(1, 11, 1):
#     icon = f"/home/rcarte4/devel/cisco-voip-device-reset/icons/{n}.png"
#     results[str(((n - 1) // 4) + 1)].append(get_coords(icon, screenshot))
# for row, values in results.items():
#     print(f"Row {row}: {values}")
