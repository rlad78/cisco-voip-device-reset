import PySimpleGUI as sg
import concurrent.futures
from concurrent.futures import Future
from ciscoreset.utils import image_to_base64
from ciscoreset import PhoneConnection
from icecream import ic


TASK_TYPES = ("screenshot", "reset", "buttons")


class BGTasks:
    instances = 0

    def __init__(self, window: sg.Window, max_threads=8) -> None:
        if BGTasks.instances > 0:
            raise Exception("Cannot create more than one BGTasks instance")
        self.__window = window
        self.__ex = concurrent.futures.ThreadPoolExecutor(max_workers=max_threads)
        self.__tasks: dict = {n: [] for n in TASK_TYPES}
        self.exceptions: list = []
        BGTasks.instances += 1

    def __update_window_callback(self, *args, **kwargs) -> None:
        # this is basically just to eat args to avoid TypeErrors
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
        fut = self.__ex.submit(func, *args, **kwargs)
        fut.add_done_callback(self.__update_window_callback)
        self.__tasks[task_type].append(fut)

    def update_screenshot(
        self, phone: PhoneConnection, img_element: sg.Image
    ) -> Future:
        def task(t_phone: PhoneConnection, t_img_element: sg.Image) -> Future:
            screenshot_path = t_phone._screenshot()
            t_img_element.update(image_to_base64(screenshot_path, (400, 240)))

        return self._add_task("screenshot", task, phone, img_element)
