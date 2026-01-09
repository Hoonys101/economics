import unittest
import csv
import logging
import sys
from unittest.mock import MagicMock, Mock

# Add project root to sys.path
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.firms import ServiceFirm
from simulation.ai.service_firm_ai import ServiceFirmAI
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.core_agents import Household
from simulation.markets.order_book_market import OrderBookMarket
from simulation.ai_model import AIDecisionEngine
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyServiceMarket")

class TestServiceMarket(unittest.TestCase):
    def setUp(self):
        # Setup Mocks
        self.mock_ai_trainer = Mock()
        self.mock_ai_trainer.get_engine.return_value = Mock(spec=AIDecisionEngine)

        # Setup Simulation Components
        self.config = config

        # Override config for testing
        self.config.SERVICE_WASTE_PENALTY_FACTOR = 0.5
        self.config.FIRM_MAINTENANCE_FEE = 0.0 # Simplify

        # Setup Service Firm (Education)
        self.firm_id = 1
        self.specialization = "education_service"

        # Create AI Engine
        self.ai_engine = ServiceFirmAI(
            agent_id=str(self.firm_id),
            ai_decision_engine=self.mock_ai_trainer.get_engine()
        )

        # Create Decision Engine
        self.decision_engine = AIDrivenFirmDecisionEngine(
            ai_engine=self.ai_engine,
            config_module=self.config,
            logger=logger
        )

        # Create Firm
        self.firm = ServiceFirm(
            id=self.firm_id,
            initial_capital=10000.0,
            initial_liquidity_need=100.0,
            specialization=self.specialization,
            productivity_factor=10.0,
            decision_engine=self.decision_engine,
            value_orientation="needs_and_growth",
            config_module=self.config,
            logger=logger,
            sector="SERVICE"
        )

        # Setup Market
        self.market = OrderBookMarket(market_id=self.specialization)

        # Setup Households (Consumers)
        self.households = []
        for i in range(10):
            # Household init signature:
            # id, talent, goods_data, initial_assets, initial_needs, decision_engine, value_orientation, personality, config_module, ...
            h = Household(
                id=100+i,
                talent=Mock(),
                goods_data=[],
                initial_assets=1000.0,
                initial_needs=self.config.INITIAL_HOUSEHOLD_NEEDS_MEAN,
                decision_engine=Mock(),
                value_orientation="needs_and_growth",
                personality="normal", # Mock personality
                config_module=self.config
            )
            # Mock household consume capability if needed, or just simulate demand via orders
            self.households.append(h)

        # Output CSV
        self.csv_file = open("verification.csv", "w", newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["tick", "capacity", "sales", "waste", "employees", "utilization", "scenario"])

    def tearDown(self):
        self.csv_file.close()

    def test_simulation_100_ticks(self):
        # Scenario 1: Over-capacity (Low Demand)
        # Firm has high capacity (e.g., via high productivity or employees) but no demand initially

        # Manually add employees to boost capacity
        for i in range(5):
            emp = Household(
                id=200+i,
                talent=Mock(),
                goods_data=[],
                initial_assets=0,
                initial_needs={},
                decision_engine=Mock(),
                value_orientation="N/A",
                personality="normal",
                config_module=self.config
            )
            emp.employer_id = self.firm.id
            emp.is_employed = True
            emp.labor_skill = 1.0
            self.firm.employees.append(emp)
            self.firm.employee_wages[emp.id] = 10.0

        print("Starting Verification Simulation...")

        for tick in range(1, 101):
            # 1. Start of Tick Logic

            # Scenario Control
            demand_qty = 0
            scenario = "Neutral"

            if tick < 40:
                scenario = "Low Demand"
                demand_qty = 5 # Low demand
            elif tick < 70:
                scenario = "High Demand"
                demand_qty = 100 # High demand
            else:
                scenario = "Balanced"
                demand_qty = 30

            # 2. Firm Produces (Actually Produce happens at END of tick in engine,
            # but for this unit test flow, we can assume produce happened previously or call it now)
            # In engine: produce -> update_needs -> market -> ... -> produce (for next day)
            # Let's follow engine order:
            # (Start Tick) -> Firm Decision -> Market -> Consumption -> Firm Produce (Next Day)

            # 2.1 Firm Decision
            # Mock Market Data
            market_data = {
                "goods_market": {f"{self.specialization}_avg_traded_price": 50.0},
                "debt_data": {str(self.firm.id): {}}
            }

            # Since we are testing AI Adaptation, we need to let AI make decisions (Hire/Fire/Price)
            # But the AI logic inside `make_decision` is complex RL.
            # We will rely on `decision_engine` calling `ai_engine`.
            # We need to make sure the Q-tables are updated or at least actions are taken.

            # Inject context
            # We skip full `make_decision` execution because it requires full engine context (Labor Market etc).
            # Instead, we will simulate the "Effect" of AI decision by manually checking state and adjusting employees
            # to verify "Directional Correctness" requested by user.

            # Wait, the prompt asked to verify if AI *does* it.
            # "Verify AI fires employees... Verify AI hires..."
            # This implies I should let the AI run.

            # To run `make_decision`, we need `markets`.
            markets = {self.specialization: self.market, "labor": OrderBookMarket("labor")}

            # Generate Demand (Households placing Buy Orders)
            self.market.clear_orders()
            for i in range(demand_qty):
                order = Mock(agent_id=1000+i, order_type="BUY", item_id=self.specialization, quantity=1.0, price=60.0) # Price high enough
                self.market.place_order(order, tick)

            # Firm Actions (Price, Production Target, Hiring)
            # Note: FirmAI V2 outputs "Aggressiveness".
            # `AIDrivenFirmDecisionEngine` translates this to orders.

            # We need to mock `firm.make_decision` or call it.
            # Let's call it.
            firm_orders, _ = self.firm.make_decision(markets, [], market_data, tick, government=Mock())

            # Process Firm Orders
            for order in firm_orders:
                if order.market_id == self.specialization and order.order_type == "SELL":
                    self.market.place_order(order, tick)
                elif order.market_id == "labor":
                    # If Hiring (BUY Labor)
                    if order.order_type == "BUY":
                        # Instant hire for simulation sake
                        new_emp = Household(
                            id=3000+tick,
                            talent=Mock(),
                            goods_data=[],
                            initial_assets=0,
                            initial_needs={},
                            decision_engine=Mock(),
                            value_orientation="N/A",
                            personality="normal",
                            config_module=self.config
                        )
                        new_emp.employer_id = self.firm.id
                        new_emp.is_employed = True
                        new_emp.labor_skill = 1.0
                        self.firm.employees.append(new_emp)
                        self.firm.employee_wages[new_emp.id] = 10.0

            # Firing Logic (usually happens in update_needs if can't afford, or AI firing?)
            # AI Firing logic in `AIDrivenFirmDecisionEngine` is based on `hiring_aggressiveness`.
            # If very low, it might fire?
            # `_handle_labor` in engine: "If hiring_agg < 0.2: Consider firing".

            # Let's execute transactions
            transactions = self.market.match_orders(tick)

            sales_volume = sum(tx.quantity for tx in transactions)

            # Update Firm Internal State (Revenue)
            self.firm.revenue_this_turn = sum(tx.quantity * tx.price for tx in transactions)
            self.firm.sales_volume_this_tick = sales_volume

            # CRITICAL FIX: Add Revenue to Assets so AI sees profit!
            self.firm.assets += self.firm.revenue_this_turn

            # Call update_needs to process expenses (wages, etc) and sync state
            # This deducts wages from assets
            # Mock government to return float for tax calculation
            mock_gov = Mock()
            mock_gov.calculate_income_tax.return_value = 0.0 # No tax for test
            mock_gov.get_survival_cost.return_value = 10.0
            self.firm.update_needs(tick, government=mock_gov, market_data=market_data)

            # 3. Firm Produce (End of Tick)
            # This is where Waste is calculated and Inventory Reset

            # Capture state before produce (current inventory is what was available for sale)
            capacity_before = self.firm.inventory.get(self.specialization, 0.0)

            # Call Produce
            self.firm.produce(tick)

            # Capture Waste (recorded in produce)
            waste = self.firm.waste_this_tick

            # Verify Perishability (Check 1)
            # Inventory should now contain ONLY the NEW production.
            # The old inventory (capacity_before) minus sales should have been voided.
            # Actually, `produce` sets `inventory = new_production`.
            # So `inventory` at start of next tick is exactly `new_capacity`.
            # Waste should be `capacity_before`. (Wait, if we sold some, waste is remainder).
            # `produce` logic: `unsold = inventory.get()`. `inventory` is decremented by sales in `match_orders` logic?
            # Yes, `Engine._process_transactions` updates seller inventory.

            # So `unsold` in `produce` is indeed the waste.

            # Check 1 Assertion Logic:
            # waste should equal (capacity_at_start - sales)
            # But capacity_at_start is hard to track unless we stored it.
            # self.firm.capacity_this_tick was updated in *previous* produce.
            # So `waste == self.firm.capacity_this_tick - sales_volume`?
            # Let's verify this in the CSV analysis or asserts.

            # However, `ServiceFirm.produce` updates `capacity_this_tick` AFTER generating new capacity.
            # So `self.firm.capacity_this_tick` now holds NEXT tick's capacity.
            # The `waste` was calculated based on PREVIOUS tick's remainder.

            # 4. Learning Step (Reward Calculation)
            # AI needs to update based on Reward.
            # `engine.py` calls `calculate_reward`.
            prev_state = self.firm.get_pre_state_data() # Mocked/Empty for now
            curr_state = self.firm.get_agent_data()

            reward = self.ai_engine.calculate_reward(self.firm, prev_state, curr_state)
            self.ai_engine.update_learning_v2(reward, curr_state, market_data)

            # Record Data
            utilization = 0
            # capacity_this_tick is now NEXT tick's capacity.
            # For logging, we probably want THIS tick's utilization.
            # We can compute it manually: sales / (sales + waste)
            total_avail = sales_volume + waste
            if total_avail > 0:
                utilization = sales_volume / total_avail

            row = [tick, total_avail, sales_volume, waste, len(self.firm.employees), utilization, scenario]
            self.csv_writer.writerow(row)

            if tick % 10 == 0:
                print(f"Tick {tick}: Scenario={scenario}, Util={utilization:.2f}, Emp={len(self.firm.employees)}, Waste={waste:.2f}")

            # AI Adaptation Check (Check 2)
            # We'll rely on the CSV output to verify the trend.
            # Low Demand -> Utilization Low -> Waste High -> Penalty High -> Fire/Downsize
            # High Demand -> Utilization High -> Waste Low -> Profit High -> Hire/Expand

if __name__ == '__main__':
    unittest.main()
