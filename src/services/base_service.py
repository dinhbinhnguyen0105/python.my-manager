# src/services/base_service.py
import logging
import sys
from contextlib import contextmanager
from PyQt6.QtSql import QSqlQuery, QSqlDatabase

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


class BaseService:
    TABLE_NAME = None
    CONNECTION = None

    @classmethod
    def get_columns(cls):
        raise NotImplementedError(
            "The get_columns() method has not been implemented for the subclass."
        )

    @classmethod
    def read(cls, record_id):
        db = QSqlDatabase.database(cls.CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE id = :id"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return None
        query.bindValue(":id", record_id)
        if not exec_query(db, query):
            return None
        if query.next():
            return record_to_dict(query)
        return None

    @classmethod
    def read_all(cls):
        db = QSqlDatabase.database(cls.CONNECTION)
        query = QSqlQuery(db)
        sql = f"SELECT * FROM {cls.TABLE_NAME}"
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
    def read_all_staticmethod(connection, table_name):
        db = QSqlDatabase.database(connection)
        query = QSqlQuery(db)
        sql = f"SELECT * FROM {table_name}"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return []
        if not exec_query(db, query):
            return []
        results = []
        while query.next():
            results.append(record_to_dict(query))
        return results

    @classmethod
    def create(cls, payload):
        db = QSqlDatabase.database(cls.CONNECTION)
        valid_columns = [col for col in cls.get_columns() if col in payload]
        if not valid_columns:
            logger.error("No valid columns provided for create.")
            return False
        columns = ", ".join(valid_columns)
        placeholders = ", ".join([f":{col}" for col in valid_columns])
        sql = f"INSERT INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"
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

    @classmethod
    def update(cls, record_id, payload):
        db = QSqlDatabase.database(cls.CONNECTION)
        valid_columns = [
            col for col in cls.get_columns() if col != "id" and col in payload
        ]
        if not valid_columns:
            logger.error("No valid columns provided for update.")
            return False
        set_clause = ", ".join([f"{col} = :{col}" for col in valid_columns])
        sql = (
            f"UPDATE {cls.TABLE_NAME} SET {set_clause}, "
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

    @classmethod
    def delete(cls, record_id):
        db = QSqlDatabase.database(cls.CONNECTION)
        sql = f"DELETE FROM {cls.TABLE_NAME} WHERE id = :id"
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
        return True

    @classmethod
    def delete_multiple(cls, record_ids):
        if not record_ids:
            return True

        db = QSqlDatabase.database(cls.CONNECTION)
        with db_transaction(db) as ok:
            if not ok:
                return False

            placeholders = ", ".join("?" * len(record_ids))
            sql = f"DELETE FROM {cls.TABLE_NAME} WHERE id IN ({placeholders})"
            query = QSqlQuery(db)

            if not query.prepare(sql):
                logger.error(query.lastError().text())
                return False

            for i, record_id in enumerate(record_ids):
                query.bindValue(i, record_id)

            if not exec_query(db, query):
                return False
            return True

    @classmethod
    def is_value_existed(cls, condition):
        db = QSqlDatabase.database(cls.CONNECTION)
        query = QSqlQuery(db)
        key, value = next(iter(condition.items()))
        sql = f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE {key} = :value"
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
    def get_label_vi_staticmethod(connection, table_name, record_id):
        db = QSqlDatabase.database(connection)
        query = QSqlQuery(db)
        sql = f"SELECT label_vi FROM {table_name} WHERE id = {record_id}"
        if not query.prepare(sql):
            logger.error(query.lastError().text())
            return None
        if not exec_query(db, query):
            return None
        if query.next():
            return query.value(0)
        return None


# def read_all_staticmethod(connection, table_name):
# db = QSqlDatabase.database(connection)
# query = QSqlQuery(db)
# sql = f"SELECT * FROM {table_name}"
# if not query.prepare(sql):
#     logger.error(query.lastError().text())
#     return []
# if not exec_query(db, query):
#     return []
# results = []
# while query.next():
#     results.append(record_to_dict(query))
# return results
