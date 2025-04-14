import logging
import sys, os
from contextlib import contextmanager
from PyQt6.QtSql import QSqlQuery, QSqlDatabase
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


def record_to_dict(query: QSqlQuery) -> dict:
    """Chuyển kết quả từ QSqlQuery thành dict."""
    rec = query.record()
    return {rec.fieldName(i): query.value(i) for i in range(rec.count())}


@contextmanager
def db_transaction(db):
    if not db.transaction():
        logger.error("Failed to start transaction.")
        yield False
        return
    try:
        yield True
        if not db.commit():
            logger.error("Failed to commit transaction.")
            db.rollback()
    except Exception as e:
        db.rollback()
        logger.error(f"ERROR: {e}")
        yield False

class RE