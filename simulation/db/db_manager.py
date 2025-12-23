import sqlite3
import json
from datetime import datetime
import logging


class DBManager:
    def __init__(self, db_path="simulation_data.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            raise

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

    def save_simulation_run(self, start_time, config_hash, description=None):
        self.cursor.execute(
            """
            INSERT INTO simulation_runs (start_time, config_hash, description)
            VALUES (?, ?, ?)
        """,
            (start_time, config_hash, description),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_simulation_run_end_time(self, run_id, end_time):
        self.cursor.execute(
            """
            UPDATE simulation_runs SET end_time = ? WHERE run_id = ?
        """,
            (end_time, run_id),
        )
        self.conn.commit()

    def save_simulation_state(
        self, run_id, tick, timestamp, global_economic_indicators
    ):
        self.cursor.execute(
            """
            INSERT INTO simulation_states (run_id, tick, timestamp, global_economic_indicators)
            VALUES (?, ?, ?, ?)
        """,
            (run_id, tick, timestamp, json.dumps(global_economic_indicators)),
        )
        self.conn.commit()

    def save_agent_state(
        self,
        run_id,
        tick,
        agent_id,
        agent_type,
        assets,
        inventory=None,
        needs=None,
        is_employed=None,
        employer_id=None,
        employees=None,
        production_targets=None,
        current_production=None,
        ai_model_state=None,
    ):
        self.cursor.execute(
            """
            INSERT INTO agents_state_history (
                run_id, tick, agent_id, agent_type, assets, inventory, needs,
                is_employed, employer_id, employees, production_targets,
                current_production, ai_model_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run_id,
                tick,
                agent_id,
                agent_type,
                assets,
                json.dumps(inventory) if inventory else None,
                json.dumps(needs) if needs else None,
                is_employed,
                employer_id,
                json.dumps(employees) if employees else None,
                json.dumps(production_targets) if production_targets else None,
                json.dumps(current_production) if current_production else None,
                json.dumps(ai_model_state) if ai_model_state else None,
            ),
        )
        self.conn.commit()

    def save_transaction(
        self,
        run_id,
        tick,
        buyer_id,
        seller_id,
        item_id,
        quantity,
        price,
        transaction_type,
        loan_id=None,
    ):
        self.cursor.execute(
            """
            INSERT INTO transactions_history (
                run_id, tick, buyer_id, seller_id, item_id, quantity, price, transaction_type, loan_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run_id,
                tick,
                buyer_id,
                seller_id,
                item_id,
                quantity,
                price,
                transaction_type,
                loan_id,
            ),
        )
        self.conn.commit()

    def save_ai_decision(
        self,
        run_id,
        tick,
        agent_id,
        decision_type,
        decision_details=None,
        predicted_reward=None,
        actual_reward=None,
    ):
        self.cursor.execute(
            """
            INSERT INTO ai_decisions_history (
                run_id, tick, agent_id, decision_type, decision_details, predicted_reward, actual_reward
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run_id,
                tick,
                agent_id,
                decision_type,
                json.dumps(decision_details) if decision_details else None,
                predicted_reward,
                actual_reward,
            ),
        )
        self.conn.commit()

    def get_simulation_run(self, run_id):
        self.cursor.execute("SELECT * FROM simulation_runs WHERE run_id = ?", (run_id,))
        return self.cursor.fetchone()

    def get_simulation_states(self, run_id, tick=None):
        query = "SELECT * FROM simulation_states WHERE run_id = ?"
        params = [run_id]
        if tick is not None:
            query += " AND tick = ?"
            params.append(tick)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_agent_states(self, run_id, tick=None, agent_id=None):
        query = "SELECT * FROM agents_state_history WHERE run_id = ?"
        params = [run_id]
        if tick is not None:
            query += " AND tick = ?"
            params.append(tick)
        if agent_id is not None:
            query += " AND agent_id = ?"
            params.append(agent_id)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_transactions(self, run_id, tick=None):
        query = "SELECT * FROM transactions_history WHERE run_id = ?"
        params = [run_id]
        if tick is not None:
            query += " AND tick = ?"
            params.append(tick)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_ai_decisions(self, run_id, tick=None, agent_id=None):
        query = "SELECT * FROM ai_decisions_history WHERE run_id = ?"
        params = [run_id]
        if tick is not None:
            query += " AND tick = ?"
            params.append(tick)
        if agent_id is not None:
            query += " AND agent_id = ?"
            params.append(agent_id)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def reset_database(self):
        """
        데이터베이스의 모든 테이블을 삭제하고 다시 생성하여 초기화합니다.
        """
        if self.conn:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = self.cursor.fetchall()
            for table_name in tables:
                if (
                    table_name[0] != "sqlite_sequence"
                ):  # sqlite_sequence는 삭제하지 않음
                    self.cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]}")
            self.conn.commit()
            self._create_tables()
            # print(f"Database at {self.db_path} has been reset.") # 기존 print 문은 제거

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None


if __name__ == "__main__":
    # Example Usage:
    db_manager = DBManager(db_path="test_simulation.db")

    # Save a new simulation run
    run_id = db_manager.save_simulation_run(
        start_time=datetime.now().isoformat(),
        config_hash="abcdef12345",
        description="Test run for new DBManager",
    )
    logging.info(f"New simulation run_id: {run_id}")

    # Save simulation state for tick 1
    db_manager.save_simulation_state(
        run_id=run_id,
        tick=1,
        timestamp=datetime.now().isoformat(),
        global_economic_indicators={"gdp": 1000, "unemployment_rate": 0.05},
    )

    # Save agent state for a household
    db_manager.save_agent_state(
        run_id=run_id,
        tick=1,
        agent_id=101,
        agent_type="Household",
        assets=500.0,
        inventory={"food": 10, "clothes": 2},
        needs={"food": 0.8, "shelter": 0.5},
        is_employed=True,
        employer_id=201,
    )

    # Save agent state for a firm
    db_manager.save_agent_state(
        run_id=run_id,
        tick=1,
        agent_id=201,
        agent_type="Firm",
        assets=2000.0,
        inventory={"food": 50, "raw_materials": 100},
        employees={"101": 150.0},
        production_targets={"food": 20},
        current_production={"food": 15},
    )

    # Save a transaction
    db_manager.save_transaction(
        run_id=run_id,
        tick=1,
        buyer_id=101,
        seller_id=201,
        item_id="food",
        quantity=5.0,
        price=10.0,
        transaction_type="Goods",
    )

    # Save an AI decision
    db_manager.save_ai_decision(
        run_id=run_id,
        tick=1,
        agent_id=101,
        decision_type="Consume",
        decision_details={"item": "food", "quantity": 3},
        predicted_reward=0.9,
        actual_reward=0.85,
    )

    # Retrieve data
    logging.info("\n--- Retrieved Data ---")
    logging.info("Simulation Run:", db_manager.get_simulation_run(run_id))
    logging.info(
        "Simulation States (tick 1):", db_manager.get_simulation_states(run_id, tick=1)
    )
    logging.info(
        "Agent States (Household 101, tick 1):",
        db_manager.get_agent_states(run_id, tick=1, agent_id=101),
    )
    logging.info("Transactions (tick 1):", db_manager.get_transactions(run_id, tick=1))
    logging.info(
        "AI Decisions (agent 101, tick 1):",
        db_manager.get_ai_decisions(run_id, tick=1, agent_id=101),
    )

    # Update simulation run end time
    db_manager.update_simulation_run_end_time(run_id, datetime.now().isoformat())
    logging.info("Updated Simulation Run:", db_manager.get_simulation_run(run_id))

    db_manager.close()
    logging.info("\nDatabase 'test_simulation.db' created and populated successfully.")
    # Clean up the test database
    # os.remove('test_simulation.db')
    # logging.info("Test database removed.")
