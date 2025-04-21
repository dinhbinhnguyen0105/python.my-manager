# src/views/user/dialog_user_create.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox
from src.ui.dialog_user_ui import Ui_Dialog_UserCreate


class DialogUserCreate(QDialog, Ui_Dialog_UserCreate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("create user".title())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.fields = {}
        self.input_widgets = [
            self.uid_input,
            self.username_input,
            self.password_input,
            self.two_fa_input,
            self.email_input,
            self.email_password_input,
            self.phone_number_input,
            self.note_input,
            self.type_input,
            self.group_input,
        ]
        self.buttonBox.accepted.connect(self.handle_save)

    def set_events(self):
        pass

    def set_fields(self):
        self.fields = {
            "uid": self.uid_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "two_fa": self.two_fa_input.text(),
            "email": self.email_input.text(),
            "email_password": self.email_password_input.text(),
            "phone_number": self.phone_number_input.text(),
            "note": self.note_input.text(),
            "type": self.type_input.text(),
            "group": self.group_input.text(),
        }

    def handle_save(self):
        self.set_fields()
        self.accept()

    def clear_field(self):
        for input_widget in self.input_widgets:
            input_widget.setText("")
