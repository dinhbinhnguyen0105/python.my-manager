# src/controllers/user_controller.py
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from src.controllers.base_controller import BaseController
from src.services.user_service import (
    UserService,
    UserUDDService,
    UserProxyService,
)
from src.services.user_automation_service import UserAutomationService


class UserController(BaseController):
    def __init__(self, model, parent=None):
        service = UserService()
        super().__init__(model, service, parent)


class UserAutomationController:
    task_status_update_signal = pyqtSignal(int, str)
    task_finished_signal = pyqtSignal(int)
    task_error_signal = pyqtSignal(int, str)

    def __init__(self):
        self.automation_service = UserAutomationService()

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
        self.automation_service.handle_task(task_data_list=task_data)


class UserUDDController(BaseController):
    def __init__(self, model, parent=None):
        service = UserUDDService()
        super().__init__(model, service, parent)

    @staticmethod
    def get_selected_udd():
        return UserUDDService.get_selected_udd()


class UserProxyController(BaseController):
    def __init__(self, model, parent=None):
        service = UserProxyService()
        super().__init__(model, service, parent)
