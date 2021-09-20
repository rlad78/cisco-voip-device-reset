from ciscoreset.configs import ROOT_DIR
from ciscoreset.utils import image_to_base64
from ciscoreset import PhoneConnection
import PySimpleGUI as sg
import concurrent.futures
from concurrent.futures import Future
import time

TASK_TYPES = ("screenshot", "reset", "buttons")


class BGTasks:
    instances = 0

    def __init__(self, window: sg.Window, max_threads=1) -> None:
        if BGTasks.instances > 0:
            raise Exception("Cannot create more than one BGTasks instance")
        self.__window = window
        self.__ex = concurrent.futures.ThreadPoolExecutor(max_workers=max_threads)
        self.__tasks: dict = {n: [] for n in TASK_TYPES}
        self.exceptions: list = []
        BGTasks.instances += 1

    def __update_window_callback(self, *args, **kwargs) -> None:
        for element in self.__window.AllKeysDict.values():
            if type(element) == sg.Button and (
                element.metadata != "n/a" and element.metadata != "no reset"
            ):
                element.update(disabled=False)

        if args[0].exception() is not None:
            self.__window["-STATUS-"].update(str(args[0].exception()))
        elif not args[0].cancelled():
            self.__window["-SCREENSHOT-"].update(
                image_to_base64(args[0].result(), (400, 240))
            )
            self.__window["-DL_STATUS-"].update("")
            self.__window.refresh()

    def __finish_reset_callback(self, *args, **kwargs) -> None:
        if args[0].exception() is not None:
            self.__window["-STATUS-"].update(str(args[0].exception()))
        elif not args[0].cancelled():
            self.__window["-STATUS-"].update("")

        for element in self.__window.AllKeysDict.values():
            if type(element) == sg.Button:
                element.update(disabled=False)
        self.__window.refresh()

    def __clean_task_list(self) -> None:
        for tasks in self.__tasks.values():
            task: Future
            for task in tasks.copy():
                if (e := task.exception()) is not None:
                    self.exceptions.append(e)
                if task.done():
                    tasks.remove(task)

    def _add_task(self, task_type: str, func, *args, **kwargs) -> Future:
        if task_type not in TASK_TYPES:
            raise Exception(f"{task_type} is not a valid background task")

        self.__clean_task_list()
        if len(self.__tasks["screenshot"]) > 0:
            [t.cancel() for t in self.__tasks["screenshot"]]

        fut = self.__ex.submit(func, *args, **kwargs)
        if task_type in ["screenshot"]:
            fut.add_done_callback(self.__update_window_callback)
        elif task_type == "reset":
            fut.add_done_callback(self.__finish_reset_callback)
        self.__tasks[task_type].append(fut)
        return fut

    def disable_buttons(self, enable=False) -> None:
        for element in self.__window.AllKeysDict.values():
            if type(element) == sg.Button and element.metadata != "n/a":
                element.update(disabled=not enable)
        # self.__window.refresh()

    def update_screenshot(self, phone: PhoneConnection) -> Future:

        img_path = gen_screenshot_path(phone.device_ip)

        def dl_screenshot(t_phone: PhoneConnection) -> str:
            print(f"dl-ing screenshot: {img_path}")
            location = t_phone._screenshot()
            print("screenshot downloaded")
            return location

        dl_fut = self._add_task("screenshot", dl_screenshot, phone)
        print("futures started")
        return dl_fut

    def send_key(self, phone: PhoneConnection, key_name: str) -> Future:
        def send(t_phone: PhoneConnection, t_key_name: str):
            t_phone.xml.send_key(t_key_name)

        return self._add_task("buttons", send, phone, key_name)

    def send_reset(self, phone: PhoneConnection, reset_type: str) -> Future:
        def reset(t_phone: PhoneConnection, t_reset_type: str):
            t_phone.send_reset(t_reset_type)
            if t_reset_type in ["Device", "Settings", "Service"]:  # "phone off" resets
                # ? wait until device disconnects
                t = 0.25
                i = 0
                while t_phone.is_reachable():
                    time.sleep(0.25)
                    t += 0.25
                    if t > 15:
                        break
                while not t_phone.is_reachable():
                    i += 1
                    self.__window["-STATUS-"].update(
                        f"Waiting for phone to come back online...({i})"
                    )
                    time.sleep(0.95)
            for n in range(10):
                self.__window["-STATUS-"].update(
                    f"Waiting 10sec for phone to finish up...({n+1})"
                )
                time.sleep(1)
            if t_reset_type in ["Security", "Network"]:
                t_phone._to_home()
                time.sleep(1)

            return t_phone._screenshot()

        return self._add_task("reset", reset, phone, reset_type)


def gen_screenshot_path(device_ip: str) -> str:
    return str(ROOT_DIR / "tmp" / (device_ip.replace(".", "-") + ".bmp"))
