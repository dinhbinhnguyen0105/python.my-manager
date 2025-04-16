# src/models/re_database.py
import logging
import sys

from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from src import constants

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

base_settings_tables_data = {
    constants.TABLE_RE_SETTINGS_STATUSES: constants.RE_SETTING_STATUSES,
    constants.TABLE_RE_SETTINGS_PROVINCES: constants.RE_SETTING_PROVINCES,
    constants.TABLE_RE_SETTINGS_DISTRICTS: constants.RE_SETTING_DISTRICTS,
    constants.TABLE_RE_SETTINGS_WARDS: constants.RE_SETTING_WARDS,
    constants.TABLE_RE_SETTINGS_OPTIONS: constants.RE_SETTING_OPTIONS,
    constants.TABLE_RE_SETTINGS_CATEGORIES: constants.RE_SETTING_CATEGORIES,
    constants.TABLE_RE_SETTINGS_BUILDING_LINES: constants.RE_SETTING_BUILDING_LINES,
    constants.TABLE_RE_SETTINGS_FURNITURES: constants.RE_SETTING_FURNITURES,
    constants.TABLE_RE_SETTINGS_LEGALS: constants.RE_SETTING_LEGALS,
    # constants.TABLE_RE_SETTINGS_IMG_DIRS: constants.RE_SETTING_IMG_DIRS,
}
templates_tables_data = {
    constants.TABLE_RE_SETTINGS_TITLE: constants.RE_SETTING_TEMPLATE_TITLES,
    constants.TABLE_RE_SETTINGS_DESCRIPTION: constants.RE_SETTING_TEMPLATE_DESCRIPTIONS,
}
img_dir_tables_data = {
    constants.TABLE_RE_SETTINGS_IMG_DIRS: constants.RE_SETTING_IMG_DIRS
}


def initialize_re_db():
    db = QSqlDatabase.addDatabase("QSQLITE", constants.RE_CONNECTION)
    db.setDatabaseName(constants.PATH_RE_DB)
    if not db.open():
        logger.error(f"Error opening database: {db.lastError().text()}")
        return False
    query = QSqlQuery(db)
    query.exec("PRAGMA foreign_keys = ON;")
    try:
        if not _create_tables(db):
            return False
        if not _seed_initial_data(db):
            return False
        return True
    except Exception as e:
        if db.isOpen():
            db.rollback()
        logger.error(f"Database initialization failed: {str(e)}")
        return False


def _create_tables(db):
    try:
        if not db.transaction():
            logger.error("Could not start transaction.")
            return False

        for table_name in base_settings_tables_data:
            base_settings_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label_vi TEXT,
    label_en TEXT,
    value TEXT UNIQUE NOT NULL,
    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
    )
    """
            if not _create_table(table_name, db, base_settings_sql):
                db.rollback()
                return False

        for table_name in templates_tables_data:
            template_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tid TEXT UNIQUE,
        option_id INTEGER,
        value TEXT,
        updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
        FOREIGN KEY (option_id) REFERENCES {constants.TABLE_RE_SETTINGS_OPTIONS}(id)
    )
    """
            if not _create_table(table_name, db, template_sql):
                db.rollback()
                return False
        image_dir_sql = f"""
    CREATE TABLE IF NOT EXISTS {constants.TABLE_RE_SETTINGS_IMG_DIRS} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        value TEXT UNIQUE NOT NULL,
        is_selected INTEGER,
        updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
    )
    """
        if not _create_table(constants.TABLE_RE_SETTINGS_IMG_DIRS, db, image_dir_sql):
            db.rollback()
            return False
        product_sql = f"""
    CREATE TABLE IF NOT EXISTS {constants.TABLE_RE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pid TEXT UNIQUE NOT NULL,
        status_id INTEGER,
        option_id INTEGER,
        ward_id INTEGER,
        street TEXT,
        category_id INTEGER,
        area REAL,
        price REAL,
        legal_id INTEGER,
        province_id INTEGER,
        district_id INTEGER,
        structure REAL,
        function TEXT,
        building_line_id INTEGER,
        furniture_id INTEGER,
        description TEXT,
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
        updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
        FOREIGN KEY (status_id) REFERENCES {constants.TABLE_RE_SETTINGS_STATUSES}(id),
        FOREIGN KEY (province_id) REFERENCES {constants.TABLE_RE_SETTINGS_PROVINCES}(id),
        FOREIGN KEY (district_id) REFERENCES {constants.TABLE_RE_SETTINGS_DISTRICTS}(id),
        FOREIGN KEY (ward_id) REFERENCES {constants.TABLE_RE_SETTINGS_WARDS}(id),
        FOREIGN KEY (option_id) REFERENCES {constants.TABLE_RE_SETTINGS_OPTIONS}(id),
        FOREIGN KEY (category_id) REFERENCES {constants.TABLE_RE_SETTINGS_CATEGORIES}(id),
        FOREIGN KEY (building_line_id) REFERENCES {constants.TABLE_RE_SETTINGS_BUILDING_LINES}(id),
        FOREIGN KEY (furniture_id) REFERENCES {constants.TABLE_RE_SETTINGS_FURNITURES}(id),
        FOREIGN KEY (legal_id) REFERENCES {constants.TABLE_RE_SETTINGS_LEGALS}(id)
    )
    """
        if not _create_table(constants.TABLE_RE, db, product_sql):
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


def _seed_initial_data(db: QSqlDatabase):
    for table_name, data_list in base_settings_tables_data.items():
        if not _seed_data(db, table_name, data_list):
            return False
    for table_name, data_list in templates_tables_data.items():
        if not _seed_data(db, table_name, data_list):
            return False
    for table_name, data_list in img_dir_tables_data.items():
        if not _seed_data(db, table_name, data_list):
            return False
    return True


def _seed_data(db: QSqlDatabase, table_name: str, payload: list):
    if not db.transaction():
        logger.error(f"Failed to start transaction for seeding table '{table_name}'.")
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
            # Đảm bảo thứ tự giá trị tương ứng với thứ tự cột
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
            logger.error(f"Invalid data format for seeding '{table_name}': {row_data}")
            db.rollback()
            return False
    # query.clear()
    # Chuyển commit ra khỏi vòng lặp dữ liệu
    if not db.commit():
        logger.error(f"Failed to commit transaction for seeding table '{table_name}'.")
        return False
    return True


def _create_table(table_name, db, sql):
    query = QSqlQuery(db)
    if not query.exec(sql):
        logger.error(f"Error creating table '{table_name}': {query.lastError().text()}")
        return False
    return True
