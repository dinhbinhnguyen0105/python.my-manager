# src/app.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QWidget
from src.ui.mainwindow_ui import Ui_MainWindow
from src.views.user.page_user import PageUser
from src.views.re.page_re import PageRE
from src.views.robot.page_robot import PageRobot


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("My manager")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # self.setFixedSize(self.size())
        # 540, 960
        self.setMinimumSize(960, 540)

        self.page_re = PageRE()
        self.page_user = PageUser()
        self.page_robot = PageRobot()

        self.content_container.addWidget(self.page_re)
        self.content_container.addWidget(self.page_user)
        self.content_container.addWidget(self.page_robot)

        self.content_container.setCurrentWidget(self.page_user)

        self.setup_events()

    def setup_ui(self):
        pass

    def setup_events(self):
        self.sidebar_re_btn.clicked.connect(
            lambda: self.content_container.setCurrentWidget(self.page_re)
        )
        self.sidebar_user_btn.clicked.connect(
            lambda: self.content_container.setCurrentWidget(self.page_user)
        )
        self.sidebar_robot_btn.clicked.connect(
            lambda: self.content_container.setCurrentWidget(self.page_robot)
        )
