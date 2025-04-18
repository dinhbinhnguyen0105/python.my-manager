# src/controllers/base_controller.py
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QDataWidgetMapper
from src.services.base_service import BaseService
from src.models.re_model import BaseSettingModel


class BaseController(QObject):
    current_record_changed = pyqtSignal(dict)

    def __init__(self, model: BaseSettingModel, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.model = model
        self.mapper = QDataWidgetMapper(self)
        self._initialize_mapper()

    def _initialize_mapper(self):
        self.mapper.setModel(self.model)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.SubmitPolicy.ManualSubmit)
        self.mapper.currentIndexChanged.connect(self._on_current_index_changed)
        self.load_data()

    def bind_ui_widgets(self, **widgets_mapping):
        for field, widget in widgets_mapping.items():
            column = self.model.fieldIndex(field)
            if column != -1:
                self.mapper.addMapping(widget, column)

    def _on_current_index_changed(self, index):
        if index != -1:
            record = self.model.record(index)
            data = {}
            for i in range(record.count()):
                data[record.fieldName(i)] = record.value(i)
            self.current_record_changed.emit(data)

    def load_data(self):
        self.model.select()
        self.mapper.setCurrentIndex(0)  # Hiển thị bản ghi đầu tiên

    def submit_changes(self):
        if self.mapper.submit():
            if self.model.submitAll():
                QMessageBox.information(None, "Success", "Changes saved.")
                return True
            else:
                QMessageBox.critical(
                    None, "Error", f"Database error: {self.model.lastError().text()}"
                )
                return False
        else:
            QMessageBox.warning(None, "Warning", "Could not submit changes from UI.")
            return False

    def create(self, payload):
        if self.service.create(payload):
            self.load_data()
            QMessageBox.information(None, "Success", "Creation successful.")
            return True
        else:
            QMessageBox.critical(None, "Error", "Creation failed.")
            return False

    def update(self, record_id, payload):
        if self.service.update(record_id, payload):
            self.load_data()
            QMessageBox.information(None, "Success", "Update successful.")
            return True
        else:
            QMessageBox.critical(None, "Error", "Update failed.")
            return False

    def delete(self, record_id):
        if self.service.delete(record_id):
            self.load_data()
            QMessageBox.information(None, "Success", "Deletion successful.")
            return True
        else:
            QMessageBox.critical(None, "Error", "Deletion failed.")
            return False

    def delete_multiple(self, record_ids):
        if self.service.delete_multiple(record_ids):
            self.load_data()
            QMessageBox.information(None, "Success", "Deletion successful.")
            return True
        else:
            QMessageBox.critical(None, "Error", "Deletion failed.")
            return False

    def read(self, record_id):
        return self.service.read(record_id)

    def read_all(self):
        return self.service.read_all()

    @staticmethod
    def read_all_staticmethod(connection, table_name):
        return BaseService.read_all_staticmethod(connection, table_name)

    @staticmethod
    def get_label_vi_staticmethod(connection, table_name, record_id):
        return BaseService.get_label_vi_staticmethod(connection, table_name, record_id)
