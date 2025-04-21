# src/views/re/dialog_re_template.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QMessageBox, QMenu
from PyQt6.QtGui import QAction

from src import constants
from src.controllers.re_controller import (
    REOptionController,
    RETemplateTitleController,
    RETemplateDescriptionController,
)
from src.models.re_model import RETitleModel, REDescriptionModel
from src.ui.dialog_re_template_settings_ui import Ui_Dialog_RETemplateSettings


class DialogRETemplateSetting(QDialog, Ui_Dialog_RETemplateSettings):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("real estate template setting".title())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.controller = None
        self.current_table = None
        self.title_container.setHidden(True)
        self.description_container.setHidden(True)
        self.setup_events()

    def setup_events(self):
        self.title_radio.clicked.connect(
            lambda: self.setup_model_and_ui(constants.TABLE_RE_SETTINGS_TITLE)
        )
        self.description_radio.clicked.connect(
            lambda: self.setup_model_and_ui(constants.TABLE_RE_SETTINGS_DESCRIPTION)
        )
        self.create_btn.clicked.connect(self.handle_create)
        return True

    def setup_model_and_ui(self, table_name):
        self.options_combobox.clear()
        options = REOptionController.read_all_staticmethod()
        for option in options:
            self.options_combobox.addItem(
                option.get("label_vi").capitalize(), option.get("id")
            )
        if table_name == constants.TABLE_RE_SETTINGS_TITLE:
            self.current_table = constants.TABLE_RE_SETTINGS_TITLE
            # self.title_container.setHidden(False)
            # self.description_container.setHidden(True)
            self.controller = RETemplateTitleController(RETitleModel())
        elif table_name == constants.TABLE_RE_SETTINGS_DESCRIPTION:
            self.current_table = constants.TABLE_RE_SETTINGS_DESCRIPTION
            # self.title_container.setHidden(True)
            # self.description_container.setHidden(False)
            self.controller = RETemplateDescriptionController(REDescriptionModel())
        else:
            raise ValueError(f"Unknown table name: {table_name}")
        self.title_container.setHidden(table_name != constants.TABLE_RE_SETTINGS_TITLE)
        self.description_container.setHidden(
            table_name != constants.TABLE_RE_SETTINGS_DESCRIPTION
        )
        self.tableView.setModel(self.controller.model)
        self.set_table()
        return True

    def set_table(self):
        self.tableView.hideColumn(0)
        self.tableView.hideColumn(5)
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
        if not self.controller or not self.current_table:
            return
        self.controller.create(
            {
                "option_id": self.options_combobox.currentData(),
                "value": (
                    self.title_input.text()
                    if self.current_table == constants.TABLE_RE_SETTINGS_TITLE
                    else self.description_input.toPlainText()
                ),
            }
        )

    def handle_delete(self):
        if not self.controller:
            return False
        record_ids = self.get_selected_ids()
        if record_ids:
            reply = QMessageBox.question(
                self,
                "Confirm",
                f"Delete record(s) with ID(s): {record_ids}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                for record_id in record_ids:
                    self.controller.delete(record_id)
        else:
            QMessageBox.warning(self, "Warning", "Please select a row to delete.")

    def get_selected_ids(self):
        selection_model = self.tableView.selectionModel()
        selected_rows = selection_model.selectedRows()
        record_ids = []
        for selected_row in selected_rows:
            row = selected_row.row()
            id_column = self.controller.model.fieldIndex("id")
            if id_column != -1:
                index = self.controller.model.index(row, id_column)
                record_ids.append(self.controller.model.data(index))
        return record_ids


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from src.database.re_database import initialize_re_db

    app = QApplication([])
    if initialize_re_db():
        dialog = DialogRETemplateSetting()
        # if dialog.exec() == QDialog.DialogCode.Accepted:
        #     print(dialog.fields)
        #     print("passed!")
        dialog.show()
    sys.exit(app.exec())
