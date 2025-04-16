from PyQt6.QtSql import QSqlTableModel, QSqlDatabase
from PyQt6.QtCore import Qt
from src import constants


class BaseUserModel(QSqlTableModel):
    def __init__(self, table_name, parent=None):
        super().__init__(parent, QSqlDatabase.database(constants.USER_CONNECTION))
        self.setTable(table_name)
        self.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.select()

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


class UserModel(BaseUserModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_USER, parent)


class UserUDDModel(BaseUserModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_USER_SETTINGS_UDD, parent)


class UserProxyModel(BaseUserModel):
    def __init__(self, parent=None):
        super().__init__(constants.TABLE_USER_SETTINGS_PROXY, parent)
