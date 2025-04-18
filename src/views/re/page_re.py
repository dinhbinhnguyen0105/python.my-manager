# src/views/re/page_re.py

from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtCore import Qt, QPoint, QSortFilterProxyModel, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QWidget, QMenu, QDialog

from src import constants
from src.utils.re_product_handler import (
    replace_keywords,
    init_footer,
    open_file_explorer,
)
from src.models.re_model import REProductModel
from src.controllers import re_controller
from src.controllers.base_controller import BaseController
from src.views.re.dialog_re_product import DialogREProduct
from src.views.re.dialog_re_settings import DialogREProductSetting
from src.views.re.dialog_re_template import DialogRETemplateSetting

from src.ui.page_re_ui import Ui_PageRE


class PageRE(QWidget, Ui_PageRE):
    image_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Real Estate Product")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(self.size())
        self.source_model = REProductModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.product_controller = re_controller.REProductController(self.source_model)
        self.img_paths = None

        self.setup_ui()
        self.setup_events()
        self.setup_filters()

    def setup_ui(self):
        self._set_comboboxes()
        self.set_table()

    def setup_events(self):
        self.products_table.selectionModel().selectionChanged.connect(
            self.handle_set_default_template
        )
        self.action_create_btn.clicked.connect(self.handle_create)
        self.action_settings_btn.clicked.connect(self.handle_re_settings)
        self.action_templates_btn.clicked.connect(self.handle_template)
        self.action_default_btn.clicked.connect(self.handle_set_default_template)
        self.action_random_btn.clicked.connect(self.handle_set_random_template)
        self.image_label.mousePressEvent = self.image_label_click_event

    def setup_filters(self):
        self.pid_input.textChanged.connect(
            lambda: self.apply_column_filter(self.pid_input.text(), 1)
        )
        self.street_input.textChanged.connect(
            lambda: self.apply_column_filter(self.street_input.text(), 5)
        )
        self.price_input.textChanged.connect(
            lambda: self.apply_column_filter(self.price_input.text(), 8)
        )
        self.function_input.textChanged.connect(
            lambda: self.apply_column_filter(self.function_input.text(), 13)
        )
        self.structure_input.textChanged.connect(
            lambda: self.apply_column_filter(self.structure_input.text(), 12)
        )
        self.area_input.textChanged.connect(
            lambda: self.apply_column_filter(self.area_input.text(), 7)
        )

        self.wards_combobox.currentIndexChanged.connect(
            lambda: self.apply_column_filter(
                (
                    re_controller.REWardsController.get_label_vi_staticmethod(
                        self.wards_combobox.currentData()
                    )
                    if self.wards_combobox.currentData()
                    else None
                ),
                4,
            )
        )
        self.categories_combobox.currentIndexChanged.connect(
            lambda: self.apply_column_filter(
                (
                    re_controller.RECategoryController.get_label_vi_staticmethod(
                        self.categories_combobox.currentData()
                    )
                    if self.categories_combobox.currentData()
                    else None
                ),
                6,
            )
        )
        self.options_combobox.currentIndexChanged.connect(
            lambda: self.apply_column_filter(
                (
                    re_controller.REOptionController.get_label_vi_staticmethod(
                        self.options_combobox.currentData()
                    )
                    if self.options_combobox.currentData()
                    else None
                ),
                3,
            )
        )
        self.building_line_s_combobox.currentIndexChanged.connect(
            lambda: self.apply_column_filter(
                (
                    re_controller.REBuildingLineController.get_label_vi_staticmethod(
                        self.building_line_s_combobox
                    )
                    if self.building_line_s_combobox.currentData()
                    else None
                ),
                14,
            )
        )
        self.furniture_s_combobox.currentIndexChanged.connect(
            lambda: self.apply_column_filter(
                (
                    re_controller.REFurnitureController.get_label_vi_staticmethod(
                        self.furniture_s_combobox
                    )
                    if self.furniture_s_combobox.currentData()
                    else None
                ),
                15,
            )
        )
        self.legal_s_combobox.currentIndexChanged.connect(
            lambda: self.apply_column_filter(
                (
                    re_controller.RELegalController.get_label_vi_staticmethod(
                        self.legal_s_combobox
                    )
                    if self.legal_s_combobox.currentData()
                    else None
                ),
                9,
            )
        )

    def _set_comboboxes(self):
        filter_comboboxes = {
            self.wards_combobox: constants.TABLE_RE_SETTINGS_WARDS,
            self.categories_combobox: constants.TABLE_RE_SETTINGS_CATEGORIES,
            self.options_combobox: constants.TABLE_RE_SETTINGS_OPTIONS,
            self.building_line_s_combobox: constants.TABLE_RE_SETTINGS_BUILDING_LINES,
            self.furniture_s_combobox: constants.TABLE_RE_SETTINGS_FURNITURES,
            self.legal_s_combobox: constants.TABLE_RE_SETTINGS_LEGALS,
        }
        for widget, table_name in filter_comboboxes.items():
            self._load_combobox_data(widget, table_name)
        pass

    def _load_combobox_data(self, combobox_widget, table_name, current_data=-1):
        records = BaseController.read_all_staticmethod(
            constants.RE_CONNECTION, table_name
        )
        for record in records:
            record_id = record.get("id", -1)
            record_vi_label = record.get("label_vi", "undefined")
            combobox_widget.addItem(record_vi_label.title(), record_id)
            if current_data == record_id:
                combobox_widget.setCurrentIndex(combobox_widget.count() - 1)

    def set_table(self):
        self.products_table.setModel(self.proxy_model)
        self.products_table.setSortingEnabled(True)
        self.products_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.products_table.customContextMenuRequested.connect(self.show_context_menu)
        self.products_table.setSelectionBehavior(
            self.products_table.SelectionBehavior.SelectRows
        )

    def apply_column_filter(self, filter_text, column_index):
        if filter_text == "Tất cả" or not filter_text:
            self.proxy_model.setFilterFixedString("")
        else:
            self.proxy_model.setFilterFixedString(filter_text)
            self.proxy_model.setFilterKeyColumn(column_index)

    def show_context_menu(self, pos: QPoint):
        global_pos = self.products_table.mapToGlobal(pos)
        menu = QMenu(self.products_table)
        edit_action = QAction("Edit", self)
        delete_action = QAction("Delete", self)

        edit_action.triggered.connect(self.handle_edit)
        delete_action.triggered.connect(self.handle_delete)

        menu.addAction(edit_action)
        menu.addAction(delete_action)

        menu.popup(global_pos)

    def get_selected_ids(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
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

    def handle_create(self):
        new_product = constants.RE_PRODUCT_INIT_VALUE
        new_product["image_paths"] = []
        create_dialog = DialogREProduct(new_product)
        create_dialog.setWindowTitle("Create Product")
        create_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        create_dialog.setFixedSize(create_dialog.size())
        if create_dialog.exec() == QDialog.DialogCode.Accepted:
            self.product_controller.create(create_dialog.fields)

    def handle_edit(self):
        record_ids = self.get_selected_ids()
        if not record_ids:
            return
        record_id = record_ids[0]
        if record_id:
            current_product = self.product_controller.read(record_id, True)
            image_path = self.product_controller.get_images(record_id)
            current_product["image_paths"] = image_path
            edit_dialog = DialogREProduct(current_product)
            edit_dialog.setWindowTitle("Edit Product")
            edit_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            edit_dialog.setFixedSize(edit_dialog.size())
            if edit_dialog.exec() == QDialog.DialogCode.Accepted:
                self.product_controller.update(record_id, edit_dialog.fields)

    def handle_delete(self):
        record_ids = self.get_selected_ids()
        if not record_ids:
            return
        record_id = record_ids[0]
        if record_id:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Are you sure you want to delete this product?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                if record_id is not None:
                    self.product_controller.delete(record_id)
                else:
                    QMessageBox.warning(self, "Warning", "No product selected.")
            else:
                # User clicked No, do nothing
                pass

    def handle_re_settings(self):
        settings_re_dialog = DialogREProductSetting()
        settings_re_dialog.setWindowTitle("RE Settings")
        settings_re_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        settings_re_dialog.setFixedSize(settings_re_dialog.size())
        settings_re_dialog.exec()

    def handle_template(self):
        template_re_dialog = DialogRETemplateSetting()
        template_re_dialog.setWindowTitle("RE Templates")
        template_re_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        template_re_dialog.setFixedSize(template_re_dialog.size())
        template_re_dialog.exec()

    def handle_set_default_template(self):
        record_ids = self.get_selected_ids()
        if not record_ids:
            return
        record_id = record_ids[0]
        if not record_id:
            return
        record_data = self.product_controller.read(record_id, False)
        self.img_paths = self.product_controller.get_images(record_id)
        title_template = re_controller.RETemplateTitleController.get_default_template()
        description_template = (
            re_controller.RETemplateDescriptionController.get_default_template()
        )

        self.detail_text.setPlainText(
            replace_keywords(record_data, title_template).upper()
            + "\n"
            + replace_keywords(record_data, description_template)
            + "\n"
            + init_footer(record_data.get("pid"), record_data.get("updated_at"))
        )
        if len(self.img_paths):
            self.display_image(self.img_paths[0])

    def handle_set_random_template(self):
        record_ids = self.get_selected_ids()
        if not record_ids:
            return
        record_id = record_ids[0]
        if not record_id:
            return
        record_data = self.product_controller.read(record_id, False)
        record_raw_data = self.product_controller.read(record_id, True)
        self.img_paths = self.product_controller.get_images(record_id)
        title_template = re_controller.RETemplateTitleController.get_random_template(
            record_raw_data.get("option_id")
        )
        description_template = (
            re_controller.RETemplateDescriptionController.get_random_template(
                record_raw_data.get("option_id")
            )
        )

        self.detail_text.setPlainText(
            replace_keywords(record_data, title_template).upper()
            + "\n"
            + replace_keywords(record_data, description_template)
            + "\n"
            + init_footer(record_data.get("pid"), record_data.get("updated_at"))
        )
        if len(self.img_paths):
            self.display_image(self.img_paths[0])

    def display_image(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(
                pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.image_label.setText("Failed to load image.")

    def image_label_click_event(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # self.image_clicked.emit()
            if self.img_paths:
                open_file_explorer(self.img_paths[0])
        super().mousePressEvent(event)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from src.database.re_database import initialize_re_db

    app = QApplication([])
    if initialize_re_db():
        page_re = PageRE()
        page_re.show()

    sys.exit(app.exec())
