from typing import Any

class QTableManager:
    """
    Q-테이블의 저장, 로드, 업데이트 로직을 관리하는 클래스.
    영속성을 위해 SQLite 데이터베이스를 사용한다.
    """
    q_table: dict[tuple, dict[Any, float]]
    def __init__(self) -> None: ...
    def get_q_value(self, state: tuple, action: Any) -> float:
        """특정 상태-행동 쌍의 Q-값을 반환한다."""
    def set_q_value(self, state: tuple, action: Any, value: float):
        """특정 상태-행동 쌍의 Q-값을 설정한다."""
    def get_state_q_values(self, state: tuple) -> dict[Any, float]:
        """특정 상태에 대한 모든 행동의 Q-값을 반환한다."""
    def save_to_db(self, db_path: str, agent_id: str, q_table_type: str):
        """Q-테이블을 SQLite 데이터베이스에 저장한다."""
    def load_from_db(self, db_path: str, agent_id: str, q_table_type: str, action_enum: Any):
        """SQLite 데이터베이스에서 Q-테이블을 로드한다."""
    def update_q_table(self, state: tuple, action: Any, reward: float, next_state: tuple, next_actions: list[Any], alpha: float, gamma: float) -> float:
        """Q-러닝 공식을 사용하여 Q-테이블을 업데이트하고, Q-값의 변화량을 반환한다."""
