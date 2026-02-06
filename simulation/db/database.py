import sqlite3
from typing import Optional
from simulation.db.schema import create_tables
import logging

DATABASE_NAME = "simulation_data.db"


class DatabaseManager:
    """
    SQLite3 데이터베이스 연결 및 관리를 담당하는 클래스입니다.
    """

    _instance: Optional["DatabaseManager"] = None
    _conn: Optional[sqlite3.Connection] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """
        데이터베이스 연결을 반환합니다. 연결이 없으면 새로 생성하고 테이블을 초기화합니다.
        """
        if self._conn is None:
            self._conn = sqlite3.connect(
                DATABASE_NAME,
                check_same_thread=False,
                timeout=30.0,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Enable WAL mode for better concurrency and synchronous=NORMAL for performance
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")

            create_tables(self._conn)
        return self._conn

    def close_connection(self):
        """
        데이터베이스 연결을 닫습니다.
        """
        if self._conn:
            self._conn.close()
            self._conn = None


# 전역적으로 사용될 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()


def get_db_connection() -> sqlite3.Connection:
    """
    데이터베이스 연결을 얻는 헬퍼 함수입니다.
    """
    return db_manager.get_connection()


def close_db_connection():
    """
    데이터베이스 연결을 닫는 헬퍼 함수입니다.
    """
    db_manager.close_connection()


if __name__ == "__main__":
    # 테스트용 데이터베이스 연결 및 테이블 생성 확인
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    logging.info(f"Tables in database: {cursor.fetchall()}")
    close_db_connection()
    logging.info(f"Database '{DATABASE_NAME}' created and tables initialized.")
