# src/views/re/dialog_re_settings.py

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QMessageBox, QMenu
from PyQt6.QtGui import QAction

from src import constants
from src.models import re_model
from src.controllers import re_controller
from src.ui.dialog_re_product_settings_ui import Ui_Dialog_REProductSettings


class DialogREProductSetting(QDialog, Ui_Dialog_REProductSettings):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("real estate product setting".title())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.controller = None

        self.basic_setting_container.setHidden(True)
        self.image_dir_setting_container.setHidden(True)

        self.set_events()

    def set_events(self):
        self.statuses_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_STATUSES)
        )
        self.provinces_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_PROVINCES)
        )
        self.districts_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_DISTRICTS)
        )
        self.wards_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_WARDS)
        )
        self.options_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_OPTIONS)
        )
        self.categories_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_CATEGORIES)
        )
        self.building_line_s_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_BUILDING_LINES)
        )
        self.furniture_s_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_FURNITURES)
        )
        self.legal_s_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_LEGALS)
        )
        self.image_dir_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_RE_SETTINGS_IMG_DIRS)
        )
        self.create_btn.clicked.connect(self.handle_create)

    def set_table(self, table_name):
        if table_name == constants.TABLE_RE_SETTINGS_STATUSES:
            self.controller = re_controller.REStatusController(re_model.REStatusModel())
        elif table_name == constants.TABLE_RE_SETTINGS_PROVINCES:
            self.controller = re_controller.REProvinceController(
                re_model.REProvinceModel()
            )
        elif table_name == constants.TABLE_RE_SETTINGS_DISTRICTS:
            self.controller = re_controller.REDistrictController(
                re_model.REDistrictModel()
            )
        elif table_name == constants.TABLE_RE_SETTINGS_WARDS:
            self.controller = re_controller.REDistrictController(
                re_model.REDistrictModel()
            )
        elif table_name == constants.TABLE_RE_SETTINGS_OPTIONS:
            self.controller = re_controller.REOptionController(re_model.REOptionModel())
        elif table_name == constants.TABLE_RE_SETTINGS_CATEGORIES:
            self.controller = re_controller.RECategoryController(
                re_model.RECategoryModel()
            )
        elif table_name == constants.TABLE_RE_SETTINGS_BUILDING_LINES:
            self.controller = re_controller.REBuildingLineController(
                re_model.REBuildingLineModel()
            )
        elif table_name == constants.TABLE_RE_SETTINGS_FURNITURES:
            self.controller = re_controller.REFurnitureController(
                re_model.REFurnitureModel()
            )
        elif table_name == constants.TABLE_RE_SETTINGS_LEGALS:
            self.controller = re_controller.RELegalController(re_model.RELegalModel())
        elif table_name == constants.TABLE_RE_SETTINGS_IMG_DIRS:
            self.controller = re_controller.REImageDirController(
                re_model.REImageDirModel()
            )
        else:
            QMessageBox.warning(self, "Warning", f"Invalid table data ({table_name}).")
        self.basic_setting_container.setHidden(
            table_name == constants.TABLE_RE_SETTINGS_IMG_DIRS
        )
        self.image_dir_setting_container.setHidden(
            table_name != constants.TABLE_RE_SETTINGS_IMG_DIRS
        )
        self.tableView.setModel(self.controller.model)
        self.tableView.setSortingEnabled(True)
        self.tableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.show_context_menu)
        self.tableView.setSelectionBehavior(self.tableView.SelectionBehavior.SelectRows)

    def show_context_menu(self, pos):
        global_pos = self.tableView.mapToGlobal(pos)
        menu = QMenu(self.tableView)
        delete_action = QAction("Delete", self)
        menu.addAction(delete_action)
        menu.popup(global_pos)
        delete_action.triggered.connect(self.handle_delete)

    def handle_create(self):
        if not self.controller:
            return
        if self.controller.model.tableName() == constants.TABLE_RE_SETTINGS_IMG_DIRS:
            self.controller.create(
                {
                    "value": self.image_dir_value_input.text(),
                    "is_selected": (
                        1 if self.img_dir_is_selected_checkbox.isChecked() else 0
                    ),
                }
            )
        else:
            self.controller.create(
                {
                    "label_vi": self.name_vi_input.text(),
                    "label_en": self.name_en_input.text(),
                    "value": self.value_input.text(),
                }
            )

    def handle_delete(self):
        if not self.controller:
            return False
        selection_model = self.tableView.selectionModel()
        selected_rows = [
            selected_row.row() for selected_row in selection_model.selectedRows()
        ]
        record_ids = self.controller.model.get_record_ids(selected_rows)
        if record_ids:
            reply = QMessageBox.question(
                self,
                "Confirm",
                f"Delete record(s) with ID(s): {record_ids}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.controller.delete_multiple(record_ids)
        else:
            QMessageBox.warning(self, "Warning", "Please select a row to delete.")


# TABLE_RE_SETTINGS_STATUSES
# TABLE_RE_SETTINGS_PROVINCES
# TABLE_RE_SETTINGS_DISTRICTS
# TABLE_RE_SETTINGS_WARDS
# TABLE_RE_SETTINGS_OPTIONS
# TABLE_RE_SETTINGS_CATEGORIES
# TABLE_RE_SETTINGS_BUILDING_LINES
# TABLE_RE_SETTINGS_FURNITURES
# TABLE_RE_SETTINGS_LEGALS
# TABLE_RE_SETTINGS_IMG_DIRS

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from src.database.re_database import initialize_re_db

    app = QApplication([])
    if initialize_re_db():
        dialog = DialogREProductSetting()
        dialog.exec()

    else:
        print("database init failed")
