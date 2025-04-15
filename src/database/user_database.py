import logging
import sys

from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from src.constants import (
    USER_CONNECTION,
    PATH_USER_DB,
    TABLE_USER,
    TABLE_USER_SETTINGS_UDD,
    TABLE_USER_SETTINGS_PROXY,
    USER_SETTING_UDD,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


def initialize_user_db():
    db = QSqlDatabase.addDatabase("QSQLITE", USER_CONNECTION)
    db.setDatabaseName(PATH_USER_DB)
    if not db.open():
        logger.error(f"Error opening database: {db.lastError().text()}")
        return False
    query = QSqlQuery(db)
    query.exec("PRAGMA foreign_keys = ON;")
    try:
        if not _create_tables(db):
            return False
        if not _seed_data(db, TABLE_USER_SETTINGS_UDD, USER_SETTING_UDD):
            return False
        return True
    except Exception as e:
        if db.isOpen():
            db.rollback()
        logger.error(f"Database initialization failed: {str(e)}")
        return False


def _create_tables(db: QSqlDatabase):
    sql_user_table = f"""
CREATE TABLE IF NOT EXISTS {TABLE_USER} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status INTEGER,
    uid TEXT,
    username TEXT,
    password TEXT,
    two_fa TEXT,
    email TEXT,
    email_password TEXT,
    phone_number TEXT,
    note TEXT,
    type TEXT,
    user_group TEXT,
    mobile_ua TEXT,
    desktop_ua TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""
    sql_udd = f"""
CREATE TABLE IF NOT EXISTS {TABLE_USER_SETTINGS_UDD} (
id INTEGER PRIMARY KEY AUTOINCREMENT,
value TEXT UNIQUE NOT NULL,
is_selected INTEGER,
updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""
    sql_proxy = f"""
CREATE TABLE IF NOT EXISTS {TABLE_USER_SETTINGS_PROXY} (
id INTEGER PRIMARY KEY AUTOINCREMENT,
value TEXT UNIQUE NOT NULL,
updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""

    try:
        if not db.transaction():
            logger.error("Could not start transaction.")
            return False
        if not _create_table(TABLE_USER, db, sql_user_table):
            db.rollback()
            return False
        if not _create_table(TABLE_USER_SETTINGS_UDD, db, sql_udd):
            db.rollback()
            return False
        if not _create_table(TABLE_USER_SETTINGS_PROXY, db, sql_proxy):
            db.rollback()
            return False
        if not db.commit():
            logger.error("Commit failed")
            return False
        return True
    except Exception as e:
        if db.isOpen():
            db.rollback()
        logger.error(f"Database creating failed: {str(e)}")
        return False


def _create_table(table_name, db, sql):
    query = QSqlQuery(db)
    if not query.exec(sql):
        logger.error(
            f"Error creating table '{table_name}': {query.lastError().text()}")
        return False
    return True


def _seed_data(db: QSqlDatabase, table_name: str, payload: list):
    if not db.transaction():
        logger.error(
            f"Failed to start transaction for seeding table '{table_name}'.")
        return False
    query = QSqlQuery(db)

    # Lấy thông tin cột của bảng
    record = db.record(table_name)
    columns = [record.fieldName(i) for i in range(record.count())]

    # Loại bỏ cột id (autoincrement) nếu có
    if "id" in columns:
        columns.remove("id")
    if "created_at" in columns:
        columns.remove("created_at")
    if "updated_at" in columns:
        columns.remove("updated_at")

    # Tạo placeholder cho các giá trị
    placeholders = ", ".join(["?"] * len(columns))
    columns_str = ", ".join(columns)
    sql = f"INSERT OR IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    query.prepare(sql)
    for row_data in payload:
        if isinstance(row_data, dict):
            values = [row_data.get(col) for col in columns]
            for value in values:
                query.addBindValue(value)
            if not query.exec():
                logger.error(
                    f"Error seeding data into '{table_name}': {query.lastError().text()} - Data: {row_data}"
                )
                db.rollback()
                return False
        elif isinstance(row_data, (list, tuple)):
            if len(row_data) != len(columns):
                logger.error(
                    f"Number of values in row does not match number of columns in '{table_name}': {row_data} vs {columns}"
                )
                db.rollback()
                return False
            for value in row_data:
                query.addBindValue(value)
            if not query.exec():
                logger.error(
                    f"Error seeding data into '{table_name}': {query.lastError().text()} - Data: {row_data}"
                )
                db.rollback()
                return False
        else:
            logger.error(
                f"Invalid data format for seeding '{table_name}': {row_data}")
            db.rollback()
            return False
    query.clear()
    if not db.commit():
        logger.error(
            f"Failed to commit transaction for seeding table '{table_name}'.")
        return False
    return True
