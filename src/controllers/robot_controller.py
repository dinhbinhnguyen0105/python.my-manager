# src/controllers/robot_controller.py

import sys, traceback
from typing import Any, Optional, Dict, Union, List
from PyQt6.QtCore import pyqtSignal, pyqtSlot

from src.my_types import BrowserInfo, ActionInfo, TaskInfo
from src.services.re_service import (
    RETemplateTitleService,
    RETemplateDescriptionService,
    REProductService,
)
from src.services.user_service import UserService
from src.services.robot_service import RobotService

from src.utils.re_product_handler import (
    replace_keywords,
    init_footer,
)


class RobotController:
    def __init__(self):
        self.user_service = UserService()
        self.re_title_temp_service = RETemplateTitleService()
        self.re_description_temp_service = RETemplateDescriptionService()
        self.re_product_service = REProductService()

    def launch_browser(
        self,
        list_user_info: list[Any],
        is_mobile: bool = False,
        headless: bool = False,
        thread_num: int = 1,
    ):
        tasks = []
        for user_info in list_user_info:
            action_info: ActionInfo = ActionInfo(action_name="launch")
            browser_info: BrowserInfo = BrowserInfo(
                user_id=user_info.get("id"),
                user_data_dir=self.user_service.get_udd(user_info.get("id")),
                user_agent=(
                    user_info.get("mobile_ua")
                    if is_mobile
                    else user_info.get("desktop_ua")
                ),
                headless=headless,
            )
            task_info = TaskInfo(browser_info=browser_info, action=action_info)
            tasks.append(task_info)
        self.robot_service = RobotService(thread_num=thread_num, max_retries=5)
        self.robot_service.add_tasks(tasks=tasks)

    def discussion(
        self,
        task_data: List,
        is_mobile: bool = False,
        headless: bool = False,
        thread_num: int = 1,
    ):
        tasks: List[TaskInfo] = []
        max_action_num = max(
            (len(task.get("actions", [])) for task in task_data), default=0
        )
        for action_num in range(max_action_num):
            for task in task_data:
                user_info = task["user_info"]
                browser_info: BrowserInfo = BrowserInfo(
                    user_id=user_info.get("id"),
                    user_data_dir=self.user_service.get_udd(user_info.get("id")),
                    user_agent=(
                        user_info.get("mobile_ua")
                        if is_mobile
                        else user_info.get("desktop_ua")
                    ),
                    headless=headless,
                )
                try:
                    action_info: ActionInfo = task.get("actions").pop()
                except:
                    action_info = ActionInfo(action_name="<empty>")
                tasks.append(TaskInfo(browser_info=browser_info, action=action_info))

        self.robot_service = RobotService(thread_num=thread_num, max_retries=5)
        self.robot_service.add_tasks(tasks=tasks)

    def build_task(self, user: Dict, action_data: list[Dict[str, Any]]):
        list_action_info: list[ActionInfo] = []
        for action in action_data:
            name = action.get("action_name", "<unknown>")
            mode = action.get("mode", "<unknown>")
            content = action.get("content", {})
            if name in ("discussion", "marketplace"):
                if mode == "manual":
                    action_info = ActionInfo(
                        action_name=name,
                        images_path=self._convert_img_str_to_list(
                            content.get("image_paths")
                        ),
                        title=content.get("title"),
                        description=content.get("description"),
                    )
                    list_action_info.append(action_info)
                    continue
                product = None
                if mode == "pid":
                    product = self._fetch_product(
                        action_mode=mode, action_content=content, user_type=None
                    )
                if mode == "random":
                    product = self._fetch_product(
                        action_mode=mode,
                        action_content=None,
                        user_type=user.get("type"),
                    )
                if not product:
                    continue
                pid_part = product.get("pid").split(".")
                if pid_part[0] == "re":
                    option_id = (
                        1
                        if pid_part[1] == "s"
                        else (
                            2
                            if pid_part[1] == "r"
                            else 3 if pid_part[1] == "a" else None
                        )
                    )
                    title_tpl = self.re_title_temp_service.get_random_template(
                        option_id
                    )
                    desc_tpl = self.re_description_temp_service.get_random_template(
                        option_id
                    )
                    title = replace_keywords(product, title_tpl).upper()
                    description = (
                        f"{title}\n"
                        f"{replace_keywords(product, desc_tpl)}\n"
                        f"{init_footer(product.get('pid'), product.get('updated_at'))}"
                    )
                    image_paths = self.re_product_service.get_images(product.get("id"))
                    list_action_info.append(
                        ActionInfo(
                            action_name=name,
                            images_path=image_paths,
                            title=title,
                            description=description,
                        )
                    )
                else:
                    raise Exception("Invalid template for ", pid_part[0])
        return {
            "user_id": user.get("id"),
            "user_info": user,
            "actions": list_action_info,
        }

    def _fetch_product(
        self,
        action_mode: str,
        action_content: Union[str, None],
        user_type: Union[str, None],
    ):
        try:
            user_type_part = user_type.lower().strip().split(".")
            product_table_name = user_type_part[0]
            product_option = user_type_part[1] if len(user_type_part) > 1 else None
            product_info = None
            if action_mode.lower() == "random":
                if product_table_name == "re":
                    option_id = (
                        1
                        if product_option == "s"
                        else (
                            2
                            if product_option == "r"
                            else 3 if product_option == "a" else None
                        )
                    )
                    if not option_id:
                        raise ValueError("Invalid product_option")
                    return self.re_product_service.get_random_product(option_id)

                # TODO: implement misc or other product types
                raise ValueError("Invalid product_table_name")

            if action_mode.lower() == "pid":
                pid_part = action_content.lower().strip().split(".")
                product_table_name = pid_part[0]
                if product_table_name == "re":
                    return self.re_product_service.read_by_pid(action_content)
                # TODO : implement misc or other product types
                raise ValueError("Invalid product category.")
        except ValueError as e:
            print(e)
            return None

    def _convert_img_str_to_list(self, input_string):
        if not input_string or input_string.strip() == "":
            return []

        parts = input_string.split(",")
        result_list = []
        for part in parts:
            cleaned_part = part.strip()
            if cleaned_part.startswith("'") and cleaned_part.endswith("'"):
                cleaned_part = cleaned_part[1:-1]
            if cleaned_part:
                result_list.append(cleaned_part)

        return result_list
