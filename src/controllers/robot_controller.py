from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from src.services.robot_service import RobotService
from src.services.re_service import (
    RETemplateTitleService,
    RETemplateDescriptionService,
    REProductService,
)
from src.utils.re_product_handler import (
    replace_keywords,
    init_footer,
)


@dataclass
class PostActionInfo:
    action_name: str
    title: str
    description: str
    images: list[str]


@dataclass
class PostTask:
    user_id: int
    user_info: dict
    actions: list[PostActionInfo]


class RobotController:
    task_status_update_signal = pyqtSignal(int, str)
    task_finished_signal = pyqtSignal(int)
    task_error_signal = pyqtSignal(int, str)

    def __init__(self):
        self.robot_service = RobotService()
        self.re_title_temp_service = RETemplateTitleService()
        self.re_description_temp_service = RETemplateDescriptionService()
        self.re_product_service = REProductService()

    @pyqtSlot(list, bool)
    def launch_browser(
        self, record_data: list, is_mobile: bool = False, headless: bool = False
    ):
        if not record_data:
            return
        task_data = []
        for record in record_data:
            task_data.append(
                {
                    "user_info": {
                        "id": record.get("id"),
                        "type": record.get("type"),
                        "ua": (
                            record.get("mobile_ua")
                            if is_mobile
                            else record.get("desktop_ua")
                        ),
                    },
                    "actions": [{"action_name": "launch"}],
                    "headless": headless,
                }
            )
        self.robot_service.handle_task(task_data_list=task_data)

    @pyqtSlot(list, bool)
    def discussion(self, post_tasks: dict[PostTask], headless=False):
        task_data = []
        is_mobile = False
        for post_task in post_tasks.values():
            post_task.user_info["ua"] = (
                post_task.user_info.get("mobile_ua")
                if is_mobile
                else post_task.user_info.get("desktop_ua")
            )
            task_data.append(
                {
                    "user_info": post_task.user_info,
                    "actions": [asdict(action) for action in post_task.actions],
                    "headless": headless,
                }
            )
        # for task in task_data:
        #     print(task.get("actions"))
        self.robot_service.handle_task(task_data, headless)

    def build_task(self, user: Dict[str, Any], raw_actions: list[Dict[str, Any]]):
        tasks: list[PostActionInfo] = []
        for action in raw_actions:
            name = action["action_name"]
            mode = action["mode"]
            content = action["content"]
            if name in ("discussion", "marketplace"):
                if mode == "manual":
                    data = content or {}
                    tasks.append(
                        PostActionInfo(
                            action_name=name,
                            title=data.get("title"),
                            description=data.get("description", ""),
                            images=self.convert_string_to_list(data.get("images", [])),
                        )
                    )
                    continue

                product = self._fetch_product(user, action)
                if not product:
                    continue
                pid_part = product.get("pid").split(".")
                option_id = (
                    1 if pid_part[1] == "s" else 2 if pid_part[1] == "r" else None
                )
                if not option_id:
                    continue
                title_tpl = self.re_title_temp_service.get_random_template(option_id)
                desc_tpl = self.re_description_temp_service.get_random_template(
                    option_id
                )
                title = replace_keywords(product, title_tpl).upper()
                description = (
                    f"{title}\n"
                    f"{replace_keywords(product, desc_tpl)}\n"
                    f"{init_footer(product.get('pid'), product.get('updated_at'))}"
                )
                images = self.re_product_service.get_images(product.get("id"))
                tasks.append(PostActionInfo(name, title, description, images))
        return PostTask(user.get("id"), user_info=user, actions=tasks)

    def _fetch_product(
        self, user: Dict[str, Any], action: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        name = action.get("action_name")
        mode = action.get("mode")
        content = action.get("content")
        if name not in ("marketplace", "discussion"):
            return None

        # Phân tích user type
        user_type = str(user.get("type", "")).lower().strip()
        parts = user_type.split(".")
        product_name = parts[0]
        product_action = parts[1] if len(parts) > 1 else None

        # Random mode
        if mode == "random":
            if product_name == "re":
                option_id = (
                    1 if product_action == "s" else 2 if product_action == "r" else None
                )
                return (
                    self.re_product_service.get_random_product(option_id)
                    if option_id
                    else None
                )
            # TODO: implement misc or other product types
            return None

        # PID mode
        if mode == "pid":
            pid_str = str(content or "").strip()
            parts = pid_str.split(".")
            prod_name = parts[0].lower().strip()
            pid = parts[1] if len(parts) > 1 else pid_str

            if prod_name == "re":
                return self.re_product_service.read_by_pid(pid)
            # TODO: implement misc or other product types
            return None

        return None

    def convert_string_to_list(self, input_string):
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
