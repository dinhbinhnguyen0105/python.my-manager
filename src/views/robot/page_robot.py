from PyQt6.QtWidgets import QMessageBox, QWidget, QMenu, QDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QPoint, QSortFilterProxyModel
from src.models.user_model import UserModel
from src.models.re_model import REProductModel
from src.controllers.user_controller import UserController, UserAutomationController
from src.controllers.re_controller import REProductController

from src.ui.page_robot_ui import Ui_PageRobot
from src.ui.action_container_ui import Ui_action_container


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

        self.user_actions: list[TabAction] = []

        self.setup_ui()
        self.setup_events()

    def setup_events(self):
        self.tabWidget.tabBarDoubleClicked.connect(self.on_add_new_action)
        # for action_widget in self.user_actions:
        #     action_widget.

        self.pushButton.clicked.connect(self.on_run_bot)

    def setup_ui(self):
        self.set_table_ui()

    def set_table_ui(self):
        self.users_table.setModel(self.proxy_model)
        self.users_table.setSortingEnabled(True)
        # self.users_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # self.users_table.customContextMenuRequested.connect(self.show_context_menu)
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
            new_action = TabAction()
            new_action.setObjectName(f"action_{index}")
            self.user_actions.append(new_action)
            self.tabWidget.insertTab(index, new_action, f"Action {index}")
            self.tabWidget.setCurrentIndex(index)

    def on_delete_current_action(self):
        current_index = self.tabWidget.currentIndex()
        if (
            current_index != -1
            and self.tabWidget.tabText(current_index) != "New action"
        ):
            widget_to_remove = self.tabWidget.widget(current_index)
            self.tabWidget.removeEventFilter(current_index)
            widget_to_remove.deleteLater()

    def on_run_bot(self):
        # self.user_actions
        actions = []
        for user_action in self.user_actions:
            actions.append(user_action.get_fields())

        print(actions)


class TabAction(QWidget, Ui_action_container):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Action_container")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.action_values = {"name": None, "content": None, "product_init": None}

        self.setup_ui()
        self.setup_events()

    def setup_ui(self):
        self.interaction_container.setHidden(True)
        self.post_container.setHidden(True)
        self.details_container_w.setHidden(True)
        self.pid_input.setHidden(True)
        self.set_action_name_ui()

    def set_action_name_ui(self):
        self.action_name.clear()
        self.action_name.addItem("Marketplace", "marketplace")
        self.action_name.addItem("Discussion", "discussion")
        self.action_name.addItem("Interaction", "interaction")
        self.action_name.setCurrentIndex(-1)

    def set_action_name_ui_and_value(self):
        action_name = self.action_name.currentData()
        self.action_values["name"] = action_name
        self.post_container.setHidden(
            False
            if action_name != "marketplace" or action_name != "discussion"
            else True
        )
        self.interaction_container.setHidden(
            True
            if action_name != "marketplace" or action_name != "discussion"
            else False
        )

        self.post_container.setHidden(True if action_name == "interaction" else False)
        self.interaction_container.setHidden(
            False if action_name == "interaction" else True
        )

    def set_action_content_ui(self, product_type):
        if product_type == "manual":
            self.action_values["content"] = {
                "images": [],
                "title": "",
                "descriptiont": "",
            }
            self.details_container_w.setHidden(False)
            self.pid_input.setHidden(True)
            self.action_values["product_init"] = "manual"
        elif product_type == "random":
            self.action_values["content"] = ""
            self.details_container_w.setHidden(True)
            self.pid_input.setHidden(False)
            self.action_values["product_init"] = "random"
        elif product_type == "pid":
            self.action_values["content"] = ""
            self.details_container_w.setHidden(True)
            self.pid_input.setHidden(False)
            self.action_values["product_init"] = "pid"

    def setup_events(self):
        self.action_name.currentIndexChanged.connect(self.set_action_name_ui_and_value)
        self.random_radio.clicked.connect(lambda: self.set_action_content_ui("random"))
        self.pid_radio.clicked.connect(lambda: self.set_action_content_ui("pid"))
        self.manual_radio.clicked.connect(lambda: self.set_action_content_ui("manual"))

    def get_fields(self):
        if (
            self.action_values["name"] == "discussion"
            or self.action_values["name"] == "marketplace"
        ):
            if (
                self.action_values["product_init"] == "random"
                or self.action_values["product_init"] == "pid"
            ):
                self.action_values["content"] = self.pid_input.text()
            if self.action_values["product_init"] == "manual":
                self.action_values["content"] = {
                    "title": self.title_input.text(),
                    "description": self.description_input.toPlainText(),
                    # "images": self.image_input.text(),
                }

        return self.action_values


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
