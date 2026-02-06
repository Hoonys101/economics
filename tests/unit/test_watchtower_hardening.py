import unittest
import sqlite3
import statistics
from unittest.mock import MagicMock
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.db.agent_repository import AgentRepository
from simulation.dtos.api import AgentStateData
from collections import deque

class TestWatchtowerHardening(unittest.TestCase):

    def setUp(self):
        # Tracker Setup
        self.config_module = MagicMock()
        self.tracker = EconomicIndicatorTracker(self.config_module)

        # Repository Setup (In-Memory DB)
        self.conn = sqlite3.connect(":memory:")
        self._create_tables()
        self.repo = AgentRepository(self.conn)

    def tearDown(self):
        self.conn.close()

    def _create_tables(self):
        # Minimal schema for AgentRepository
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                time INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                agent_type TEXT NOT NULL,
                assets REAL NOT NULL,
                is_active BOOLEAN NOT NULL,
                is_employed BOOLEAN,
                employer_id INTEGER,
                needs_survival REAL,
                needs_labor REAL,
                inventory_food REAL,
                current_production REAL,
                num_employees INTEGER,
                education_xp REAL,
                generation INTEGER
            )
        """)
        self.conn.commit()

    def test_tracker_sma_logic(self):
        # Window is 50. Let's feed 50 values.
        # GDP: 1, 2, ..., 50
        # CPI: 1, 1, ..., 1 (all 1s)
        # M2 Leak: 0.1, 0.2, ...

        expected_gdp_sum = 0
        expected_m2_sum = 0

        for i in range(1, 61): # Feed 60 values (window 50)
            gdp = float(i)
            cpi = 1.0
            m2_leak = float(i) * 0.1

            # Mock track inputs
            # We only care about the SMA update part which uses the passed args or updated metrics
            # tracker.track calls record["gdp"] = ...
            # We can manually append to deques to test get_smoothed_values,
            # OR we can Mock the track method's internal logic.
            # But track does a lot of calculation.
            # Easiest is to directly manipulate the deques or subclass.

            # Let's test the deque logic directly since we verified the code does append.
            # But better: use the public method get_smoothed_values.

            self.tracker.gdp_history.append(gdp)
            self.tracker.cpi_history.append(cpi)
            self.tracker.m2_leak_history.append(m2_leak)

        smoothed = self.tracker.get_smoothed_values()

        # Last 50 values: 11 to 60
        last_50_gdp = list(range(11, 61))
        expected_gdp_sma = statistics.mean(last_50_gdp)

        self.assertEqual(smoothed["gdp_sma"], expected_gdp_sma)
        self.assertEqual(smoothed["cpi_sma"], 1.0)

        last_50_m2 = [x * 0.1 for x in range(11, 61)]
        expected_m2_sma = statistics.mean(last_50_m2)
        self.assertAlmostEqual(smoothed["m2_leak_sma"], expected_m2_sma)

    def test_repo_birth_counts(self):
        # T=1: Agent 1, 2
        # T=2: Agent 1, 2, 3 (New: 3)
        # T=3: Agent 1, 3, 4 (New: 4, 2 died)

        def create_agent(tick, agent_id, run_id=1):
            return AgentStateData(
                run_id=run_id, time=tick, agent_id=agent_id, agent_type='household',
                assets=100.0, is_active=True, is_employed=False, employer_id=None,
                needs_survival=0, needs_labor=0, inventory_food=0, current_production=0,
                num_employees=0, education_xp=0, generation=1
            )

        # Insert T=1
        self.repo.save_agent_state(create_agent(1, 1))
        self.repo.save_agent_state(create_agent(1, 2))

        # Insert T=2
        self.repo.save_agent_state(create_agent(2, 1))
        self.repo.save_agent_state(create_agent(2, 2))
        self.repo.save_agent_state(create_agent(2, 3))

        # Insert T=3
        self.repo.save_agent_state(create_agent(3, 1))
        self.repo.save_agent_state(create_agent(3, 3))
        self.repo.save_agent_state(create_agent(3, 4))

        # Test 1 -> 2 (Expected: 1 birth - Agent 3)
        births_1_2 = self.repo.get_birth_counts(start_tick=1, end_tick=2, run_id=1)
        self.assertEqual(births_1_2, 1)

        # Test 2 -> 3 (Expected: 1 birth - Agent 4)
        births_2_3 = self.repo.get_birth_counts(start_tick=2, end_tick=3, run_id=1)
        self.assertEqual(births_2_3, 1)

        # Test 1 -> 3 (Expected: 2 births - Agent 3, 4)
        # Logic: Agents at T=3 (1, 3, 4) NOT IN Agents at T=1 (1, 2) => {3, 4} => 2
        births_1_3 = self.repo.get_birth_counts(start_tick=1, end_tick=3, run_id=1)
        self.assertEqual(births_1_3, 2)

        # Test Run ID isolation
        # Insert T=2 for Run=2
        self.repo.save_agent_state(create_agent(2, 99, run_id=2))
        # Should not affect Run=1 query
        births_1_2_run1 = self.repo.get_birth_counts(start_tick=1, end_tick=2, run_id=1)
        self.assertEqual(births_1_2_run1, 1)

if __name__ == '__main__':
    unittest.main()
