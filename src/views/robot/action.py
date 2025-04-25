from PyQt6.QtWidgets import QWidget, QButtonGroup
from PyQt6.QtCore import Qt
from src.ui.action_container_ui import Ui_action_container


class Action(QWidget, Ui_action_container):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Action Container")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.action_values = {
            "action_name": None,
            "content": None,
            "mode": None,
        }
        self.product_mode = None

        self._setup_radio_group()

        self.action_name.currentIndexChanged.connect(self._on_action_changed)
        # self.delete_action_btn.clicked.connect(self.deleteLater)

        self._reset_ui()

    def _reset_ui(self):
        self.post_container.setHidden(True)
        self.interaction_container.setHidden(True)
        self.details_container_w.setHidden(True)
        self.pid_container_w.setHidden(True)
        self.action_name.clear()
        for label, data in [
            ("Marketplace", "marketplace"),
            ("Discussion", "discussion"),
            ("Interaction", "interaction"),
        ]:
            self.action_name.addItem(label, data)
        self.action_name.setCurrentIndex(-1)
        self.images_message.setText("")
        self.images_message.setHidden(True)
        self.pid_message.setText("")
        self.pid_message.setHidden(True)

    def _on_action_changed(self, index):
        name = self.action_name.currentData()
        self.action_values["action_name"] = name
        self.post_container.setHidden(name == "interaction")
        self.interaction_container.setHidden(name != "interaction")
        self.modeGroup.setExclusive(False)
        for btn in self.mode_buttons.values():
            btn.setChecked(False)
        self.modeGroup.setExclusive(True)
        self.details_container_w.setHidden(True)
        self.pid_container_w.setHidden(True)
        self.action_values["mode"] = None

    def _setup_radio_group(self):
        self.modeGroup = QButtonGroup(self)
        self.mode_buttons = {
            "random": self.random_radio,
            "pid": self.pid_radio,
            "manual": self.manual_radio,
        }
        for mode, btn in self.mode_buttons.items():
            self.modeGroup.addButton(btn)
        self.modeGroup.buttonClicked.connect(self._on_mode_changed)

    def _on_mode_changed(self, button):
        mode = next(m for m, b in self.mode_buttons.items() if b is button)
        self.action_values["mode"] = mode
        manual = mode == "manual"
        show_details = manual
        show_pid = not manual
        self.details_container_w.setHidden(not show_details)
        self.pid_container_w.setHidden(not show_pid)

        if mode == "random":
            self.pid_input.setDisabled(True)
        else:
            self.pid_input.setDisabled(False)

        if manual:
            self.action_values["content"] = {
                "title": "",
                "description": "",
                "image_paths": "",
            }
        else:
            self.action_values["content"] = {}

    def get_fields(self):
        name = self.action_values.get("action_name")
        product_mode = self.action_values.get("mode")
        if product_mode in ("random", "pid"):
            content = self.pid_input.text()
        elif product_mode == "manual":
            content = {
                "title": self.title_input.text(),
                "description": self.description_input.toPlainText(),
                "image_paths": self.images_input.text(),
            }
        else:
            content = {}

        return {
            "action_name": name,
            "content": content,
            "mode": product_mode,
        }
