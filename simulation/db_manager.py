import sqlite3
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, db_path=':memory:'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                config_hash TEXT NOT NULL,
                description TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_states (
                state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                global_economic_indicators TEXT,
                FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents_state_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                agent_type TEXT NOT NULL,
                assets REAL NOT NULL,
                inventory TEXT,
                needs TEXT,
                is_employed BOOLEAN,
                employer_id INTEGER,
                employees TEXT,
                production_targets TEXT,
                current_production TEXT,
                ai_model_state TEXT,
                FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions_history (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                buyer_id INTEGER,
                seller_id INTEGER,
                item_id TEXT,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                loan_id TEXT,
                FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_decisions_history (
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                decision_type TEXT NOT NULL,
                decision_details TEXT,
                predicted_reward REAL,
                actual_reward REAL,
                FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
            )
        """)
        self.conn.commit()

    def reset_database(self):
        if self.db_path != ':memory:' and os.path.exists(self.db_path):
            self.conn.close()
            os.remove(self.db_path)
            self._connect()
            self._create_tables()
        elif self.db_path == ':memory:':
            self.conn.close()
            self._connect()
            self._create_tables()
        logger.info(f"Database at {self.db_path} has been reset.")

    def close(self):
        if self.conn:
            self.conn.close()

    def save_simulation_run(self, config_hash, description=None):
        start_time = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO simulation_runs (start_time, config_hash, description) VALUES (?, ?, ?)",
            (start_time, config_hash, description)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_simulation_run_end_time(self, run_id):
        end_time = datetime.now().isoformat()
        self.cursor.execute(
            "UPDATE simulation_runs SET end_time = ? WHERE run_id = ?",
            (end_time, run_id)
        )
        self.conn.commit()

    def save_simulation_state(self, run_id, tick, global_economic_indicators):
        timestamp = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO simulation_states (run_id, tick, timestamp, global_economic_indicators) VALUES (?, ?, ?, ?)",
            (run_id, tick, timestamp, json.dumps(global_economic_indicators))
        )
        self.conn.commit()

    def save_agent_state(self, run_id, tick, agent_id, agent_type, assets, inventory=None, needs=None,
                         is_employed=None, employer_id=None, employees=None, production_targets=None,
                         current_production=None, ai_model_state=None):
        self.cursor.execute(
            """
            INSERT INTO agents_state_history (
                run_id, tick, agent_id, agent_type, assets, inventory, needs,
                is_employed, employer_id, employees, production_targets,
                current_production, ai_model_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, tick, agent_id, agent_type, assets,
                json.dumps(inventory) if inventory else None,
                json.dumps(needs) if needs else None,
                is_employed, employer_id,
                json.dumps(employees) if employees else None,
                json.dumps(production_targets) if production_targets else None,
                json.dumps(current_production) if current_production else None,
                json.dumps(ai_model_state) if ai_model_state else None
            )
        )
        self.conn.commit()

    def save_transaction(self, run_id, tick, buyer_id, seller_id, item_id, quantity, price, transaction_type, loan_id=None):
        self.cursor.execute(
            """
            INSERT INTO transactions_history (
                run_id, tick, buyer_id, seller_id, item_id, quantity, price, transaction_type, loan_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, tick, buyer_id, seller_id, item_id, quantity, price, transaction_type, loan_id)
        )
        self.conn.commit()

    def save_ai_decision(self, run_id, tick, agent_id, decision_type, decision_details, predicted_reward=None, actual_reward=None):
        self.cursor.execute(
            """
            INSERT INTO ai_decisions_history (
                run_id, tick, agent_id, decision_type, decision_details, predicted_reward, actual_reward
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, tick, agent_id, decision_type,
                json.dumps(decision_details) if decision_details else None,
                predicted_reward, actual_reward
            )
        )
        self.conn.commit()

    def get_data(self, table_name, run_id=None, tick=None, agent_id=None):
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        params = []
        if run_id is not None:
            query += " AND run_id = ?"
            params.append(run_id)
        if tick is not None:
            query += " AND tick = ?"
            params.append(tick)
        if agent_id is not None:
            query += " AND agent_id = ?"
            params.append(agent_id)
        self.cursor.execute(query, tuple(params))
        return self.cursor.fetchall()

if __name__ == '__main__':
    pass
