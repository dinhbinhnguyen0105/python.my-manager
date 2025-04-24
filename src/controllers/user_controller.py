# src/controllers/user_controller.py
from src.controllers.base_controller import BaseController
from src.services.user_service import (
    UserService,
    UserUDDService,
    UserProxyService,
)


class UserController(BaseController):
    def __init__(self, model, parent=None):
        service = UserService()
        super().__init__(model, service, parent)


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
