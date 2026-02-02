
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
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.schemas import FirmActionVector, HouseholdActionVector
from simulation.ai.firm_ai import FirmAI
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Personality

class TestSupplyShock(unittest.TestCase):
    def setUp(self):
        # Use a real file for the test DB
        self.db_path = "simulation_data.db" # Default name used by DatabaseManager
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass
            
        self.repository = SimulationRepository()
        self.repository.clear_all_data()

        # Update DB schema for market_history table
        # This is a direct schema update for the test
        self.repository.cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_history (
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

    def tearDown(self):
        # self.repository.close() - Repository doesn't have close, it uses db_manager
        pass

    def test_supply_shock_response(self):
        print("\n=== Market Shock Test: Supply Collapse ===")
        
        logging.basicConfig(level=logging.ERROR) # Only Errors for console to keep it clean
        logger = logging.getLogger("TestSupplyShock")
        
        # Repository is already initialized in setUp
        
        # Mocks for AI Registry dependencies
        mock_action_proposal = MagicMock()
        mock_state_builder = MagicMock()
        
        # AI Registry
        ai_manager = AIEngineRegistry(
            action_proposal_engine=mock_action_proposal,
            state_builder=mock_state_builder
        )
        
        # Goods Data
        goods_list = []
        for id, info in config.GOODS.items():
            info["id"] = id
            goods_list.append(info)

        # 1. Create Agents with Diversity
        households = []
        for i in range(20): # 20 Households
            talent = Talent(base_learning_rate=0.1, max_potential={})
            ai_engine = ai_manager.get_engine("needs_and_growth") 
            household_ai = HouseholdAI(agent_id=f"H{i}", ai_decision_engine=ai_engine)
            decision_engine = AIDrivenHouseholdDecisionEngine(household_ai, config, logger)
            
            # Diverse initial states
            h = Household(
                id=i,
                talent=talent,
                goods_data=goods_list,
                initial_assets=random.uniform(800.0, 1200.0), 
                initial_needs={
                    "survival": random.uniform(40.0, 60.0),
                    "asset": 10.0,
                    "social": 10.0,
                    "improvement": 10.0
                },
                decision_engine=decision_engine,
                value_orientation="needs_and_growth",
                personality=Personality.GROWTH_ORIENTED,
                config_module=config,
                logger=logger
            )
            households.append(h)

        firms = []
        for i in range(5): # 5 Firms
            ai_engine = ai_manager.get_engine("profit_maximizer")
            firm_ai = FirmAI(agent_id=str(i + 20), ai_decision_engine=ai_engine)
            decision_engine = AIDrivenFirmDecisionEngine(firm_ai, config, logger)
            
            f = Firm(
                id=i + 20,
                initial_capital=random.uniform(8000.0, 12000.0),
                initial_liquidity_need=100.0,
                specialization="basic_food", 
                productivity_factor=random.uniform(8.0, 12.0),
                decision_engine=decision_engine,
                value_orientation="profit_maximizer",
                config_module=config,
                logger=logger
            )
            f.inventory["basic_food"] = random.uniform(10.0, 20.0) 
            f.production_target = 100.0 
            firms.append(f)

        # 2. Initialize Simulation
        sim = Simulation(
            households=households,
            firms=firms,
            ai_trainer=ai_manager,
            repository=self.repository,
            config_module=config,
            goods_data=goods_list,
            logger=logger
        )

        # Helper: Create noisy action vectors
        def noisy_firm_vector(base_agg_sell, base_agg_hire):
            noise = (random.random() - 0.5) * 0.1 # +/- 0.05 noise
            return FirmActionVector(max(0, min(1, base_agg_sell + noise)), max(0, min(1, base_agg_hire + noise)), 0.5)

        def noisy_hh_vector(base_consumption_agg, item_id="basic_food"):
            noise = (random.random() - 0.5) * 0.1
            return HouseholdActionVector({item_id: max(0, min(1, base_consumption_agg + noise))}, 0.5, 0.0, 0.0)

        # 3. Run Phase 1: Normal Operation (Tick 1-15)
        print("Phase 1: Normal Operation (Tick 1-15)")
        for _ in range(15):
            for f in sim.firms:
                # Capture f in closure or use individual lambda
                f.decision_engine.ai_engine.decide_action_vector = MagicMock(side_effect=lambda *args, **kwargs: noisy_firm_vector(0.5, 0.5))
            for h in sim.households:
                h.decision_engine.ai_engine.decide_action_vector = MagicMock(side_effect=lambda *args, **kwargs: noisy_hh_vector(0.5))
            
            sim.run_tick()

        # 4. Apply Shock: Production Stops (Tick 16-40)
        print("\n!!! SHOCK: FACTORY SHUTDOWN !!!")
        for firm in sim.firms:
            firm.productivity_factor = 0.0 

        print("Phase 2: Scarcity & Panic Buying (Tick 16-40)")
        for _ in range(25):
            for f in sim.firms:
                f.productivity_factor = 0.0
                f.decision_engine.ai_engine.decide_action_vector = MagicMock(side_effect=lambda *args, **kwargs: noisy_firm_vector(0.1, 0.0))
            
            for h in sim.households:
                # Calculate urgency based on individual needs
                current_survival = h._bio_state.needs.get("survival", 0)
                base_agg = 0.5
                if current_survival > 60: base_agg = 0.9 # Panic buy
                elif current_survival < 30: base_agg = 0.3 # Relaxed
                
                h.decision_engine.ai_engine.decide_action_vector = MagicMock(side_effect=lambda *args, **kwargs: noisy_hh_vector(base_agg))

            sim.run_tick()

        # 5. DB Verification using DAO (Repository)
        print("\n=== DAO Data Analysis ===")
        
        # Query Market History
        # We'll use raw SQL through repository's cursor for flexibility
        self.repository.cursor.execute("""
            SELECT time, avg_price, best_ask, worst_ask, best_bid, worst_bid, avg_ask, avg_bid
            FROM market_history 
            WHERE item_id = 'basic_food'
            ORDER BY time ASC
        """)
        rows = self.repository.cursor.fetchall()
        
        if not rows:
            print("ERROR: No market history recorded in DB!")
            self.fail("No market history found")

        print(f"{'Tick':<4} | {'Price':<6} | {'Ask(B/W/A)':<22} | {'Bid(B/W/A)':<22}")
        print("-" * 65)
        
        price_pre = []
        price_post = []
        
        for r in rows:
            tick, price, b_ask, w_ask, b_bid, w_bid, a_ask, a_bid = r
            ask_str = f"{b_ask:>5.1f}/{w_ask:>5.1f}/{a_ask:>5.1f}"
            bid_str = f"{b_bid:>5.1f}/{w_bid:>5.1f}/{a_bid:>5.1f}"
            print(f"{tick:<4} | {price:<6.2f} | {ask_str:<22} | {bid_str:<22}")
            
            if tick <= 15:
                if price > 0: price_pre.append(price)
            else:
                if price > 0: price_post.append(price)

        # AI Decisions Check
        self.repository.cursor.execute("SELECT COUNT(*) FROM ai_decisions_history")
        count = self.repository.cursor.fetchone()[0]
        print(f"\nTotal AI Decisions recorded in DB: {count}")
        
        if count > 0:
            print("SUCCESS: AI decisions and rewards are being saved.")
        else:
            print("FAIL: AI decisions NOT found in DB.")

        # Final Assessment
        avg_pre = sum(price_pre) / len(price_pre) if price_pre else 0
        avg_post = sum(price_post) / len(price_post) if price_post else 0
        max_post = max(price_post) if price_post else 0
        
        print(f"\nSummary Analysis:")
        print(f"Avg Price (Pre-Shock): {avg_pre:.2f}")
        print(f"Avg Price (Post-Shock): {avg_post:.2f}")
        print(f"Max Price (Post-Shock): {max_post:.2f}")
        
        if max_post > avg_pre * 1.5:
            print("RESULT: PASS - Scarcity correctly drove prices up in DB records.")
        else:
            print("RESULT: FAIL - Prices remained stagnant despite scarcity.")

if __name__ == "__main__":
    unittest.main()
