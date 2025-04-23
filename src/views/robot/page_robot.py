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

        self.user_actions = []

        self.setup_ui()
        self.setup_events()

    def setup_events(self):
        self.tabWidget.tabBarDoubleClicked.connect(self.on_add_new_action)

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

    def set_actions_container_ui(self):
        self.tabWidget
        pass

    def on_add_new_action(self, index):
        clicked_tab = self.tabWidget.tabText(index)
        if clicked_tab == "New action":
            new_action = TabAction()
            self.user_actions.append(new_action)
            self.tabWidget.insertTab(index, new_action, f"Action {index}")
            self.tabWidget.setCurrentIndex(index)


class TabAction(QWidget, Ui_action_container):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Action_container")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setup_ui()
        self.setup_events()
        self.action_values = {}

    def setup_ui(self):
        self.set_action_name_ui()

    def set_action_name_ui(self):
        self.action_name.clear()
        self.action_name.addItem("Marketplace", "marketplace")
        self.action_name.addItem("Discussion", "discussion")
        self.action_name.addItem("Interaction", "interaction")

    def set_action_container_ui(self, index):
        action_name = self.action_name.currentData(index)
        self.post_container.setHidden(False if action_name == "marketplace" else True)
        self.post_container.setHidden(False if action_name == "discussion" else True)
        self.interaction_container.setHidden(
            False if action_name == "interaction" else True
        )
        # if action_name == "marketplace" or action_name == "discussion":
        # elif action_name == "discussion"

    def setup_events(self):
        self.action_name.currentIndexChanged.connect(self.set_action_container_ui)


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
