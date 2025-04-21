# src/models/re_model.py
from PyQt6.QtSql import (
    QSqlRelationalTableModel,
    QSqlRelation,
    QSqlTableModel,
    QSqlDatabase,
)
from PyQt6.QtCore import Qt
from src import constants


class REProductModel(QSqlRelationalTableModel):
    def __init__(self, parent=None):
        super().__init__(parent, QSqlDatabase.database(constants.RE_CONNECTION))
        self.setTable(constants.TABLE_RE)
        self.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnManualSubmit)
        self._column_headers = {
            self.fieldIndex("pid"): "pid".upper(),
            self.fieldIndex("ward_id"): "ward".title(),
            self.fieldIndex("street"): "street".title(),
            self.fieldIndex("status_id"): "status".title(),
            self.fieldIndex("province_id"): "province".title(),
            self.fieldIndex("district_id"): "district".title(),
            self.fieldIndex("option_id"): "option".title(),
            self.fieldIndex("category_id"): "category".title(),
            self.fieldIndex("building_line_id"): "building_line".title(),
            self.fieldIndex("furniture_id"): "furniture".title(),
            self.fieldIndex("legal_id"): "legal".title(),
            self.fieldIndex("area"): "area".title(),
            self.fieldIndex("structure"): "structure".title(),
            self.fieldIndex("function"): "function".title(),
            self.fieldIndex("description"): "description".title(),
            self.fieldIndex("price"): "price".title(),
            "relation-status_id": "status".title(),
            "relation-option_id": "option".title(),
            "relation-category_id": "category".title(),
            "relation-province_id": "province".title(),
            "relation-district_id": "district".title(),
            "relation-ward_id": "ward".title(),
            "relation-building_line_id": "building_line".title(),
            "relation-legal_id": "legal".title(),
            "relation-furniture_id": "furniture".title(),
        }
        self._set_relations()

    def _set_relations(self):
        self.setRelation(
            self.fieldIndex("status_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_STATUSES, "id", "label_vi"),
        )
        self.setRelation(
            self.fieldIndex("province_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_PROVINCES, "id", "label_vi"),
        )
        self.setRelation(
            self.fieldIndex("district_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_DISTRICTS, "id", "label_vi"),
        )
        self.setRelation(
            self.fieldIndex("ward_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_WARDS, "id", "label_vi"),
        )
        self.setRelation(
            self.fieldIndex("option_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_OPTIONS, "id", "label_vi"),
        )
        self.setRelation(
            self.fieldIndex("category_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_CATEGORIES, "id", "label_vi"),
        )
        self.setRelation(
            self.fieldIndex("building_line_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_BUILDING_LINES, "id", "label_vi"),
        )
        self.setRelation(
            self.fieldIndex("legal_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_LEGALS, "id", "label_vi"),
        )
        self.setRelation(
            self.fieldIndex("furniture_id"),
            QSqlRelation(constants.TABLE_RE_SETTINGS_FURNITURES, "id", "label_vi"),
        )

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            # Tiêu đề cho các cột dữ liệu trực tiếp từ bảng re_products
            if section in self._column_headers:
                return self._column_headers[section]

            # Tiêu đề cho các cột quan hệ (hiển thị giá trị từ bảng liên kết)
            for field_name in [
                "status_id",
                "province_id",
                "district_id",
                "ward_id",
                "option_id",
                "category_id",
                "building_line_id",
                "legal_id",
                "furniture_id",
            ]:
                relation_index = self.fieldIndex(field_name)
                if self.relation(relation_index).isValid():
                    if (
                        self.relation(relation_index).displayColumn() == 2
                        and self.relation(relation_index).indexInRelatedTable()
                        == section - self.columnCount()
                    ):
                        return self._column_headers.get(
                            f"relation-{field_name}",
                            field_name.replace("_id", "").title(),
                        )
            return super().headerData(section, orientation, role)
        return super().headerData(section, orientation, role)

    def get_record_ids(self, rows):
        ids = []
        for row in rows:
            if 0 <= row < self.rowCount():
                index = self.index(row, self.fieldIndex("id"))
                ids.append(self.data(index))
        return ids


class BaseSettingModel(QSqlTableModel):
    def __init__(self, table_name, parent=None):
        super().__init__(parent, QSqlDatabase.database(constants.RE_CONNECTION))
        self.setTable(table_name)
        self.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        if not self.select():
            error_msg = f"Error selecting data from table '{table_name}': {self.lastError().text()}"
            print(error_msg)

    def flags(self, index):
        return (
            Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsEditable
        )

    def get_record_ids(self, rows):
        ids = []
        for row in rows:
            if 0 <= row < self.rowCount():
                index = self.index(row, self.fieldIndex("id"))
                ids.append(self.data(index))
        return ids


class REStatusModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_STATUSES, parent)


class REProvinceModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_PROVINCES, parent)


class REDistrictModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_DISTRICTS, parent)


class REWardModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_WARDS, parent)


class REOptionModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_OPTIONS, parent)


class RECategoryModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_CATEGORIES, parent)


class REBuildingLineModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_BUILDING_LINES, parent)


class REFurnitureModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_FURNITURES, parent)


class RELegalModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_LEGALS, parent)


class REImageDirModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_IMG_DIRS, parent)


class RETitleModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_TITLE, parent)


class REDescriptionModel(BaseSettingModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_RE_SETTINGS_DESCRIPTION, parent)
