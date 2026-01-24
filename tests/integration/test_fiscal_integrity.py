
import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from simulation.bank import Bank
from simulation.systems.reflux_system import EconomicRefluxSystem
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.system import FinanceSystem
from simulation.systems.ministry_of_education import MinistryOfEducation
from simulation.core_agents import Household

class MockConfig:
    TICKS_PER_YEAR = 100
    INFRASTRUCTURE_INVESTMENT_COST = 5000.0
    PUBLIC_EDU_BUDGET_RATIO = 0.2
    EDUCATION_COST_PER_LEVEL = {1: 500}
    SCHOLARSHIP_WEALTH_PERCENTILE = 0.2
    SCHOLARSHIP_POTENTIAL_THRESHOLD = 0.7
    GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    INCOME_TAX_RATE = 0.1
    CORPORATE_TAX_RATE = 0.2
    GOODS_INITIAL_PRICE = {"basic_food": 5.0}
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0

    def get(self, key, default=None):
        if key == "economy_params.DEBT_RISK_PREMIUM_TIERS": return {}
        if key == "economy_params.BOND_MATURITY_TICKS": return 400
        if key == "economy_params.QE_INTERVENTION_YIELD_THRESHOLD": return 0.10
        if key == "economy_params.BAILOUT_PENALTY_PREMIUM": 0.05
        if key == "economy_params.BAILOUT_COVENANT_RATIO": 0.5
        if key == "economy_params.STARTUP_GRACE_PERIOD_TICKS": return 24
        if key == "economy_params.ALTMAN_Z_SCORE_THRESHOLD": return 1.81
        return getattr(self, key, default)

def test_infrastructure_investment_is_zero_sum():
    # Setup
    config = MockConfig()
    settlement_system = SettlementSystem()

    gov = Government(id=1, initial_assets=1000.0, config_module=config)
    gov.settlement_system = settlement_system

    # Inject minimal dependencies for Government
    gov.finance_system = None # Will set later

    bank = Bank(id=2, initial_assets=10000.0, config_manager=config, settlement_system=settlement_system)
    bank.settlement_system = settlement_system
    bank.set_government(gov) # Bank needs gov reference

    reflux = EconomicRefluxSystem()

    central_bank = MagicMock()
    central_bank.get_base_rate.return_value = 0.05

    finance_system = FinanceSystem(gov, central_bank, bank, config, settlement_system)
    gov.finance_system = finance_system

    # Check Initial State
    initial_gov_assets = gov.assets
    initial_bank_assets = bank.assets
    initial_reflux_assets = reflux.assets
    initial_total = initial_gov_assets + initial_bank_assets + initial_reflux_assets

    print(f"\n[INIT] Gov: {gov.assets}, Bank: {bank.assets}, Reflux: {reflux.assets}")

    # Execution
    # Invest Infrastructure cost 5000. Gov has 1000. Deficit 4000.
    # Expectation:
    # 1. Gov issues bonds (synchronous) -> +4000 assets (from Bank).
    # 2. Gov pays Reflux -> -5000 assets.
    # Final Gov: 1000 + 4000 - 5000 = 0.

    # Note: Before the fix, this might return False (fail) or create deferred transactions.
    # If it creates deferred transactions, assets won't change immediately.

    success, txs = gov.invest_infrastructure(current_tick=1, reflux_system=reflux)

    print(f"[POST] Success: {success}, Txs: {len(txs)}")
    print(f"[POST] Gov: {gov.assets}, Bank: {bank.assets}, Reflux: {reflux.assets}")

    final_total = gov.assets + bank.assets + reflux.assets
    diff = final_total - initial_total

    # Assertions
    assert success, "Infrastructure investment should succeed with synchronous financing."
    assert abs(diff) < 1e-9, f"Zero-sum violation! Drift: {diff}"
    assert gov.assets == 0.0
    assert bank.assets == 6000.0
    assert reflux.assets == 5000.0

def test_education_spending_is_zero_sum():
    # Setup
    config = MockConfig()
    settlement_system = SettlementSystem()

    gov = Government(id=1, initial_assets=1000.0, config_module=config)
    gov.settlement_system = settlement_system
    gov.revenue_this_tick = 10000.0 # High revenue to trigger high budget
    # Budget = 10000 * 0.2 = 2000.

    bank = Bank(id=2, initial_assets=10000.0, config_manager=config, settlement_system=settlement_system)
    bank.settlement_system = settlement_system
    bank.set_government(gov)

    reflux = EconomicRefluxSystem()
    central_bank = MagicMock()
    central_bank.get_base_rate.return_value = 0.05
    finance_system = FinanceSystem(gov, central_bank, bank, config, settlement_system)
    gov.finance_system = finance_system

    # Setup Household
    household = MagicMock(spec=Household)
    household.id = 10
    household.education_level = 0
    household.assets = 100.0
    household.is_active = True
    household.settlement_system = settlement_system # Mock needs this?

    # We need a real Household or something that works with SettlementSystem
    # SettlementSystem calls withdraw/deposit on agents.
    # MagicMock works if configured.
    household.withdraw = MagicMock()
    household.deposit = MagicMock()

    households = [household]

    # Execution
    # Cost for Level 1 is 500. Budget is 2000.
    # Gov Assets 1000. Cost 500. Can pay directly.

    # Let's force deficit.
    gov._assets = 100.0
    # Cost 500. Deficit 400.
    # Should issue bonds for 400.

    initial_total = gov.assets + bank.assets + reflux.assets # Household mocked, assumed constant/ handled

    # Need to verify if Household assets are touched.
    # Level 0->1 is full grant (Gov pays Reflux). Household assets untouched.

    gov.run_public_education(households, config, current_tick=1, reflux_system=reflux)

    final_total = gov.assets + bank.assets + reflux.assets
    diff = final_total - initial_total

    # After fix
    # Gov should have issued 400 bonds. Assets 100 + 400 = 500.
    # Spent 500. Assets 0.
    # Bank assets 10000 - 400 = 9600.
    # Reflux assets 500.

    assert gov.assets == 0.0
    assert bank.assets == 9600.0
    assert reflux.assets == 500.0
    assert abs(diff) < 1e-9

if __name__ == "__main__":
    test_infrastructure_investment_is_zero_sum()
    test_education_spending_is_zero_sum()
