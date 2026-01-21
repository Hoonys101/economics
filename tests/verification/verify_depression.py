import logging
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from simulation.components.finance_department import FinanceDepartment
from simulation.decisions.corporate_manager import CorporateManager
from simulation.firms import Firm
from simulation.dtos import DecisionContext, StressScenarioConfig
from simulation.schemas import FirmActionVector
from simulation.systems.reflux_system import EconomicRefluxSystem
from simulation.ai.enums import Personality

logger = logging.getLogger("Phase29Verify")
logging.basicConfig(level=logging.INFO)

# Mock Config
class MockConfig:
    def __init__(self):
        self.PROFIT_HISTORY_TICKS = 10
        self.CORPORATE_TAX_RATE = 0.2
        self.FIRM_MAINTENANCE_FEE = 50.0
        self.BAILOUT_REPAYMENT_RATIO = 0.5
        self.VALUATION_PER_MULTIPLIER = 10.0
        self.GOODS = {"widget": {"production_cost": 10.0, "initial_price": 20.0, "inputs": {}}}
        self.AUTOMATION_COST_PER_PCT = 1000.0
        self.AUTOMATION_TAX_RATE = 0.05
        self.STARTUP_COST = 30000.0
        self.SEO_TRIGGER_RATIO = 0.5
        self.SEO_MAX_SELL_RATIO = 0.10
        self.LABOR_ALPHA = 0.7
        self.AUTOMATION_LABOR_REDUCTION = 0.5
        self.LABOR_MARKET_MIN_WAGE = 10.0
        self.SEVERANCE_PAY_WEEKS = 4
        self.ALTMAN_Z_SCORE_THRESHOLD = 1.81
        self.DIVIDEND_SUSPENSION_LOSS_TICKS = 3
        self.DIVIDEND_RATE_MIN = 0.1
        self.DIVIDEND_RATE_MAX = 0.5
        self.MAX_SELL_QUANTITY = 100
        self.FIRM_SAFETY_MARGIN = 2000.0
        self.CAPITAL_TO_OUTPUT_RATIO = 2.0
        self.SYSTEM2_HORIZON = 100
        self.SYSTEM2_DISCOUNT_RATE = 0.98
        self.SYSTEM2_TICKS_PER_CALC = 10
        self.scenario = StressScenarioConfig() # Default inactive

    def get(self, key, default=None):
        return getattr(self, key, default)

def test_phase29_depression_simulation():
    """
    Stress-test FinanceDepartment and CorporateManager under Phase 29 Depression scenario.
    """
    config = MockConfig()

    # 1. Activate Phase 29 Scenario
    config.scenario.is_active = True
    config.scenario.scenario_name = "Phase 29 - The Great Depression"
    config.scenario.base_interest_rate_multiplier = 3.0
    config.scenario.corporate_tax_rate_delta = 0.1
    config.scenario.demand_shock_multiplier = 0.7

    # 2. Setup Firm and Dependencies
    firm = MagicMock(spec=Firm)
    firm.id = 1
    firm.assets = 10000.0
    firm.capital_stock = 5000.0
    firm.inventory = {"widget": 100}
    firm.last_prices = {"widget": 20.0}
    firm.production_target = 100
    firm.specialization = "widget"
    firm.automation_level = 0.0
    firm.productivity_factor = 1.0
    firm.base_quality = 1.0
    firm.dividend_rate = 0.2
    firm.total_shares = 1000
    firm.treasury_shares = 0
    firm.system2_planner = None
    firm.research_history = {"total_spent": 0.0, "success_count": 0}
    firm.logger = logger
    firm.hr = MagicMock()
    firm.hr.employees = []
    firm.hr.employee_wages = {}
    firm.sales = MagicMock()
    firm.production = MagicMock()
    firm.personality = Personality.BALANCED

    # Create Real FinanceDepartment
    finance = FinanceDepartment(firm, config)
    firm.finance = finance

    # Create Real CorporateManager
    corp_manager = CorporateManager(config, logger)

    # 3. Setup Context
    context = MagicMock(spec=DecisionContext)
    context.current_time = 0
    context.market_data = {"widget": {"avg_price": 20.0}}
    context.markets = {"widget": MagicMock()}
    context.government = MagicMock()
    context.reflux_system = MagicMock(spec=EconomicRefluxSystem)

    # Mock Loan Market Data for Interest Calculation
    # We need to simulate interest expense. The scenario multiplier affects the BANK base rate,
    # which in turn affects loan rates.
    # Here we manually simulate the impact on expenses.

    # Simulate a debt
    loan_principal = 5000.0
    finance.add_liability(loan_principal, interest_rate=0.05) # 5% base

    # 4. Run Simulation for 20 Ticks
    z_score_history = []
    dividend_history = []

    logger.info("Starting Phase 29 Simulation...")

    for tick in range(20):
        context.current_time = tick

        # --- A. Simulate Shock Effects ---

        # 1. Interest Rate Shock: 3x Multiplier
        # Assume 5% base rate -> 15% effective rate (0.15 annual? Tick rate needs adjustment)
        # Using tick-rate approximation for test visibility
        base_tick_rate = 0.001
        effective_rate = base_tick_rate * config.scenario.base_interest_rate_multiplier
        interest_expense = loan_principal * effective_rate

        firm.finance.record_expense(interest_expense)
        firm.assets -= interest_expense # Cash outflow

        # 2. Demand Shock: 30% reduction in Sales
        # Assume normal sales would be 1000.0 revenue
        normal_revenue = 1000.0
        shocked_revenue = normal_revenue * config.scenario.demand_shock_multiplier
        firm.finance.record_revenue(shocked_revenue)
        firm.assets += shocked_revenue

        # 3. Tax Shock: +10%p
        config.CORPORATE_TAX_RATE = 0.2 + config.scenario.corporate_tax_rate_delta # 0.3

        # --- B. Run Corporate Manager ---

        action_vector = FirmActionVector(
            rd_aggressiveness=0.5,
            capital_aggressiveness=0.5,
            hiring_aggressiveness=0.5,
            dividend_aggressiveness=0.5,
            debt_aggressiveness=0.5,
            sales_aggressiveness=0.5
        )

        # Execute Decisions
        corp_manager.realize_ceo_actions(firm, context, action_vector)

        # --- C. Financial Maintenance ---
        firm.finance.check_bankruptcy()
        firm.finance.pay_taxes(context.government, tick)

        # --- D. Observations ---
        z_score = firm.finance.calculate_altman_z_score()
        z_score_history.append(z_score)
        dividend_history.append(firm.dividend_rate)

        # Reset tick counters (normally handled by TickScheduler)
        firm.finance.revenue_this_tick = 0
        firm.finance.expenses_this_tick = 0
        firm.finance.revenue_this_turn = 0
        firm.finance.cost_this_turn = 0


    # 5. Verification

    # Force distress to verify dividend suspension logic explicitly if not triggered naturally
    firm.finance.retained_earnings = -5000.0
    firm.finance.consecutive_loss_turns = 5

    corp_manager.realize_ceo_actions(firm, context, action_vector)

    if firm.dividend_rate == 0.0:
        logger.info("Verification Passed: Dividend Suspended under distress.")
    else:
        logger.error(f"Dividend NOT suspended! Rate: {firm.dividend_rate}")
        raise AssertionError("Dividend should be suspended!")

    assert all(isinstance(z, float) for z in z_score_history)

    logger.info("=== Phase 29 Validation Complete ===")
    logger.info(f"Final Z-Score: {z_score_history[-1]:.2f}")
    logger.info(f"Dividend Rate: {firm.dividend_rate}")

if __name__ == "__main__":
    test_phase29_depression_simulation()
