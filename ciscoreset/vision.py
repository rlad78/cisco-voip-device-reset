from typing import Tuple
from cv2 import imread, matchTemplate, TM_CCOEFF_NORMED
import numpy as np
from pathlib import Path


def get_coords(subimage_path: str, main_image_path: str) -> Tuple[int, int]:
    main_img = imread(main_image_path)
    sub_img = imread(subimage_path)
    result = matchTemplate(main_img, sub_img, TM_CCOEFF_NORMED)
    return np.unravel_index(result.argmax(), result.shape)


def get_menu_position(menu_item: str, model: str, screenshot_path: str) -> int:
    if (menu_data := MENU_SUPPORT.get(model, None)) is None:
        raise Exception(f"{model} is not supported for menu auto-navigation")
    if (icon := menu_data["icons"].get(menu_item, None)) is None:
        raise Exception(f"{menu_item} is not a valid menu item.")
    row, col = get_coords(icon, screenshot_path)
    # print(f"x: {col} | y: {row}")

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


def get_list_position(entry: str, model: str, screenshot_path: str) -> int:
    menu_files: list[Path] = list(Path("menus").glob("**/*"))
    for menu in menu_files:
        if menu.stem == entry.lower().replace(" ", "_"):
            menu_img_file = menu
            break
    else:
        raise Exception(f"Could not find a matching image for {entry}")

    y, _ = get_coords(str(menu_img_file), screenshot_path)

    for i, height in enumerate([100, 175, 250, 315, 400]):
        if y <= height:
            return i + 1
    else:
        raise Exception(f"Could not find list item '{entry}'")


menu_data: dict = {
    "icons": {
        "Recents": "icons/recents.png",
        "Settings": "icons/settings.png",
        "Accessibility": "icons/accessibility.png",
        "Bluetooth": "icons/bluetooth.png",
        "Accessories": "icons/accessories.png",
        "Running Applications": "icons/running_applications.png",
        "Admin Settings": "icons/admin_settings.png",
        "Phone Information": "icons/phone_information.png",
    },
    "coordinates": {
        "columns": (0, 250, 400, 525, 700),
        "rows": (0, 90, 210, 350),
    },
}

MENU_SUPPORT: dict = {
    dev: menu_data
    for dev in ["8811", "8841", "8845", "8851", "8851NR", "8861", "8865", "8865NR"]
}

# results = defaultdict(list)
# screenshot: str = "/home/rcarte4/devel/cisco-voip-device-reset/tmp/screenshot.bmp"
# for n in range(1, 11, 1):
#     icon = f"/home/rcarte4/devel/cisco-voip-device-reset/icons/{n}.png"
#     results[str(((n - 1) // 4) + 1)].append(get_coords(icon, screenshot))
# for row, values in results.items():
#     print(f"Row {row}: {values}")
