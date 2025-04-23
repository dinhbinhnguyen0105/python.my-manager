# src/views/user/page_user.py

from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QPoint, QSortFilterProxyModel
from PyQt6.QtWidgets import QMessageBox, QWidget, QMenu, QDialog

from src.models.user_model import UserModel
from src.controllers.user_controller import UserController, UserAutomationController
from src.views.user.dialog_user_create import DialogUserCreate
from src.views.user.dialog_user_settings import DialogUserSettings

from src.ui.user_ui import Ui_User


class PageUser(QWidget, Ui_User):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Real Estate Product")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # self.setFixedSize(self.size())

        self.source_model = UserModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.user_controller = UserController(self.source_model)
        self.user_automation_controller = UserAutomationController()

        self.setup_ui()
        self.setup_events()

    def setup_ui(self):
        self.set_table()

    def setup_events(self):
        self.action_create_btn.clicked.connect(self.handle_create)
        self.action_setting_btn.clicked.connect(self.handle_setting)

        self.set_filter()

    def set_filter(self):
        self.uid_input.textChanged.connect(
            lambda: self.apply_column_filter(self.uid_input.text(), 2)
        )
        self.username_input.textChanged.connect(
            lambda: self.apply_column_filter(self.username_input.text(), 3)
        )
        self.password_input.textChanged.connect(
            lambda: self.apply_column_filter(self.password_input.text(), 4)
        )
        self.two_fa_input.textChanged.connect(
            lambda: self.apply_column_filter(self.two_fa_input.text(), 5)
        )
        self.email_input.textChanged.connect(
            lambda: self.apply_column_filter(self.email_input.text(), 6)
        )
        self.email_password_input.textChanged.connect(
            lambda: self.apply_column_filter(self.email_password_input.text(), 7)
        )
        self.phone_number_input.textChanged.connect(
            lambda: self.apply_column_filter(self.phone_number_input.text(), 8)
        )
        self.note_input.textChanged.connect(
            lambda: self.apply_column_filter(self.note_input.text(), 9)
        )
        self.type_input.textChanged.connect(
            lambda: self.apply_column_filter(self.type_input.text(), 10)
        )
        self.group_input.textChanged.connect(
            lambda: self.apply_column_filter(self.group_input.text(), 11)
        )

    def apply_column_filter(self, filter_text, column_index):
        if filter_text == "Tất cả" or not filter_text:
            self.proxy_model.setFilterFixedString("")
        else:
            self.proxy_model.setFilterFixedString(filter_text)
            self.proxy_model.setFilterKeyColumn(column_index)

    def set_table(self):
        self.users_table.setModel(self.proxy_model)
        self.users_table.setSortingEnabled(True)
        self.users_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.users_table.customContextMenuRequested.connect(self.show_context_menu)
        self.users_table.setSelectionBehavior(
            self.users_table.SelectionBehavior.SelectRows
        )

    def show_context_menu(self, pos: QPoint):
        global_pos = self.users_table.mapToGlobal(pos)
        menu = QMenu(self.users_table)
        launch_browser_mobile_action = QAction("Launch as mobile", self)
        launch_browser_desktop_action = QAction("Launch as desktop", self)
        check_status_action = QAction("Check", self)
        delete_action = QAction("Delete", self)

        launch_browser_mobile_action.triggered.connect(
            lambda: self.handle_launch(is_mobile=True, headless=False)
        )
        launch_browser_desktop_action.triggered.connect(
            lambda: self.handle_launch(is_mobile=False, headless=False)
        )
        check_status_action.triggered.connect(self.handle_check_status)
        delete_action.triggered.connect(self.handle_delete)

        menu.addAction(launch_browser_mobile_action)
        menu.addAction(launch_browser_desktop_action)
        menu.addAction(check_status_action)
        menu.addAction(delete_action)

        menu.popup(global_pos)

    def handle_delete(self):
        record_ids = self.get_selected_ids()
        if not record_ids:
            return
        record_id = record_ids[0]
        if record_id:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Are you sure you want to delete this user?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                if record_id is not None:
                    self.user_controller.delete(record_id)
                else:
                    QMessageBox.warning(self, "Warning", "No user selected.")
            else:
                # User clicked No, do nothing
                pass

    def handle_create(self):
        create_dialog = DialogUserCreate()
        create_dialog.setWindowTitle("Create New User")
        create_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        create_dialog.setFixedSize(create_dialog.size())
        if create_dialog.exec() == QDialog.DialogCode.Accepted:
            self.user_controller.create(create_dialog.fields)

    def handle_setting(self):
        setting_dialog = DialogUserSettings()
        setting_dialog.setWindowTitle("User Settings")
        setting_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        setting_dialog.setFixedSize(setting_dialog.size())
        setting_dialog.exec()

    def handle_launch(self, is_mobile, headless):
        record_data = self.get_selected_data()
        if not record_data:
            QMessageBox.warning(
                self, "Warning", "Please select at least one user to launch."
            )
            print("PageUser: No users selected.")
            return
        self.user_automation_controller.launch_browser(record_data, is_mobile, headless)

    def handle_check_status(self):
        pass

    def get_selected_ids(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        selected_ids = []
        id_column_index = self.source_model.fieldIndex("id")

        for proxy_index in selected_rows:
            source_index = self.proxy_model.mapToSource(proxy_index)
            if source_index.isValid():
                id_data = self.source_model.data(
                    source_index.siblingAtColumn(id_column_index),
                    Qt.ItemDataRole.DisplayRole,
                )
                selected_ids.append(id_data)
        return selected_ids

    def get_selected_data(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        selected_data = []
        column_count = self.source_model.columnCount()
        headers = [
            self.source_model.headerData(
                col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
            )
            for col in range(column_count)
        ]

        for proxy_index in selected_rows:
            source_index = self.proxy_model.mapToSource(proxy_index)
            if source_index.isValid():
                row_data = {}
                for col in range(column_count):
                    cell_index = self.source_model.index(source_index.row(), col)

                    if cell_index.isValid():
                        data = self.source_model.data(
                            cell_index, Qt.ItemDataRole.DisplayRole
                        )
                        header_key = (
                            headers[col]
                            if headers[col] is not None
                            else f"Column_{col}"
                        )
                        row_data[str(header_key)] = data
                if row_data:
                    selected_data.append(row_data)
        return selected_data
