from PyQt6.QtWidgets import QMessageBox, QWidget, QDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from src.models.user_model import UserModel
from src.models.re_model import REProductModel
from src.controllers.user_controller import UserController
from src.controllers.robot_controller import RobotController
from src.controllers.re_controller import (
    REProductController,
)
from src.views.robot.action import Action
from src.views.robot.dialog_robot_run import DialogRobotRun
from src.ui.page_robot_ui import Ui_PageRobot


class PageRobot(QWidget, Ui_PageRobot):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Robot")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.source_model = UserModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.user_controller = UserController(self.source_model)

        self.headers = [
            self.proxy_model.headerData(
                col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
            )
            for col in range(self.proxy_model.columnCount())
        ]

        self.re_controller = REProductController(REProductModel())
        self.robot_controller = RobotController()

        self.user_actions: list[Action] = []
        self.task_data = {}

        self.setup_ui()
        self.setup_events()

    def setup_events(self):
        self.tabWidget.tabBarDoubleClicked.connect(self.on_add_new_action)
        self.run_actions_btn.clicked.connect(self.on_run_bot)
        self.save_actions_btn.clicked.connect(self.on_save_actions)

        self.username_input.textChanged.connect(
            lambda: self.apply_filter(self.username_input.text(), "username")
        )
        self.type_input.textChanged.connect(
            lambda: self.apply_filter(self.type_input.text(), "type")
        )
        self.group_input.textChanged.connect(
            lambda: self.apply_filter(self.group_input.text(), "user_group")
        )
        self.note_input.textChanged.connect(
            lambda: self.apply_filter(self.note_input.text(), "note")
        )

    def setup_ui(self):
        self.set_table_ui()

    def set_table_ui(self):
        self.users_table.setModel(self.proxy_model)
        self.users_table.setSortingEnabled(True)
        self.users_table.setSelectionBehavior(
            self.users_table.SelectionBehavior.SelectRows
        )

        for column_hide_name in [
            "status",
            "password",
            "two_fa",
            "email",
            "email_password",
            "phone_number",
            "mobile_ua",
            "desktop_ua",
            "created_at",
            "updated_at",
        ]:
            if column_hide_name in self.headers:
                column_index = self.headers.index(column_hide_name)
                self.users_table.hideColumn(column_index)

    def apply_filter(self, filter_text: str, column_name):
        if filter_text == "Tất cả" or not filter_text.strip():
            self.proxy_model.setFilterFixedString("")
        else:
            self.proxy_model.setFilterFixedString(filter_text)
            if column_name in self.headers:
                self.proxy_model.setFilterKeyColumn(self.headers.index(column_name))

    def on_add_new_action(self, index):
        clicked_tab = self.tabWidget.tabText(index)
        if clicked_tab == "New action":
            new_action = Action()
            new_action.delete_action_btn.clicked.connect(
                lambda: self.on_delete_action(new_action)
            )
            new_action.setObjectName(f"action_{index}")
            self.user_actions.append(new_action)
            self.tabWidget.insertTab(index, new_action, f"Action {index}")
            self.tabWidget.setCurrentIndex(index)

    def on_delete_action(self, action_widget: QAction):
        if action_widget in self.user_actions:
            self.user_actions.remove(action_widget)
        action_widget.deleteLater()

    def on_save_actions(self):
        users = self.get_selected_data()
        raw_actions = [w.get_fields() for w in self.user_actions]
        for user in users:
            user_task = self.robot_controller.build_task(user, raw_actions)
            self.task_data[user_task.get("user_id")] = user_task
        QMessageBox.information(self, "Saved", "")

    def on_run_bot(self):
        self.dialog_run = DialogRobotRun(self)
        self.dialog_run.setWindowTitle("RE Settings")
        self.dialog_run.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.dialog_run.setFixedSize(self.dialog_run.size())

        if self.dialog_run.exec() == QDialog.DialogCode.Accepted:
            self.robot_controller.run_task(
                self.task_data.values(),
                is_mobile=False,
                headless=False,
                thread_num=self.dialog_run.thread_num,
            )

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


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from src.database.re_database import initialize_re_db
    from src.database.user_database import initialize_user_db

    app = QApplication([])
    if initialize_re_db() and initialize_user_db():
        robot_window = PageRobot()
        robot_window.show()

    else:
        print("initialize db failed!")
    sys.exit(app.exec())
