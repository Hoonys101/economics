import sqlite3
from _typeshed import Incomplete
from simulation.db.schema import create_tables as create_tables

DATABASE_NAME: str

class DatabaseManager:
    """
    SQLite3 데이터베이스 연결 및 관리를 담당하는 클래스입니다.
    """
    def __new__(cls): ...
    def get_connection(self) -> sqlite3.Connection:
        """
        데이터베이스 연결을 반환합니다. 연결이 없으면 새로 생성하고 테이블을 초기화합니다.
        """
    def close_connection(self) -> None:
        """
        데이터베이스 연결을 닫습니다.
        """

db_manager: Incomplete

def get_db_connection() -> sqlite3.Connection:
    """
    데이터베이스 연결을 얻는 헬퍼 함수입니다.
    """
def close_db_connection() -> None:
    """
    데이터베이스 연결을 닫는 헬퍼 함수입니다.
    """
