# src/views/user/dialog_user_settings.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QMenu, QDialog
from PyQt6.QtGui import QAction

from src import constants
from src.ui.dialog_user_settings_ui import Ui_Dialog_UserSettings

from src.controllers.user_controller import UserProxyController, UserUDDController
from src.models.user_model import UserUDDModel, UserProxyModel


class DialogUserSettings(QDialog, Ui_Dialog_UserSettings):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("user settings".title())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.controller = None
        self.proxy_container.setHidden(True)
        self.udd_container.setHidden(True)
        self.set_events()

    def set_events(self):
        self.udd_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_USER_SETTINGS_UDD)
        )
        self.proxy_radio.clicked.connect(
            lambda: self.set_table(constants.TABLE_USER_SETTINGS_PROXY)
        )
        self.create_new_btn.clicked.connect(self.handle_create)
        self.buttonBox.rejected.connect(self.reject)

    def set_table(self, table_name):
        if table_name == constants.TABLE_USER_SETTINGS_PROXY:
            self.controller = UserProxyController(UserProxyModel())
        elif table_name == constants.TABLE_USER_SETTINGS_UDD:
            self.controller = UserUDDController(UserUDDModel())
        self.proxy_container.setHidden(
            table_name != constants.TABLE_USER_SETTINGS_PROXY
        )
        self.udd_container.setHidden(table_name != constants.TABLE_USER_SETTINGS_UDD)
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
                    "value": self.udd_input.text(),
                    "is_selected": (
                        1 if self.udd_is_selected_checkbox.isChecked() else 0
                    ),
                }
            )
        else:
            self.controller.create(
                {
                    "value": self.proxy_input.text(),
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


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from src.database.user_database import initialize_user_db

    app = QApplication([])
    if initialize_user_db():
        dialog = DialogUserSettings()
        dialog.exec()

    else:
        print("database init failed")
