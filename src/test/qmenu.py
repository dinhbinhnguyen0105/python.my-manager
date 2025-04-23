import sys
from PyQt6.QtCore import QEvent, Qt, QPoint
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QMenu,
    QMainWindow,
    QMenuBar,
)
from PyQt6.QtGui import QAction


class MyLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)
        self.menu = self.create_popup_menu()

    def enterEvent(self, event):
        # Show the popup menu at the cursor position when mouse enters
        self.menu.popup(self.mapToGlobal(QPoint(0, self.height())))
        super().enterEvent(event)

    def create_popup_menu(self):
        menu = QMenu(self)
        action1 = QAction("Option 1", self)
        action1.triggered.connect(self.on_option1_selected)
        menu.addAction(action1)

        action2 = QAction("Option 2", self)
        action2.triggered.connect(self.on_option2_selected)
        menu.addAction(action2)

        menu.addSeparator()

        action3 = QAction("Exit", self)
        action3.triggered.connect(self.on_exit_selected)
        menu.addAction(action3)

        return menu

    def on_option1_selected(self):
        print("Option 1 selected")

    def on_option2_selected(self):
        print("Option 2 selected")

    def on_exit_selected(self):
        print("Exit selected")
        QApplication.quit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Popup Menu on Hover")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.my_label = MyLabel("Hover over me to see the menu")
        self.my_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.my_label.setStyleSheet("border: 1px solid black;")

        # Install the event filter on the label
        self.my_label.installEventFilter(self.my_label)

        layout.addWidget(self.my_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
