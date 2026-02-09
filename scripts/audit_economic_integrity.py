
import logging
import sys
import os

# Ensure we can import modules
sys.path.append(os.getcwd())

from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import RealEstateUnit, Share, Transaction, Talent
from modules.system.api import DEFAULT_CURRENCY
from simulation.api import MarketSnapshotDTO
from modules.household.api import HouseholdConfigDTO
from modules.common.config.api import GovernmentConfigDTO
from modules.simulation.api import AgentCoreConfigDTO
from simulation.ai.enums import Personality

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Audit")

def create_household_config_dto(**kwargs) -> HouseholdConfigDTO:
    defaults = {
        "survival_need_consumption_threshold": 50.0,
        "target_food_buffer_quantity": 2.0,
        "food_purchase_max_per_tick": 10.0,
        "assets_threshold_for_other_actions": 100.0,
        "wage_decay_rate": 0.01,
        "reservation_wage_floor": 5.0,
        "survival_critical_turns": 10.0,
        "labor_market_min_wage": 7.0,
        "household_low_asset_threshold": 50.0,
        "household_low_asset_wage": 7.0,
        "household_default_wage": 10.0,
        "market_price_fallback": 10.0,
        "need_factor_base": 1.0,
        "need_factor_scale": 1.0,
        "valuation_modifier_base": 1.0,
        "valuation_modifier_range": 0.2,
        "household_max_purchase_quantity": 20.0,
        "bulk_buy_need_threshold": 80.0,
        "bulk_buy_agg_threshold": 0.8,
        "bulk_buy_moderate_ratio": 0.5,
        "panic_buying_threshold": 0.9,
        "hoarding_factor": 1.5,
        "deflation_wait_threshold": -0.01,
        "delay_factor": 0.5,
        "dsr_critical_threshold": 0.4,
        "budget_limit_normal_ratio": 0.5,
        "budget_limit_urgent_need": 100.0,
        "budget_limit_urgent_ratio": 0.9,
        "min_purchase_quantity": 1.0,
        "job_quit_threshold_base": 0.5,
        "job_quit_prob_base": 0.1,
        "job_quit_prob_scale": 0.1,
        "stock_market_enabled": True,
        "household_min_assets_for_investment": 500.0,
        "stock_investment_equity_delta_threshold": 0.1,
        "stock_investment_diversification_count": 3,
        "expected_startup_roi": 0.2,
        "startup_cost": 1000.0,
        "debt_repayment_ratio": 0.1,
        "debt_repayment_cap": 0.5,
        "debt_liquidity_ratio": 0.2,
        "initial_rent_price": 500.0,
        "default_mortgage_rate": 0.05,
        "enable_vanity_system": True,
        "mimicry_factor": 0.1,
        "maintenance_rate_per_tick": 0.001,
        "goods": {"food": {}, "basic_food": {}, "luxury_food": {}},
        "household_consumable_goods": ["food", "basic_food", "luxury_food"],
        "value_orientation_mapping": {},
        "price_memory_length": 10,
        "wage_memory_length": 10,
        "ticks_per_year": 365,
        "adaptation_rate_normal": 0.1,
        "adaptation_rate_impulsive": 0.2,
        "adaptation_rate_conservative": 0.05,
        "conformity_ranges": {},
        "initial_household_assets_mean": 1000.0,
        "quality_pref_snob_min": 0.8,
        "quality_pref_miser_max": 0.2,
        "wage_recovery_rate": 0.1,
        "learning_efficiency": 0.5,
        "default_fallback_price": 10.0,
        "need_medium_threshold": 50.0,
        "housing_expectation_cap": 1000.0,
        "household_min_wage_demand": 7.0,
        "panic_selling_asset_threshold": 100.0,
        "perceived_price_update_factor": 0.1,
        "social_status_asset_weight": 0.5,
        "social_status_luxury_weight": 0.5,
        "leisure_coeffs": {},
        "base_desire_growth": 0.1,
        "max_desire_value": 100.0,
        "survival_need_death_threshold": 100.0,
        "assets_death_threshold": -100.0,
        "household_death_turns_threshold": 10,
        "survival_need_death_ticks_threshold": 10.0,
        "initial_wage": 10.0,
        "education_cost_multipliers": {},
        "survival_need_emergency_threshold": 80.0,
        "primary_survival_good_id": "food",
        "survival_bid_premium": 0.2,
        "elasticity_mapping": {"DEFAULT": 1.0},
        "max_willingness_to_pay_multiplier": 1.5,
        "initial_household_age_range": (20.0, 60.0),
        "initial_aptitude_distribution": (0.5, 0.15),
        "emergency_liquidation_discount": 0.8,
        "emergency_stock_liquidation_fallback_price": 8.0,
        "distress_grace_period_ticks": 5,
        "ai_epsilon_decay_params": (0.5, 0.05, 700),
        "housing_npv_horizon_years": 10,
        "housing_npv_risk_premium": 0.02,
        "mortgage_default_down_payment_rate": 0.2,
        "age_death_probabilities": {60: 0.01, 70: 0.02, 80: 0.05, 90: 0.15, 100: 0.50},
        "fallback_survival_cost": 10.0,
        "base_labor_skill": 1.0,
    }
    defaults.update(kwargs)
    return HouseholdConfigDTO(**defaults)

class MockConfig:
    def __init__(self):
        self.DEFAULT_FALLBACK_PRICE = 10.0
        self.INHERITANCE_TAX_RATE = 0.4
        self.INHERITANCE_DEDUCTION = 0.0 # Simplify for test
        self.sales_tax_rate = 0.10

class MockDecisionEngine:
    def __init__(self):
        self.loan_market = None
        self.logger = logger

    def make_decisions(self, context, macro_context):
        return [], (None, None)

def create_household(id, config):
    core_config = AgentCoreConfigDTO(
        id=id,
        name=f"Household_{id}",
        value_orientation="Asset-Oriented",
        initial_needs={"survival": 0.0},
        logger=logger,
        memory_interface=None
    )
    talent = Talent(base_learning_rate=0.1, max_potential={})
    return Household(
        core_config=core_config,
        engine=MockDecisionEngine(),
        talent=talent,
        goods_data=[],
        personality=Personality.BALANCED,
        config_dto=config
    )

class MockMarket:
    def get_daily_avg_price(self, item_id):
        return 100.0

class MockTransactionProcessor:
    def __init__(self):
        self.executed_transactions = []

    def execute(self, simulation, transactions):
        results = []
        for tx in transactions:
            self.executed_transactions.append(tx)
            # Mock success
            class Result:
                success = True
            results.append(Result())

            # Simulate side effects for transfer
            if tx.transaction_type == "asset_liquidation":
                if "stock" in tx.item_id:
                     firm_id = int(tx.item_id.split("_")[1])
                     seller = simulation.agents.get(tx.seller_id)
                     if seller and firm_id in seller._econ_state.portfolio.holdings:
                         del seller._econ_state.portfolio.holdings[firm_id]
                elif "real_estate" in tx.item_id:
                     unit_id = int(tx.item_id.split("_")[2])
                     seller = simulation.agents.get(tx.seller_id)
                     if seller and unit_id in seller._econ_state.owned_properties:
                         seller._econ_state.owned_properties.remove(unit_id)
            elif tx.transaction_type == "tax" or tx.transaction_type == "escheatment" or tx.transaction_type == "inheritance_distribution":
                 pass

        return results

class MockSimulation:
    def __init__(self):
        self.time = 1
        self.stock_market = MockMarket()
        self.transaction_processor = MockTransactionProcessor()
        self.agents = {}
        self.real_estate_units = []
        self.settlement_system = None # Should not be used directly

def test_sales_tax_atomicity():
    logger.info("--- Testing Sales Tax Atomicity ---")

    config = MockConfig()
    commerce_system = CommerceSystem(config)

    # 1. Test Insolvent Case (Cash = Price, but Tax exists)
    hh_poor = create_household(1, create_household_config_dto())
    hh_poor._econ_state.wallet.load_balances({DEFAULT_CURRENCY: 100.0})
    hh_poor._bio_state.is_active = True
    hh_poor._bio_state.needs["survival"] = 0.0 # Force buy

    # Mock context
    context = {
        "households": [hh_poor],
        "breeding_planner": type("MockPlanner", (), {
            "decide_consumption_batch": lambda self, h, m: {
                'consume': [0.0],
                'buy': [1.0], # Try to buy 1 unit
                'price': 100.0
            }
        })(),
        "market_data": {},
        "time": 1,
        "sales_tax_rate": 0.10,
        "government": type("MockGov", (), {"id": 999999})()
    }

    plans, txs = commerce_system.plan_consumption_and_leisure(context)

    if len(txs) > 0:
        logger.error(f"FAIL: Transaction generated for insolvent household! Cash: 100, Price: 100, Tax: 10%. Cost: 110.")
        return False
    else:
        logger.info("PASS: Insolvent household correctly denied purchase.")

    # 2. Test Solvent Case (Cash = Price + Tax)
    hh_rich = create_household(2, create_household_config_dto())
    hh_rich._econ_state.wallet.load_balances({DEFAULT_CURRENCY: 110.0})
    hh_rich._bio_state.is_active = True

    context["households"] = [hh_rich]

    plans, txs = commerce_system.plan_consumption_and_leisure(context)

    if len(txs) == 1:
        logger.info("PASS: Solvent household allowed purchase.")
    else:
        logger.error(f"FAIL: Transaction NOT generated for solvent household!")
        return False

    return True

def test_inheritance_leaks():
    logger.info("--- Testing Inheritance Leaks ---")

    config = MockConfig()
    inheritance_manager = InheritanceManager(config)
    sim = MockSimulation()

    # Create Deceased
    deceased = create_household(1, create_household_config_dto())
    deceased._econ_state.wallet.load_balances({DEFAULT_CURRENCY: 1000.0})
    deceased._econ_state.portfolio.holdings = {
        101: Share(101, 1, 10.0, 100.0) # 10 shares, price 100 = 1000
    }
    deceased._econ_state.owned_properties.append(201)

    unit = RealEstateUnit(201, owner_id=1, estimated_value=10000.0)
    sim.real_estate_units.append(unit)
    sim.agents[1] = deceased

    # Create Government
    gov = Government(id=999999, initial_assets=0.0, config_module=config)

    # Initial Wealth Calculation
    initial_wealth = 1000.0 + 1000.0 + 10000.0 # Cash + Stock + RE = 12000

    # Run Process Death
    # Note: MockConfig has 40% tax rate, 0 deduction.
    # Tax = 12000 * 0.4 = 4800.
    # Cash is 1000. Needs 3800 more.
    # Will liquidate Stock (1000). Needs 2800 more.
    # Will liquidate RE (Value 10000 * 0.9 fire sale = 9000).
    # Total Cash raised = 1000 + 1000 + 9000 = 11000.
    # Pay Tax 4800. Remaining = 6200.
    # Distribute 6200 to Heirs (or Escheat).

    txs = inheritance_manager.process_death(deceased, gov, sim)

    # Analyze Transactions
    total_tax_paid = 0.0
    total_escheated = 0.0
    total_distributed = 0.0
    liquidation_proceeds = 0.0

    logger.info(f"Generated {len(txs)} transactions:")
    for tx in txs:
        logger.info(f"  {tx.transaction_type}: {tx.quantity} x {tx.price} = {tx.quantity * tx.price}")
        if tx.transaction_type == "tax":
            total_tax_paid += tx.quantity * tx.price
        elif tx.transaction_type == "escheatment":
            total_escheated += tx.quantity * tx.price
        elif tx.transaction_type == "inheritance_distribution":
            total_distributed += tx.quantity * tx.price
        elif tx.transaction_type == "asset_liquidation":
            liquidation_proceeds += tx.quantity * tx.price

    # Verify Logic
    # 1. Tax
    expected_tax = 12000.0 * 0.4
    if abs(total_tax_paid - expected_tax) > 0.1:
        logger.error(f"FAIL: Tax mismatch. Expected {expected_tax}, Got {total_tax_paid}")
        # Note: Depending on liquidation order/proceeds, tax might be limited by available cash if liquidation failed?
        # In our mock, execution succeeds.

    # 2. Total Value Conservation
    # Initial Wealth = 12000 (Valued at Market Price)
    # Real Estate Liquidation Loss = 10000 * 0.1 = 1000 (Fire Sale)
    # Expected Conserved Value = 11000.

    # Final destinations: Tax + Escheat + Distribution
    final_value = total_tax_paid + total_escheated + total_distributed

    # Note: Real Estate that was NOT liquidated (if any) would be transferred directly.
    # In this case, we needed to liquidate RE to pay tax.

    logger.info(f"Initial Wealth: {initial_wealth}")
    logger.info(f"Liquidation Proceeds: {liquidation_proceeds}")
    logger.info(f"Tax Paid: {total_tax_paid}")
    logger.info(f"Distributed/Escheated: {total_escheated + total_distributed}")
    logger.info(f"Final Cash Out: {final_value}")

    # Check if RE was removed from deceased
    if 201 in deceased.owned_properties:
         logger.error("FAIL: RE Unit 201 was liquidated but not removed from deceased ownership list (in memory object)!")
    else:
         logger.info("PASS: RE Unit correctly removed from deceased.")

    if len(deceased._econ_state.portfolio.holdings) > 0:
         logger.error("FAIL: Stock holdings were liquidated but not removed from deceased portfolio!")
    else:
         logger.info("PASS: Stock holdings correctly removed.")

    if abs(final_value - 11000.0) < 0.1:
        logger.info("PASS: Value conserved (Accounting for fire sale loss).")
        return True
    else:
        logger.error(f"FAIL: Value Leak! Expected 11000, Got {final_value}")
        return False

if __name__ == "__main__":
    success_tax = test_sales_tax_atomicity()
    success_inh = test_inheritance_leaks()

    if success_tax and success_inh:
        print("AUDIT PASS")
        sys.exit(0)
    else:
        print("AUDIT FAIL")
        sys.exit(1)
