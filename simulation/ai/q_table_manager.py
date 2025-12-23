# simulation/ai/q_table_manager.py

import sqlite3
import pickle
from typing import Any, Dict, Tuple, List
from enum import Enum
import logging


class QTableManager:
    """
    Q-테이블의 저장, 로드, 업데이트 로직을 관리하는 클래스.
    영속성을 위해 SQLite 데이터베이스를 사용한다.
    """

    def __init__(self):
        self.q_table: Dict[Tuple, Dict[Any, float]] = {}

    def get_q_value(self, state: Tuple, action: Any) -> float:
        """특정 상태-행동 쌍의 Q-값을 반환한다."""
        return self.q_table.get(state, {}).get(action, 0.0)

    def set_q_value(self, state: Tuple, action: Any, value: float):
        """특정 상태-행동 쌍의 Q-값을 설정한다."""
        if state not in self.q_table:
            self.q_table[state] = {}
        self.q_table[state][action] = value

    def get_state_q_values(self, state: Tuple) -> Dict[Any, float]:
        """특정 상태에 대한 모든 행동의 Q-값을 반환한다."""
        return self.q_table.get(state, {})

    def save_to_db(self, db_path: str, agent_id: str, q_table_type: str):
        """Q-테이블을 SQLite 데이터베이스에 저장한다."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_q_values (
                    agent_id TEXT,
                    q_table_type TEXT,
                    state_pickle BLOB,
                    action_name TEXT,
                    q_value REAL,
                    PRIMARY KEY (agent_id, q_table_type, state_pickle, action_name)
                )
            """)

            cursor.execute(
                "DELETE FROM agent_q_values WHERE agent_id = ? AND q_table_type = ?",
                (agent_id, q_table_type),
            )

            rows = []
            for state, actions in self.q_table.items():
                for action, q_value in actions.items():
                    state_pickle = pickle.dumps(state)
                    action_name = (
                        action.name if isinstance(action, Enum) else str(action)
                    )
                    rows.append(
                        (agent_id, q_table_type, state_pickle, action_name, q_value)
                    )

            cursor.executemany(
                "INSERT INTO agent_q_values (agent_id, q_table_type, state_pickle, action_name, q_value) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()

    def load_from_db(
        self, db_path: str, agent_id: str, q_table_type: str, action_enum: Any
    ):
        """SQLite 데이터베이스에서 Q-테이블을 로드한다."""
        self.q_table = {}
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_q_values (
                        agent_id TEXT,
                        q_table_type TEXT,
                        state_pickle BLOB,
                        action_name TEXT,
                        q_value REAL,
                        PRIMARY KEY (agent_id, q_table_type, state_pickle, action_name)
                    )
                """)
                cursor.execute(
                    "SELECT state_pickle, action_name, q_value FROM agent_q_values WHERE agent_id = ? AND q_table_type = ?",
                    (agent_id, q_table_type),
                )
                for row in cursor.fetchall():
                    state = pickle.loads(row[0])
                    action = (
                        action_enum[row[1]]
                        if (action_enum and isinstance(action_enum, type(Enum)))
                        else row[1]
                    )
                    q_value = row[2]
                    if state not in self.q_table:
                        self.q_table[state] = {}
                    self.q_table[state][action] = q_value
        except sqlite3.Error as e:
            logging.error(
                f"Database error while loading Q-table for agent {agent_id}: {e}"
            )
        except FileNotFoundError:
            logging.warning(
                f"Database file not found at {db_path}. Starting with empty Q-table for agent {agent_id}."
            )
        except KeyError as e:
            logging.error(
                f"Action name {e} not found in enum {action_enum} for agent {agent_id}."
            )

    def update_q_table(
        self,
        state: Tuple,
        action: Any,
        reward: float,
        next_state: Tuple,
        next_actions: List[Any],
        alpha: float,
        gamma: float,
    ) -> float:
        """Q-러닝 공식을 사용하여 Q-테이블을 업데이트하고, Q-값의 변화량을 반환한다."""
        old_value = self.get_q_value(state, action)

        next_max = 0.0
        if next_actions:
            next_q_values = self.get_state_q_values(next_state)
            next_max = max(
                (next_q_values.get(a, 0.0) for a in next_actions), default=0.0
            )

        new_value = old_value + alpha * (reward + gamma * next_max - old_value)
        self.set_q_value(state, action, new_value)
        return new_value - old_value
