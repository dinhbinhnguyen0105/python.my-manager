# src/views/re/page_re.py

from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtCore import Qt, QPoint, QSortFilterProxyModel, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QWidget, QMenu, QDialog

from src import constants
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

        self.setup_ui()
        self.setup_events()
        self.setup_filters()

    def setup_ui(self):
        self._set_comboboxes()
        self.set_table()

    def setup_events(self):

        self.action_create_btn.clicked.connect(self.handle_create)

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
        id = self.get_selected_ids()[0]
        if id:
            current_product = self.product_controller.read(id, True)
            image_path = self.product_controller.get_images(id)
            current_product["image_paths"] = image_path
            edit_dialog = DialogREProduct(current_product)
            edit_dialog.setWindowTitle("Edit Product")
            edit_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            edit_dialog.setFixedSize(edit_dialog.size())
            if edit_dialog.exec() == QDialog.DialogCode.Accepted:
                self.product_controller.create(edit_dialog.fields)

    def handle_delete(self):
        id = self.get_selected_ids()[0]
        if id:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Are you sure you want to delete this product?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                if id is not None:
                    self.product_controller.delete(id)
                else:
                    QMessageBox.warning(self, "Warning", "No product selected.")
            else:
                # User clicked No, do nothing
                pass


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from src.database.re_database import initialize_re_db

    app = QApplication([])
    if initialize_re_db():
        page_re = PageRE()
        page_re.show()

    sys.exit(app.exec())
