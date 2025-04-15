# src/controllers/re_controller.py
import uuid
from PyQt6.QtWidgets import QMessageBox

from src import constants
from src.controllers.base_controller import BaseController
# from src.services.re_service import (REProductService, REImageDirService, RETemplateTitleService, RETemplateDescriptionService, REStatusService, REWardsService,
#                                      REProvinceService, REDistrictService, REOptionService, RECategoryService, REBuildingLinesService, RELegalsService, REFurnitureService, )
from src.services import re_service


class REProductController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REProductService()
        super().__init__(model, service, parent)

    def create(self, payload):
        payload.setdefault("image_paths", [])
        payload.setdefault("area", 0.0)
        payload.setdefault("structure", 0.0)
        payload.setdefault("function", "")
        payload.setdefault("street", "")
        payload.setdefault("description", "")
        payload.setdefault("price", 0.0)

        try:
            if not self.validate_product(payload):
                return False
            if len(payload.get("image_paths")) < 1:
                QMessageBox.critical(None, "Error", "Invalid images.")
                return False
            if self.service.create(payload):
                self.load_data()
                QMessageBox.information(
                    None, "Success", "Real estate product added successfully."
                )
                return True
            else:
                QMessageBox.critical(
                    None, "Error", "Failed to create new real estate product."
                )
                return False
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            return False

    def read(self, record_id, raw=False):
        try:
            if not raw:
                product = self.service.read(record_id)
            else:
                product = self.service.read_raw(record_id)
            if not product:
                QMessageBox.warning(None, "Warning", "Product not found.")
            return product
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            return None

    def read_all(self):
        try:
            return self.service.read_all()
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            return []

    def update(self, record_id, payload):
        payload.setdefault("image_paths", [])
        payload.setdefault("area", 0.0)
        payload.setdefault("structure", 0.0)
        payload.setdefault("function", "")
        payload.setdefault("description", "")
        payload.setdefault("price", 0.0)
        try:
            if not self.validate_product(payload):
                return False
            if self.service.update(record_id, payload):
                self.load_data()
                QMessageBox.information(
                    None, "Success", "Real estate product updated successfully."
                )
                return True
            else:
                QMessageBox.warning(
                    None, "Warning", "Failed to update product.")
                return False
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            return False

    def delete(self, record_id):
        try:
            if self.service.delete(record_id):
                self.load_data()
                QMessageBox.information(
                    None, "Success", "Real estate product deleted successfully."
                )
                return True
            else:
                QMessageBox.warning(
                    None, "Warning", "Failed to delete product.")
                return False
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            return False

    def get_images(self, record_id):
        return self.service.get_images(record_id)

    def get_columns(self):
        return self.service.get_columns()

    def generate_pid(self, option):
        try:
            while True:
                uuid_str = str(uuid.uuid4())
                pid = uuid_str.replace("-", "")[:8]
                if option.lower() == "sell":
                    pid = "S." + pid
                elif option.lower() == "rent":
                    pid = "R." + pid
                elif option.lower() == "assignment":
                    pid = "A." + pid
                else:
                    raise ValueError("Invalid option")
                pid = ("RE." + pid).lower()
                if not self.service.is_value_existed({"pid": pid}):
                    return pid
                else:
                    continue
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            raise Exception("Failed to generate PID.")

    def validate_product(self, payload):
        if not payload.get("image_paths"):
            QMessageBox.critical(
                None, "Error", "invalid image paths.".capitalize())
            return False
        if not payload.get("pid") or self.service.is_value_existed({"pid": payload.get("pid")}):
            QMessageBox.critical(None, "Error", "invalid pid.".capitalize())
            return False
        if not isinstance(payload.get("area"), (int, float)):
            QMessageBox.critical(
                None, "Error", "area must be numbers.".capitalize())
            return False
        if not isinstance(payload.get("structure"), (int, float)):
            QMessageBox.critical(
                None, "Error", "structure must be numbers.".capitalize())
            return False
        if not isinstance(payload.get("price"), (int, float)) or payload.get("price") <= 0:
            QMessageBox.critical(
                None, "Error", "price must be a number and greater than 0.".capitalize())
            return False
        if not re_service.REStatusService.is_value_existed({"id": payload.get("status_id")}):
            QMessageBox.critical(None, "Error", "Invalid status selected.")
            return False
        if not re_service.REProvinceService.is_value_existed({"id": payload.get("province_id")}):
            QMessageBox.critical(None, "Error", "Invalid province selected.")
            return False
        if not re_service.REDistrictService.is_value_existed({"id": payload.get("district_id")}):
            QMessageBox.critical(None, "Error", "Invalid district selected.")
            return False
        if not re_service.REWardsService.is_value_existed({"id": payload.get("ward_id")}):
            QMessageBox.critical(None, "Error", "Invalid ward selected.")
            return False
        if not re_service.REOptionService.is_value_existed({"id": payload.get("option_id")}):
            QMessageBox.critical(None, "Error", "Invalid option selected.")
            return False
        if not re_service.RECategoryService.is_value_existed({"id": payload.get("category_id")}):
            QMessageBox.critical(None, "Error", "Invalid category selected.")
            return False
        if not re_service.REBuildingLinesService.is_value_existed({"id": payload.get("building_line_id")},):
            QMessageBox.critical(
                None, "Error", "Invalid building_line selected.")
            return False
        if not re_service.REFurnitureService.is_value_existed({"id": payload.get("furniture_id")},):
            QMessageBox.critical(None, "Error", "Invalid furniture selected.")
            return False
        if not re_service.RELegalsService.is_value_existed({"id": payload.get("legal_id")}):
            QMessageBox.critical(None, "Error", "Invalid legal selected.")
            return False

        return True


class REStatusController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REStatusService()
        super().__init__(model, service, parent)


class REProvinceController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REProvinceService()
        super().__init__(model, service, parent)


class REDistrictController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REDistrictService()
        super().__init__(model, service, parent)


class REWardsController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REWardsService()
        super().__init__(model, service, parent)


class REOptionController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REOptionService()
        super().__init__(model, service, parent)


class RECategoryController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.RECategoryService()
        super().__init__(model, service, parent)


class REBuildingLinesController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REBuildingLinesService()
        super().__init__(model, service, parent)


class RELegalsController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.RELegalsService()
        super().__init__(model, service, parent)


class REFurnitureController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REFurnitureService()
        super().__init__(model, service, parent)


class RETemplateTitleController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.RETemplateTitleService()
        super().__init__(model, service, parent)


class RETemplateDescriptionController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.RETemplateDescriptionService()
        super().__init__(model, service, parent)


class REImageDirController(BaseController):
    def __init__(self, model, parent=None):
        service = re_service.REImageDirService()
        super().__init__(model, service, parent)
