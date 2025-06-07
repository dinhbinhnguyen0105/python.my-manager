# src/views/robot/dialog_robot_run.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from src.ui.dialog_robot_run_ui import Ui_Dialog_RobotRun


class DialogRobotRun(QDialog, Ui_Dialog_RobotRun):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("robot run".capitalize())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.thread_num = 0
        self.setup_ui()
        self.setup_events()

    def setup_ui(self):
        self.thread_input.setValue(1)

    def setup_events(self):
        self.thread_input.valueChanged.connect(
            lambda: self.set_thread_num(self.thread_input.value())
        )

        # self.buttonBox.accepted.disconnect()
        # self.btn_ok = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)

    def set_thread_num(self, value):
        self.thread_num = value


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication([])
    dialog = DialogRobotRun()
    app.exit(dialog.exec())
