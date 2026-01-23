import logging
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.engine import Simulation
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.db.repository import SimulationRepository
import config
from simulation.ai.firm_ai import FirmAI
from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)


# Mock Repository
class MockRepository(SimulationRepository):
    def __init__(self):
        self.decisions = []

    def save_simulation_run(self, config_hash, description):
        return 1

    def update_simulation_run_end_time(self, run_id):
        pass

    def save_agent_states_batch(self, data):
        pass

    def save_transactions_batch(self, data):
        pass

    def save_economic_indicators_batch(self, data):
        pass

    def save_ai_decision(self, decision_data):
        self.decisions.append(decision_data)
        print(
            f"Recorded Decision: {decision_data.agent_id} | Type: {decision_data.decision_type} | Reward: {decision_data.actual_reward}"
        )

    def close(self):
        pass


# Mock AIEngineRegistry
class MockAIRegistry:
    def __init__(self):
        pass

    def end_episode(self, all_agents):
        pass


def run_verification():
    logging.basicConfig(level=logging.INFO)

    # 1. Setup
    repo = MockRepository()
    ai_registry = MockAIRegistry()

    # 1. Setup Firm
    firm_ai = FirmAI("firm_1", None)
    firm_engine = AIDrivenFirmDecisionEngine(firm_ai, config)
    firm = Firm(
        id=1,
        initial_capital=1000.0,
        initial_liquidity_need=10.0,
        specialization="basic_food",
        productivity_factor=1.0,
        decision_engine=firm_engine,
        value_orientation="wealth",
        config_module=config,
    )
    firm_ai.set_ai_decision_engine(firm.decision_engine)
    firm.inventory["basic_food"] = 10
    firm.production_target = 20

    # 2. Setup Household
    from simulation.core_agents import Talent
    from simulation.ai.api import Personality

    talent = Talent(base_learning_rate=0.1, max_potential={})
    household_ai = HouseholdAI("household_2", None)
    household_engine = AIDrivenHouseholdDecisionEngine(household_ai, config)

    household = Household(
        id=2,
        talent=talent,
        goods_data=[],
        initial_assets=1000.0,
        initial_needs={
            "survival": 50.0,
            "asset": 50.0,
            "social": 50.0,
            "improvement": 50.0,
        },
        decision_engine=household_engine,
        value_orientation="wealth",
        personality=Personality.MISER,
        config_module=config,
    )
    household_ai.set_ai_decision_engine(household.decision_engine)

    simulation = Simulation(
        households=[household],
        firms=[firm],
        ai_trainer=ai_registry,
        repository=repo,
        config_module=config,
        goods_data=[],  # Dummy
        logger=logging.getLogger("test"),
    )

    # Ensure markets are aligned
    simulation.markets["labor"] = simulation.markets["labor_market"]

    # 2. Run Tick 1 (Initial)
    print("\n--- Running Tick 1 ---")
    simulation.run_tick()

    # 3. Verify Orders
    print("\n--- Verification: Orders ---")
    market = simulation.markets["basic_food"]
    labor_market = simulation.markets["labor_market"]

    sell_orders = market.get_all_asks("basic_food")
    print(f"Firm Sell Orders: {len(sell_orders)}")
    if sell_orders:
        print(f"First Sell Order: Price={sell_orders[0].price}")

    buy_orders = labor_market.get_all_bids("labor")  # Firms BUY labor
    print(f"Firm Labor Buy Orders (Job Offers): {len(buy_orders)}")

    labor_asks = labor_market.get_all_asks("labor")  # Households SELL labor
    print(f"Household Labor Sell Orders: {len(labor_asks)}")

    # 4. Verify Learning Update
    print("\n--- Verification: Learning ---")
    # Simulation calls update_learning at end of tick
    # Check if decisions were recorded in MockRepository
    decisions = repo.decisions
    print(f"Total Recorded AI Decisions: {len(decisions)}")

    assert len(sell_orders) > 0, (
        "Firm should have placed a SELL order (Continuous Action)"
    )
    assert len(decisions) >= 2, "Both firm and household should have learned"
    assert decisions[0].decision_type == "VECTOR_V2", (
        "Decision type should be VECTOR_V2"
    )

    print("\nSUCCESS: AI Architecture V2 verified!")


if __name__ == "__main__":
    run_verification()
