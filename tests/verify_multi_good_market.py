import unittest
import logging
import random
import os
import sqlite3
import config
from unittest.mock import MagicMock, patch
from simulation.engine import Simulation
from simulation.db.repository import SimulationRepository
from simulation.ai_model import AIEngineRegistry
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.schemas import FirmActionVector, HouseholdActionVector
from simulation.ai.firm_ai import FirmAI
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Personality


class TestMultiGoodMarket(unittest.TestCase):
    def setUp(self):
        self.db_path = "simulation_data.db"
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

        self.repository = SimulationRepository()
        self.repository.clear_all_data()

        # Ensure schema has all columns needed (should be handled by repository, but enforcing for test)
        self.repository.cursor.execute("DROP TABLE IF EXISTS market_history")
        self.repository.cursor.execute("""
            CREATE TABLE market_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time INTEGER,
                market_id TEXT,
                item_id TEXT,
                avg_price REAL,
                trade_volume REAL,
                best_ask REAL,
                best_bid REAL,
                avg_ask REAL,
                avg_bid REAL,
                worst_ask REAL,
                worst_bid REAL
            );
        """)
        self.repository.conn.commit()

    def test_multi_good_dynamics(self):
        print("\n=== Market Test: Multi-good (Food & Clothing) ===")

        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger("TestMultiGood")

        mock_action_proposal = MagicMock()
        mock_state_builder = MagicMock()
        ai_manager = AIEngineRegistry(
            action_proposal_engine=mock_action_proposal,
            state_builder=mock_state_builder,
        )

        goods_list = []
        for id, info in config.GOODS.items():
            info["id"] = id
            goods_list.append(info)

        # 1. Create Agents with Diversity
        households = []
        for i in range(20):
            talent = Talent(base_learning_rate=0.1, max_potential={})
            ai_engine = ai_manager.get_engine("needs_and_growth")
            household_ai = HouseholdAI(agent_id=f"H{i}", ai_decision_engine=ai_engine)
            decision_engine = AIDrivenHouseholdDecisionEngine(
                household_ai, config, logger
            )

            h = Household(
                id=i,
                talent=talent,
                goods_data=goods_list,
                initial_assets=random.uniform(2000.0, 3000.0),
                initial_needs={
                    "survival": random.uniform(10.0, 30.0),  # Food need
                    "social": random.uniform(5.0, 20.0),  # Clothing need
                    "asset": 10.0,
                    "improvement": 10.0,
                },
                decision_engine=decision_engine,
                value_orientation="needs_and_growth",
                personality=Personality.GROWTH_ORIENTED,
                config_module=config,
                logger=logger,
            )
            households.append(h)

        firms = []
        # 3 Food Firms
        for i in range(3):
            firm_id = i + 20
            ai_engine = ai_manager.get_engine("profit_maximizer")
            firm_ai = FirmAI(agent_id=str(firm_id), ai_decision_engine=ai_engine)
            decision_engine = AIDrivenFirmDecisionEngine(firm_ai, config, logger)

            f = Firm(
                id=firm_id,
                initial_capital=random.uniform(10000.0, 15000.0),
                initial_liquidity_need=100.0,
                specialization="basic_food",
                productivity_factor=random.uniform(10.0, 15.0),
                decision_engine=decision_engine,
                value_orientation="profit_maximizer",
                config_module=config,
                logger=logger,
            )
            f.inventory["basic_food"] = 50.0
            firms.append(f)

        # 2 Clothing Firms
        for i in range(2):
            firm_id = i + 23
            ai_engine = ai_manager.get_engine("profit_maximizer")
            firm_ai = FirmAI(agent_id=str(firm_id), ai_decision_engine=ai_engine)
            decision_engine = AIDrivenFirmDecisionEngine(firm_ai, config, logger)

            f = Firm(
                id=firm_id,
                initial_capital=random.uniform(10000.0, 15000.0),
                initial_liquidity_need=100.0,
                specialization="clothing",
                productivity_factor=random.uniform(
                    5.0, 8.0
                ),  # Lower productivity for clothing
                decision_engine=decision_engine,
                value_orientation="profit_maximizer",
                config_module=config,
                logger=logger,
            )
            f.inventory["clothing"] = 20.0
            firms.append(f)

        sim = Simulation(
            households=households,
            firms=firms,
            ai_trainer=ai_manager,
            repository=self.repository,
            config_module=config,
            goods_data=goods_list,
            logger=logger,
        )

        def noisy_firm_vector():
            noise = (random.random() - 0.5) * 0.1
            return FirmActionVector(0.5 + noise, 0.5 + noise, 0.5)

        def noisy_hh_vector(item_list):
            consump_agg = {
                item: 0.5 + (random.random() - 0.5) * 0.1 for item in item_list
            }
            return HouseholdActionVector(consump_agg, 0.5, 0.0, 0.0)

        # Run Simulation Phase 1: Normal (1-15)
        print("Phase 1: Normal Operation (Tick 1-15)")
        for t in range(1, 16):
            for f in sim.firms:
                f.decision_engine.ai_engine.decide_action_vector = MagicMock(
                    return_value=noisy_firm_vector()
                )
            for h in sim.households:
                h.decision_engine.ai_engine.decide_action_vector = MagicMock(
                    side_effect=lambda *args, **kwargs: noisy_hh_vector(goods_list_ids)
                )

            goods_list_ids = [g["id"] for g in goods_list]
            sim.run_tick()

        # Run Simulation Phase 2: High Needs (16-30)
        print("\nPhase 2: High Need State (Tick 16-30)")
        for t in range(16, 31):
            for f in sim.firms:
                # Firms push prices up slightly as demand grows
                f.decision_engine.ai_engine.decide_action_vector = MagicMock(
                    return_value=FirmActionVector(0.2, 0.4, 0.5)
                )
            for h in sim.households:
                # Force hunger and social need
                h.needs["survival"] = min(
                    100.0, h.needs.get("survival", 0.0) + 10.0 * (t - 15)
                )
                h.needs["social"] = min(
                    100.0, h.needs.get("social", 0.0) + 5.0 * (t - 15)
                )

                # High aggressiveness
                h.decision_engine.ai_engine.decide_action_vector = MagicMock(
                    side_effect=lambda *args, **kwargs: noisy_hh_vector(goods_list_ids)
                )

            sim.run_tick()

        # Analysis
        print("\n=== Market History Analysis ===")
        for item in ["basic_food", "clothing"]:
            print(f"\nItem: {item}")
            self.repository.cursor.execute(
                """
                SELECT time, avg_price, trade_volume, avg_ask, avg_bid
                FROM market_history 
                WHERE item_id = ?
                ORDER BY time ASC
            """,
                (item,),
            )
            rows = self.repository.cursor.fetchall()

            print(
                f"{'Tick':<4} | {'Price':<6} | {'Vol':<5} | {'AvgAsk':<6} | {'AvgBid':<6}"
            )
            print("-" * 40)
            for r in rows[:10]:  # Show first 10
                print(
                    f"{r[0]:<4} | {r[1]:<6.2f} | {r[2]:<5.1f} | {r[3]:<6.1f} | {r[4]:<6.1f}"
                )
            print("...")
            for r in rows[-5:]:  # Show last 5
                print(
                    f"{r[0]:<4} | {r[1]:<6.2f} | {r[2]:<5.1f} | {r[3]:<6.1f} | {r[4]:<6.1f}"
                )

        # Check Bulk Buying (Quantity > 1)
        self.repository.cursor.execute(
            "SELECT COUNT(*) FROM transactions WHERE quantity > 1"
        )
        bulk_count = self.repository.cursor.fetchone()[0]
        print(f"\nTransactions with Bulk Buying (>1 unit): {bulk_count}")

        # Verify Indifference Curves: Check if households hold both items
        sample_h = sim.households[0]
        print(f"\nSample Household Inventory (H0): {sample_h.inventory}")

        if len(sample_h.inventory) >= 2:
            print("SUCCESS: Households are consuming multiple goods.")
        else:
            print(
                "NOTICE: Household only has one type of good. Adjusting needs/prices might be needed."
            )


if __name__ == "__main__":
    unittest.main()
