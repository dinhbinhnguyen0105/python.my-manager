# src/services/user_service.py
import logging
import sys
import os

from contextlib import contextmanager
from fake_useragent import UserAgent
from PyQt6.QtSql import QSqlQuery, QSqlDatabase
from src import constants
from src.utils import file_handler
from src.services.base_service import BaseService

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


class UserService:
    @staticmethod
    def get_columns():
        return [
            "id",
            "status",
            "uid",
            "username",
            "password",
            "two_fa",
            "email",
            "email_password",
            "phone_number",
            "note",
            "type",
            "user_group",
            "mobile_ua",
            "desktop_ua",
            "created_at",
            "updated_at",
        ]

    @staticmethod
    def read(record_id):
        db = QSqlDatabase.database(constants.USER_CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT * FROM {constants.TABLE_USER} WHERE id = :id"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return None
        query.bindValue(":id", record_id)
        if not exec_query(db, query):
            return None
        if query.next():
            return record_to_dict(query)
        return None

    @staticmethod
    def read_all():
        db = QSqlDatabase.database(constants.USER_CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT * FROM {constants.TABLE_USER}"
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
        ua_desktop_controller = UserAgent(
            os="Mac OS X",
        )
        ua_mobile_controller = UserAgent(
            os="iOS",
        )
        payload["mobile_ua"] = ua_mobile_controller.random
        payload["desktop_ua"] = ua_desktop_controller.random
        db = QSqlDatabase.database(constants.USER_CONNECTION)
        valid_columns = [col for col in UserService.get_columns() if col in payload]
        if not valid_columns:
            logger.error("No valid columns provided for create.")
            return False
        columns = ", ".join(valid_columns)
        placeholders = ", ".join([f":{col}" for col in valid_columns])
        sql = f"INSERT INTO {constants.TABLE_USER} ({columns}) VALUES ({placeholders})"
        query = QSqlQuery(db)
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        for col in valid_columns:
            query.bindValue(f":{col}", payload[col])
        with db_transaction(db) as ok:
            if not ok:
                return False
            if not exec_query(db, query):
                return False
        return True

    @staticmethod
    def update(record_id, payload):
        db = QSqlDatabase.database(constants.USER_CONNECTION)
        valid_columns = [
            col for col in UserService.get_columns() if col != "id" and col in payload
        ]
        if not valid_columns:
            logger.error("No valid columns provided for update.")
            return False
        set_clause = ", ".join([f"{col} = :{col}" for col in valid_columns])
        sql = (
            f"UPDATE {constants.TABLE_USER} SET {set_clause}, "
            "updated_at = (strftime('%Y-%m-%d %H:%M:%S', 'now')) "
            "WHERE id = :id"
        )
        query = QSqlQuery(db)
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return False
        for col in valid_columns:
            query.bindValue(f":{col}", payload[col])
        query.bindValue(":id", record_id)
        with db_transaction(db) as ok:
            if not ok:
                return False
            if not exec_query(db, query):
                return False
        return True

    @staticmethod
    def delete(record_id):
        db = QSqlDatabase.database(constants.USER_CONNECTION)
        sql = f"DELETE FROM {constants.TABLE_USER} WHERE id = :id"
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
        udd_container_dir = UserUDDService.get_selected_udd()
        file_handler.delete_dir(os.path.join(udd_container_dir, str(record_id)))
        return True

    @staticmethod
    def is_value_existed(condition):
        db = QSqlDatabase.database(constants.USER_CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {constants.TABLE_USER} WHERE {key} = :value"
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
    def get_ua(record_id, is_mobile=False):
        db = QSqlDatabase.database(constants.USER_CONNECTION)
        query = QSqlQuery(db)
        if is_mobile:
            sql = f"SELECT mobile_ua FROM {constants.TABLE_USER} WHERE id = :id"
        else:
            sql = f"SELECT desktop_ua FROM {constants.TABLE_USER} WHERE id = :id"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return None
        query.bindValue(":id", record_id)
        if not exec_query(db, query):
            return None
        if query.next():
            return query.value(0)
        return None

    @staticmethod
    def get_udd(record_id):
        udd_path = os.path.abspath(
            os.path.join(UserUDDService.get_selected_udd(), str(record_id))
        )
        if os.path.exists(udd_path):
            return udd_path
        else:
            return None


class UserUDDService(BaseService):
    TABLE_NAME = constants.TABLE_USER_SETTINGS_UDD
    CONNECTION = constants.USER_CONNECTION

    @classmethod
    def get_columns(cls):
        return [
            "id",
            "value",
            "is_selected",
            "updated_at",
            "created_at",
        ]

    @classmethod
    def get_selected_udd(cls):
        db = QSqlDatabase.database(constants.USER_CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT value FROM {cls.TABLE_NAME} WHERE is_selected = :is_selected"
        if not query.prepare(sql):
            return None
        query.bindValue(":is_selected", 1)
        if not exec_query(db, query):
            return None
        if query.next():
            return query.value(0)
        return None

    @classmethod
    def set_selected_udd(cls, record_id):
        db = QSqlDatabase.database(constants.USER_CONNECTION)
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


class UserProxyService(BaseService):
    TABLE_NAME = constants.TABLE_USER_SETTINGS_PROXY
    CONNECTION = constants.USER_CONNECTION

    @classmethod
    def get_columns(cls):
        return [
            "id",
            "value",
            "updated_at",
            "created_at",
        ]

    @classmethod
    def get_proxies(cls):
        proxies = []
        db = QSqlDatabase.database(cls.CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT value FROM {cls.TABLE_NAME}"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return proxies
        if not exec_query(db, query):
            return proxies
        while query.next():
            proxies.append(query.value(0))
        return proxies
