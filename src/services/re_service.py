# src/services/re_service.py
import logging
import sys
import os
import uuid
from contextlib import contextmanager
from PyQt6.QtSql import QSqlQuery, QSqlDatabase
from src import constants
from src.services.base_service import BaseService
from src.utils import file_handler

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


def record_to_dict(query: QSqlQuery) -> dict:
    rec = query.record()
    return {rec.fieldName(i): query.value(i) for i in range(rec.count())}


def exec_query(db, query):
    sql = query.lastQuery()
    if not query.exec():
        logger.info("Query bound values: %s", query.boundValues())
        logger.error(
            "Error executing SQL query: %s\nERROR message: %s",
            sql,
            query.lastError().text(),
        )
        db.rollback()
        return False
    return True


def fetch_single_result(db, sql, bindings):
    query = QSqlQuery(db)
    if not query.prepare(sql):
        logger.error(query.lastError().text())
        return None
    for key, value in bindings.items():
        query.bindValue(f":{key}", value)
    if not exec_query(db, query):
        return None
    if query.next():
        return record_to_dict(query)
    return None


def is_affected(query):
    rows_affected = query.numRowsAffected()
    if rows_affected > 0:
        logger.info("Updated %d record(s).", rows_affected)
        return True
    else:
        sql = query.lastQuery()
        logger.info("No records were updated. Query: %s", sql)
        return False


@contextmanager
def db_transaction(db):
    if not db.transaction():
        logger.error("Failed to start transaction.")
        yield False
        return
    try:
        yield True
    except Exception as e:
        db.rollback()
        logger.error("Transaction error: %s", e)
        raise
    else:
        if not db.commit():
            logger.error("Failed to commit transaction.")
            db.rollback()


class REProductService:
    @staticmethod
    def get_columns():
        return [
            "id",
            "pid",
            "street",
            "area",
            "structure",
            "function",
            "description",
            "price",
            "status_id",
            "province_id",
            "district_id",
            "ward_id",
            "option_id",
            "category_id",
            "building_line_id",
            "furniture_id",
            "legal_id",
            "created_at",
            "updated_at",
        ]

    @staticmethod
    def read(record_id):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        sql = f"""
SELECT 
    main.id,
    main.pid,
    main.street,
    main.area,
    main.structure,
    main.function,
    main.description,
    main.price,
    main.updated_at,
    statuses.label_vi AS status,
    provinces.label_vi AS province,
    districts.label_vi AS district,
    wards.label_vi AS ward,
    options.label_vi AS option,
    categories.label_vi AS category,
    building_line_s.label_vi AS building_line,
    furniture_s.label_vi AS furniture,
    legal_s.label_vi AS legal,
    main.created_at,
    main.updated_at
FROM {constants.TABLE_RE} main
JOIN {constants.TABLE_RE_SETTINGS_STATUSES} statuses ON main.status_id = statuses.id
JOIN {constants.TABLE_RE_SETTINGS_PROVINCES} provinces ON main.province_id = provinces.id
JOIN {constants.TABLE_RE_SETTINGS_DISTRICTS} districts ON main.district_id = districts.id
JOIN {constants.TABLE_RE_SETTINGS_WARDS} wards ON main.ward_id = wards.id
JOIN {constants.TABLE_RE_SETTINGS_OPTIONS} options ON main.option_id = options.id
JOIN {constants.TABLE_RE_SETTINGS_CATEGORIES} categories ON main.category_id = categories.id
JOIN {constants.TABLE_RE_SETTINGS_BUILDING_LINES} building_line_s ON main.building_line_id = building_line_s.id
JOIN {constants.TABLE_RE_SETTINGS_FURNITURES} furniture_s ON main.furniture_id = furniture_s.id
JOIN {constants.TABLE_RE_SETTINGS_LEGALS} legal_s ON main.legal_id = legal_s.id
WHERE main.id = :id
"""
        return fetch_single_result(db, sql, {"id": record_id})

    @staticmethod
    def read_by_pid(pid):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        sql = f"""
SELECT 
    main.id,
    main.pid,
    main.street,
    main.area,
    main.structure,
    main.function,
    main.description,
    main.price,
    main.updated_at,
    statuses.label_vi AS status,
    provinces.label_vi AS province,
    districts.label_vi AS district,
    wards.label_vi AS ward,
    options.label_vi AS option,
    categories.label_vi AS category,
    building_line_s.label_vi AS building_line,
    furniture_s.label_vi AS furniture,
    legal_s.label_vi AS legal,
    main.created_at,
    main.updated_at
FROM {constants.TABLE_RE} main
JOIN {constants.TABLE_RE_SETTINGS_STATUSES} statuses ON main.status_id = statuses.id
JOIN {constants.TABLE_RE_SETTINGS_PROVINCES} provinces ON main.province_id = provinces.id
JOIN {constants.TABLE_RE_SETTINGS_DISTRICTS} districts ON main.district_id = districts.id
JOIN {constants.TABLE_RE_SETTINGS_WARDS} wards ON main.ward_id = wards.id
JOIN {constants.TABLE_RE_SETTINGS_OPTIONS} options ON main.option_id = options.id
JOIN {constants.TABLE_RE_SETTINGS_CATEGORIES} categories ON main.category_id = categories.id
JOIN {constants.TABLE_RE_SETTINGS_BUILDING_LINES} building_line_s ON main.building_line_id = building_line_s.id
JOIN {constants.TABLE_RE_SETTINGS_FURNITURES} furniture_s ON main.furniture_id = furniture_s.id
JOIN {constants.TABLE_RE_SETTINGS_LEGALS} legal_s ON main.legal_id = legal_s.id
WHERE main.pid = :pid
"""
        return fetch_single_result(db, sql, {"pid": pid})

    @staticmethod
    def read_raw(record_id):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        sql = f"""
SELECT 
    main.id,
    main.pid,
    main.street,
    main.area,
    main.structure,
    main.function,
    main.description,
    main.price,
    main.updated_at,
    main.status_id,
    main.province_id,
    main.district_id,
    main.ward_id,
    main.option_id,
    main.category_id,
    main.building_line_id,
    main.furniture_id,
    main.legal_id,
    main.created_at,
    main.updated_at
FROM {constants.TABLE_RE} main
WHERE main.id = :id
"""
        return fetch_single_result(db, sql, {"id": record_id})

    @staticmethod
    def read_all():
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        sql = f"""
SELECT 
    main.id,
    main.pid,
    main.street,
    main.area,
    main.structure,
    main.function,
    main.description,
    main.price,
    main.updated_at,
    statuses.label_vi AS status,
    provinces.label_vi AS province,
    districts.label_vi AS district,
    wards.label_vi AS ward,
    options.label_vi AS option,
    categories.label_vi AS category,
    building_line_s.label_vi AS building_line,
    furniture_s.label_vi AS furniture,
    legal_s.label_vi AS legal,
    main.created_at,
    main.updated_at
FROM {constants.TABLE_RE} main
JOIN {constants.TABLE_RE_SETTINGS_STATUSES} statuses ON main.status_id = statuses.id
JOIN {constants.TABLE_RE_SETTINGS_PROVINCES} provinces ON main.province_id = provinces.id
JOIN {constants.TABLE_RE_SETTINGS_DISTRICTS} districts ON main.district_id = districts.id
JOIN {constants.TABLE_RE_SETTINGS_WARDS} wards ON main.ward_id = wards.id
JOIN {constants.TABLE_RE_SETTINGS_OPTIONS} options ON main.option_id = options.id
JOIN {constants.TABLE_RE_SETTINGS_CATEGORIES} categories ON main.category_id = categories.id
JOIN {constants.TABLE_RE_SETTINGS_BUILDING_LINES} building_line_s ON main.building_line_id = building_line_s.id
JOIN {constants.TABLE_RE_SETTINGS_FURNITURES} furniture_s ON main.furniture_id = furniture_s.id
JOIN {constants.TABLE_RE_SETTINGS_LEGALS} legal_s ON main.legal_id = legal_s.id
"""
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return []
        if not exec_query(db, query):
            return []
        results = []
        while query.next():
            results.append(record_to_dict(query))
        return results

    @staticmethod
    def create(payload):
        print("payload: ", payload)
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        valid_columns = [k for k in payload if k in REProductService.get_columns()]
        if not valid_columns:
            logger.error("No valid columns provided for create.")
            return False
        columns = ", ".join(valid_columns)
        placeholders = ", ".join([f":{k}" for k in valid_columns])
        sql = f"INSERT INTO {constants.TABLE_RE} ({columns}) VALUES ({placeholders})"
        query = QSqlQuery(db)
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        for key in valid_columns:
            query.bindValue(f":{key}", payload[key])

        with db_transaction(db) as ok:
            if not ok:
                return False
            img_record = REImageDirService.get_selected_img_dir()
            if not img_record:
                logger.error("Image dir path is undefined.")
                return False
            if not exec_query(db, query):
                return False
            is_affected(query)

            current_id = None
            current_id_query = QSqlQuery(db)
            if current_id_query.exec("SELECT last_insert_rowid();"):
                if current_id_query.next():
                    current_id = current_id_query.value(0)
            else:
                logger.error(
                    "Error get the ID of the latest record: %s",
                    current_id_query.lastError().text(),
                )
                return False

            image_paths = payload.get("image_paths")
            image_dir = os.path.join(img_record.get("value"), str(current_id))
            if not file_handler.copy_files(image_paths, image_dir, current_id):
                return False

        return True

    @staticmethod
    def update(record_id, payload):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        valid_columns = [
            k for k in REProductService.get_columns() if k != "id" and k in payload
        ]
        if not valid_columns:
            logger.error("No valid columns provided for update.")
            return False
        set_clause = ", ".join([f"{k} = :{k}" for k in valid_columns])
        sql = (
            f"UPDATE {constants.TABLE_RE} SET {set_clause}, "
            "updated_at = (strftime('%Y-%m-%d %H:%M:%S', 'now')) "
            "WHERE id = :id"
        )
        query = QSqlQuery(db)
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        for key in valid_columns:
            query.bindValue(f":{key}", payload[key])
        query.bindValue(":id", record_id)
        with db_transaction(db) as ok:
            if not ok:
                return False
            if not exec_query(db, query):
                return False
            is_affected(query)
        return True

    @staticmethod
    def delete(record_id):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        sql = f"DELETE FROM {constants.TABLE_RE} WHERE id = :id"
        query = QSqlQuery(db)
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":id", record_id)
        with db_transaction(db) as ok:
            if not ok:
                return False
            if not exec_query(db, query):
                return False
            img_record = REImageDirService.get_selected_img_dir()
            if not img_record:
                logger.error("Image dir path is undefined.")
                db.rollback()
                return False
            image_dir = os.path.join(img_record.get("value"), str(record_id))
            file_handler.delete_dir(image_dir)
            is_affected(query)
        return True

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False

    @staticmethod
    def is_pid_existed(pid):
        return REProductService.is_value_existed({"pid": pid})

    @staticmethod
    def get_images(record_id):
        img_dir_service = REImageDirService()
        img_dir_record = img_dir_service.get_selected_img_dir()
        return file_handler.get_images_in_directory(
            os.path.abspath(os.path.join(img_dir_record.get("value"), str(record_id)))
        )

    @staticmethod
    def get_random_product(option_id):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        sql = f"""
SELECT 
    main.id,
    main.pid,
    main.street,
    main.area,
    main.structure,
    main.function,
    main.description,
    main.price,
    main.updated_at,
    statuses.label_vi AS status,
    provinces.label_vi AS province,
    districts.label_vi AS district,
    wards.label_vi AS ward,
    options.label_vi AS option,
    categories.label_vi AS category,
    building_line_s.label_vi AS building_line,
    furniture_s.label_vi AS furniture,
    legal_s.label_vi AS legal,
    main.created_at,
    main.updated_at
FROM {constants.TABLE_RE} main
JOIN {constants.TABLE_RE_SETTINGS_STATUSES} statuses ON main.status_id = statuses.id
JOIN {constants.TABLE_RE_SETTINGS_PROVINCES} provinces ON main.province_id = provinces.id
JOIN {constants.TABLE_RE_SETTINGS_DISTRICTS} districts ON main.district_id = districts.id
JOIN {constants.TABLE_RE_SETTINGS_WARDS} wards ON main.ward_id = wards.id
JOIN {constants.TABLE_RE_SETTINGS_OPTIONS} options ON main.option_id = options.id
JOIN {constants.TABLE_RE_SETTINGS_CATEGORIES} categories ON main.category_id = categories.id
JOIN {constants.TABLE_RE_SETTINGS_BUILDING_LINES} building_line_s ON main.building_line_id = building_line_s.id
JOIN {constants.TABLE_RE_SETTINGS_FURNITURES} furniture_s ON main.furniture_id = furniture_s.id
JOIN {constants.TABLE_RE_SETTINGS_LEGALS} legal_s ON main.legal_id = legal_s.id
WHERE option_id = {option_id} ORDER BY RANDOM() LIMIT 1
"""
        return fetch_single_result(db, sql, {"option_id": option_id})


class REImageDirService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_IMG_DIRS
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "value", "is_selected", "created_at", "updated_at"]

    @classmethod
    def get_selected_img_dir(cls):
        db = QSqlDatabase.database(cls.CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE is_selected = :is_selected"
        if not query.prepare(sql):
            return None
        query.bindValue(":is_selected", 1)
        if not exec_query(db, query):
            return None
        if query.next():
            return record_to_dict(query)
        return None

    @classmethod
    def set_selected_img_dir(cls, record_id):
        db = QSqlDatabase.database(cls.CONNECTION)
        with db_transaction(db) as ok:
            if not ok:
                return False
            query = QSqlQuery(db)
            sql_reset = f"UPDATE {cls.TABLE_NAME} SET is_selected = 0"
            if not query.prepare(sql_reset) or not query.exec():
                return False
            sql_set = f"UPDATE {cls.TABLE_NAME} SET is_selected = 1 WHERE id = :id"
            if not query.prepare(sql_set):
                return False
            query.bindValue(":id", record_id)
            if not exec_query(db, query):
                return None
        return True

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_IMG_DIRS} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class RETemplateTitleService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_TITLE
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def create(cls, payload):
        payload.setdefault("tid", cls.generate_tid())
        return super().create(payload)

    @classmethod
    def get_columns(cls):
        return ["id", "tid", "option_id", "value", "created_at", "updated_at"]

    @classmethod
    def is_tid_existed(cls, tid):
        return cls.is_value_existed({"tid": tid})

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_TITLE} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False

    @classmethod
    def generate_tid(cls):
        try:
            while True:
                uuid_str = str(uuid.uuid4())
                tid = "template.title." + uuid_str.replace("-", "")[:8]
                if not cls.is_value_existed({"pid": tid}):
                    return tid
                else:
                    continue
        except Exception as e:
            logger.error(str(e))
            raise Exception("Failed to generate PID.")

    @staticmethod
    def get_random_template(option_id):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT value FROM {constants.TABLE_RE_SETTINGS_TITLE} WHERE option_id = {option_id} ORDER BY RANDOM() LIMIT 1"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return None
        if not exec_query(db, query):
            return None
        if query.next():
            return query.value(0)
        return None

    @staticmethod
    def get_default_template():
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT value FROM {constants.TABLE_RE_SETTINGS_TITLE} WHERE id = 1"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return None
        if not exec_query(db, query):
            return None
        if query.next():
            return query.value(0)
        return None


class RETemplateDescriptionService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_DESCRIPTION
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def create(cls, payload):
        payload.setdefault("tid", cls.generate_tid())
        print(payload)
        return super().create(payload)

    @classmethod
    def get_columns(cls):
        return ["id", "tid", "option_id", "value", "created_at", "updated_at"]

    @classmethod
    def is_tid_existed(cls, tid):
        return cls.is_value_existed({"tid": tid})

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_DESCRIPTION} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False

    @classmethod
    def generate_tid(cls):
        try:
            while True:
                uuid_str = str(uuid.uuid4())
                tid = "template.description." + uuid_str.replace("-", "")[:8]
                if not cls.is_value_existed({"pid": tid}):
                    return tid
                else:
                    continue
        except Exception as e:
            logger.error(str(e))
            raise Exception("Failed to generate PID.")

    @staticmethod
    def get_random_template(option_id):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT value FROM {constants.TABLE_RE_SETTINGS_DESCRIPTION} WHERE option_id = {option_id} ORDER BY RANDOM() LIMIT 1"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return None
        if not exec_query(db, query):
            return None
        if query.next():
            return query.value(0)
        return None

    @staticmethod
    def get_default_template():
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        sql = (
            f"SELECT value FROM {constants.TABLE_RE_SETTINGS_DESCRIPTION} WHERE id = 1"
        )
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return None
        if not exec_query(db, query):
            return None
        if query.next():
            return query.value(0)
        return None


class REStatusService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_STATUSES
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_STATUSES} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class REProvinceService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_PROVINCES
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_PROVINCES} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class REDistrictService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_DISTRICTS
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_DISTRICTS} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class REWardsService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_WARDS
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_WARDS} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class REOptionService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_OPTIONS
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_OPTIONS} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class RECategoryService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_CATEGORIES
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_CATEGORIES} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class REBuildingLinesService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_BUILDING_LINES
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_BUILDING_LINES} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class RELegalsService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_LEGALS
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_LEGALS} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False


class REFurnitureService(BaseService):
    TABLE_NAME = constants.TABLE_RE_SETTINGS_FURNITURES
    CONNECTION = constants.RE_CONNECTION

    @classmethod
    def get_columns(cls):
        return ["id", "label_vi", "label_en", "value", "created_at", "updated_at"]

    @staticmethod
    def is_value_existed(condition):

        db = QSqlDatabase.database(constants.RE_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_RE_SETTINGS_FURNITURES} WHERE {key} = :value"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        query.bindValue(":value", value)
        if not exec_query(db, query):
            return False
        if query.next():
            return query.value(0) > 0
        return False
