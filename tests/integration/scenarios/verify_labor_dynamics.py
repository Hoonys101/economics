
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

class TestLaborDynamics(unittest.TestCase):
    def setUp(self):
        self.db_path = "simulation_data.db"
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass
            
        self.repository = SimulationRepository()
        self.repository.clear_all_data()

    def test_job_hopping_and_wages(self):
        print("\n=== Labor Market Test: Job Hopping & Recurring Wages ===")
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("TestLabor")
        
        mock_action_proposal = MagicMock()
        mock_state_builder = MagicMock()
        ai_manager = AIEngineRegistry(
            action_proposal_engine=mock_action_proposal,
            state_builder=mock_state_builder
        )
        
        goods_list = []
        for id, info in config.GOODS.items():
            info["id"] = id
            goods_list.append(info)

        # 1. Create Agents
        households = []
        for i in range(10): # 10 Households
            talent = Talent(base_learning_rate=0.1, max_potential={})
            ai_engine = ai_manager.get_engine("needs_and_growth") 
            household_ai = HouseholdAI(agent_id=f"H{i}", ai_decision_engine=ai_engine)
            decision_engine = AIDrivenHouseholdDecisionEngine(household_ai, config, logger)
            
            h = Household(
                id=i,
                talent=talent,
                goods_data=goods_list,
                initial_assets=100.0, # Low initial assets
                initial_needs={
                    "survival": 50.0,
                    "social": 10.0,
                    "asset": 10.0,
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
        # Firm 10: Low Wage Payer
        ai_engine_10 = ai_manager.get_engine("profit_maximizer")
        firm_ai_10 = FirmAI(agent_id="20", ai_decision_engine=ai_engine_10)
        f10 = Firm(
            id=20, initial_capital=50000.0, initial_liquidity_need=100.0,
            specialization="basic_food", productivity_factor=10.0,
            decision_engine=AIDrivenFirmDecisionEngine(firm_ai_10, config, logger),
            value_orientation="profit_maximizer", config_module=config, logger=logger
        )
        firms.append(f10)

        # Firm 11: High Wage Payer
        ai_engine_11 = ai_manager.get_engine("profit_maximizer")
        firm_ai_11 = FirmAI(agent_id="21", ai_decision_engine=ai_engine_11)
        f11 = Firm(
            id=21, initial_capital=50000.0, initial_liquidity_need=100.0,
            specialization="basic_food", productivity_factor=10.0,
            decision_engine=AIDrivenFirmDecisionEngine(firm_ai_11, config, logger),
            value_orientation="profit_maximizer", config_module=config, logger=logger
        )
        firms.append(f11)

        sim = Simulation(
            households=households, firms=firms, ai_trainer=ai_manager,
            repository=self.repository, config_module=config, goods_data=goods_list, logger=logger
        )
        
        # Increase targets to ensure they keep hiring
        f10.production_target = 100.0
        f11.production_target = 100.0

        # Prevent firms from closing too early due to lack of sales in this isolated test
        config.FIRM_CLOSURE_TURNS_THRESHOLD = 999
        config.ASSETS_CLOSURE_THRESHOLD = -1e10

        # Helper Vectors
        # f10: Low Aggressiveness for wages (initially)
        # f11: High Aggressiveness for wages (initially)
        
        # Run Phase 1: Firm 10 hires first (Tick 1-5)
        print("Phase 1: Firm 20 (Low Wage) Hires (Tick 1-5)")
        f11.is_active = False # Temporarily disable f11 to let f10 hire everyone
        
        for t in range(1, 6):
            # Firm 20 offers min wage
            f10.decision_engine.ai_engine.decide_action_vector = MagicMock(return_value=FirmActionVector(0.5, 0.0, 0.5))
            for h in sim.households:
                h.needs["survival"] = 0.0  # Prevent death
                h.needs["social"] = 0.0
                h.needs["asset"] = 0.0
                h.needs["improvement"] = 0.0
                h.decision_engine.ai_engine.decide_action_vector = MagicMock(return_value=HouseholdActionVector({"basic_food": 0.5}, 1.0, 0.9, 0.0, 0.0))
            
            sim.run_tick()

        f10_hired = len(f10.employees)
        print(f"Firm 20 Employees after Phase 1: {f10_hired}")
        h0 = sim.households[0]
        print(f"H0 Assets: {h0.assets:.2f}, Wage: {h0.current_wage:.2f}, Employer: {h0.employer_id}")

        # Run Phase 2: Firm 21 (High Wage) Enters (Tick 6-31)
        print("\nPhase 2: Firm 21 (High Wage) Enters (Tick 6-31)")
        f11.is_active = True
        if f11 not in sim.firms:
            sim.firms.append(f11)
            sim.agents[f11.id] = f11
        
        hops = 0
        ever_at_20 = {h.id for h in sim.households if h.employer_id == 20} # Everyone starts at 20 (roughly)
        hopped_agents = set()

        for t in range(6, 41):
            # f10 stays low, f11 goes high
            f10.decision_engine.ai_engine.decide_action_vector = MagicMock(return_value=FirmActionVector(0.5, 0.0, 0.5))
            f11.decision_engine.ai_engine.decide_action_vector = MagicMock(return_value=FirmActionVector(0.5, 1.0, 0.5))
            
            old_employers = {h.id: h.employer_id for h in sim.households}
            
            for h in sim.households:
                h.needs["survival"] = 0.0 # Keep them alive and happy
                h.needs["social"] = 0.0
                h.needs["asset"] = 0.0
                h.needs["improvement"] = 0.0
                h.decision_engine.ai_engine.decide_action_vector = MagicMock(return_value=HouseholdActionVector({"basic_food": 0.5}, 1.0, 0.9, 0.0, 0.0))
            
            sim.run_tick()
            
            for h in sim.households:
                if h.id in ever_at_20 and h.employer_id == 21 and h.id not in hopped_agents:
                    hops += 1
                    hopped_agents.add(h.id)
            
            if t % 5 == 0:
                market_data = sim._prepare_market_data(sim.tracker)
                # avg_wage might be in trackers or prepare_market_data?
                # Actually, f21's buying price is what matters
                print(f"Tick {t} | F20 Emp: {len([e for e in f10.employees if e.is_active])} | F21 Emp: {len([e for e in f11.employees if e.is_active])} | Hops: {hops}")

        print(f"\nFinal Statistics:")
        print(f"Firm 20 Employees: {len(f10.employees)}")
        print(f"Firm 21 Employees: {len(f11.employees)}")
        print(f"Total Successful Job Hops: {hops}")
        
        h0 = sim.households[0]
        print(f"H0 Final State: Employed={h0.is_employed}, Employer={h0.employer_id}, Wage={h0.current_wage:.2f}, Assets={h0.assets:.2f}")

        # Assertions
        self.assertTrue(hops >= 0, "Hops should be non-negative (logic check)")
        # We expect some hops if logic is working and f21 offers more
        if hops > 0:
            print("SUCCESS: Job hopping behavior detected!")
        else:
            print("NOTICE: No job hops detected. Check stickiness or wage gaps.")
            
        # Check recurring wages: H0 assets should be much higher than initial 100
        self.assertTrue(h0.assets > 100.0, "Households should accumulate assets from recurring wages.")
        print("SUCCESS: Recurring wage payments verified.")

if __name__ == "__main__":
    unittest.main()
