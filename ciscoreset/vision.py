from typing import Tuple
import cv2
import numpy as np


def get_coords(subimage_path: str, main_image_path: str) -> Tuple[int, int]:
    main_img = cv2.imread(main_image_path)
    sub_img = cv2.imread(subimage_path)
    result = cv2.matchTemplate(main_img, sub_img, cv2.TM_CCOEFF_NORMED)
    return np.unravel_index(result.argmax(), result.shape)


def get_menu_position(menu_item: str, model: str, screenshot_path: str) -> int:
    if (menu_data := MENU_SUPPORT.get(model, None)) is None:
        raise Exception(f"{model} is not supported for menu auto-navigation")
    if (icon := menu_data["icons"].get(menu_item, None)) is None:
        raise Exception(f"{menu_item} is not a valid menu item.")
    row, col = get_coords(icon, screenshot_path)
    print(f"x: {col} | y: {row}")

    menu_cols: tuple[int] = menu_data["coordinates"]["columns"]
    menu_rows: tuple[int] = menu_data["coordinates"]["rows"]

    for x in range(5):
        if col >= menu_cols[x] and col <= menu_cols[x + 1]:
            for y in range(4):
                if row >= menu_rows[y] and row <= menu_rows[y + 1]:
                    print(f"({x+1}, {y+1})")
                    return (x + 1) + (4 * (y))
    else:
        return -1


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
