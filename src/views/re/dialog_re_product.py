# src/views/re/dialog_re_product.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from src import constants
from src.models.re_model import REProductModel
from src.controllers.base_controller import BaseController
from src.controllers.re_controller import REProductController
from src.ui.dialog_re_product_ui import Ui_Dialog_REProduct


class DialogREProduct(QDialog, Ui_Dialog_REProduct):
    def __init__(self, payload=constants.RE_PRODUCT_INIT_VALUE, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("real estate product".title())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.fields = payload
        self.provinces_combobox.setDisabled(True)
        self.districts_combobox.setDisabled(True)
        self.product_model = REProductModel()
        self.product_controller = REProductController(self.product_model)
        self.setup_ui()
        self.setup_events()

    def setup_ui(self):
        self.option_sell_radio.setProperty("id", 1)
        self.option_rent_radio.setProperty("id", 2)
        self.option_assignment_radio.setProperty("id", 3)
        self.option_sell_radio.setProperty("value", "sell")
        self.option_rent_radio.setProperty("value", "rent")
        self.option_assignment_radio.setProperty("value", "assignment")

        self._setupImageDrop()
        self._init_data()

    def setup_events(self):
        self.option_sell_radio.clicked.connect(
            lambda: self.handle_option_clicked(
                self.option_sell_radio.property("id"),
                self.option_sell_radio.property("value"),
            )
        )
        self.option_rent_radio.clicked.connect(
            lambda: self.handle_option_clicked(
                self.option_rent_radio.property("id"),
                self.option_rent_radio.property("value"),
            )
        )
        self.option_assignment_radio.clicked.connect(
            lambda: self.handle_option_clicked(
                self.option_assignment_radio.property("id"),
                self.option_assignment_radio.property("value"),
            )
        )

        self.buttonBox.accepted.disconnect()
        self.btn_save = self.buttonBox.button(QDialogButtonBox.StandardButton.Save)
        self.btn_save.clicked.connect(self.handle_save)

    def _init_data(self):
        self._init_option_radios()
        if self.fields.get("image_paths"):
            self._display_image(self.fields["image_paths"][0])
        self.street_input.setText(self.fields.get("street"))
        self.description_input.setPlainText(self.fields.get("description"))
        self.area_input.setText(str(self.fields.get("area")))
        self.structure_input.setText(str(self.fields.get("structure")))
        self.function_input.setText(str(self.fields.get("function")))
        self.price_input.setText(str(self.fields.get("price")))

        self._load_combobox_data(
            self.statuses_combobox,
            constants.TABLE_RE_SETTINGS_STATUSES,
            self.fields.get("status_id"),
        )
        self._load_combobox_data(
            self.provinces_combobox,
            constants.TABLE_RE_SETTINGS_PROVINCES,
            self.fields.get("province_id"),
        )
        self._load_combobox_data(
            self.districts_combobox,
            constants.TABLE_RE_SETTINGS_DISTRICTS,
            self.fields.get("district_id"),
        )
        self._load_combobox_data(
            self.wards_combobox,
            constants.TABLE_RE_SETTINGS_WARDS,
            self.fields.get("ward_id"),
        )
        self._load_combobox_data(
            self.categories_combobox,
            constants.TABLE_RE_SETTINGS_CATEGORIES,
            self.fields.get("category_id"),
        )
        self._load_combobox_data(
            self.building_line_s_combobox,
            constants.TABLE_RE_SETTINGS_BUILDING_LINES,
            self.fields.get("building_line_id"),
        )
        self._load_combobox_data(
            self.furniture_s_combobox,
            constants.TABLE_RE_SETTINGS_FURNITURES,
            self.fields.get("furniture_id"),
        )
        self._load_combobox_data(
            self.legal_s_combobox,
            constants.TABLE_RE_SETTINGS_LEGALS,
            self.fields.get("legal_id"),
        )
        pass

    def get_fields(self):
        return {
            "image_paths": self.fields.get("image_paths"),
            "pid": self.pid_input.text(),
            "street": self.street_input.text().lower(),
            "status_id": self.statuses_combobox.currentData(),
            "province_id": self.provinces_combobox.currentData(),
            "district_id": self.districts_combobox.currentData(),
            "ward_id": self.wards_combobox.currentData(),
            "option_id": self.fields.get("option_id"),
            "category_id": self.categories_combobox.currentData(),
            "building_line_id": self.building_line_s_combobox.currentData(),
            "furniture_id": self.furniture_s_combobox.currentData(),
            "legal_id": self.legal_s_combobox.currentData(),
            "area": self.area_input.text(),  # validate
            "structure": self.structure_input.text(),  # validate
            "function": self.function_input.text().lower(),
            "description": self.description_input.toPlainText(),
            "price": self.price_input.text(),  # validate
        }

    def _load_combobox_data(self, combobox_widget, table_name, current_data=-1):
        combobox_widget.clear()
        records = BaseController.read_all_staticmethod(
            constants.RE_CONNECTION, table_name
        )
        for record in records:
            record_id = record.get("id", -1)
            record_vi_label = record.get("label_vi", "undefined")
            combobox_widget.addItem(record_vi_label.title(), record_id)
            if current_data == record_id:
                combobox_widget.setCurrentIndex(combobox_widget.count() - 1)

    def handle_option_clicked(self, option_id, option_value):
        self.legal_s_combobox.setEnabled(option_value not in ("assignment", "rent"))
        self.fields["option_id"] = option_id
        new_pid = self.product_controller.generate_pid(option_value)
        self.pid_input.setText(new_pid)
        self.fields["pid"] = new_pid

    def _init_option_radios(self):
        current_option_id = self.fields.get("option_id")
        if current_option_id == 1:
            self.option_sell_radio.setChecked(True)
        elif current_option_id == 2:
            self.option_rent_radio.setChecked(True)
        elif current_option_id == 3:
            self.option_assignment_radio.setChecked(True)
        else:
            pass
        self.pid_input.setText(self.fields.get("pid"))
        self.pid_input.setReadOnly(True)

    def handle_save(self):
        self.fields = self.get_fields()
        if not self.product_controller.validate_product(self.fields):
            return False
        self.accept()

    def clear_field(self):
        self.fields = None

    def _setupImageDrop(self):
        self.image_input.setAcceptDrops(True)
        self.image_input.dragEnterEvent = self._imagesDragEnterEvent
        self.image_input.dropEvent = self._imagesDropEvent

    def _imagesDragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def _imagesDropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            images = [url.toLocalFile() for url in event.mimeData().urls()]
            self._handleDroppedImages(images)
            self.fields["image_paths"] = images

    def _handleDroppedImages(self, image_paths):
        if image_paths:
            self._display_image(image_paths[0])
        else:
            self.image_input.setText("No images dropped.")

    def _display_image(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_input.setPixmap(
                pixmap.scaled(
                    self.image_input.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.image_input.setText("Failed to load image.")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from src.database.re_database import initialize_re_db

    app = QApplication([])
    if initialize_re_db():
        dialog = DialogREProduct()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            print(dialog.fields)
            print("passed!")
