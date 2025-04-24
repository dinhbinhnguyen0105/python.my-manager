from PyQt6.QtWidgets import QMessageBox, QWidget
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

    def setup_ui(self):
        self.set_table_ui()

    def set_table_ui(self):
        self.users_table.setModel(self.proxy_model)
        self.users_table.setSortingEnabled(True)
        self.users_table.setSelectionBehavior(
            self.users_table.SelectionBehavior.SelectRows
        )

        self.users_table.hideColumn(1)
        self.users_table.hideColumn(4)
        self.users_table.hideColumn(5)
        self.users_table.hideColumn(6)
        self.users_table.hideColumn(7)
        self.users_table.hideColumn(8)
        self.users_table.hideColumn(12)
        self.users_table.hideColumn(13)
        self.users_table.hideColumn(14)
        self.users_table.hideColumn(15)
        self.users_table.hideColumn(16)

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
        self.task_data = {}
        for u in users:
            utask = self.robot_controller.build_task(u, raw_actions)
            self.task_data[utask.user_id] = utask
        QMessageBox.information(self, "Lưu thành công", "Đã lưu action cho người dùng.")

    def on_run_bot(self):
        self.robot_controller.discussion(self.task_data)

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
