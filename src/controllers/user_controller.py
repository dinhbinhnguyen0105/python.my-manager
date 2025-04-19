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
    def launch_browser(self, record_ids: list, is_mobile: bool = False):
        if not record_ids:
            return
        self.automation_service.launch_automation_task(record_ids, is_mobile)


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
