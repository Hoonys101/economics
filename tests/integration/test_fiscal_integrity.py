
import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from simulation.bank import Bank
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.system import FinanceSystem
from simulation.core_agents import Household
from simulation.models import Transaction

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

def test_infrastructure_investment_generates_transactions_and_issues_bonds():
    # Setup
    config = MockConfig()
    settlement_system = SettlementSystem()

    gov = Government(id=1, initial_assets=1000.0, config_module=config)
    gov.settlement_system = settlement_system

    bank = Bank(id=2, initial_assets=10000.0, config_manager=config, settlement_system=settlement_system)
    bank.settlement_system = settlement_system
    bank.set_government(gov) # Bank needs gov reference

    central_bank = MagicMock()
    central_bank.get_base_rate.return_value = 0.05

    finance_system = FinanceSystem(gov, central_bank, bank, config, settlement_system)
    gov.finance_system = finance_system

    # Setup Households for Public Works
    h1 = MagicMock(spec=Household)
    h1.id = 101
    h1.is_active = True
    h1.assets = 0.0

    households = [h1]

    # Check Initial State
    initial_gov_assets = gov.assets
    initial_bank_assets = bank.assets

    # Cost 5000. Gov has 1000. Deficit 4000.
    # Gov should issue 4000 bonds (synchronous).
    # Then create transactions for 5000.

    transactions = gov.invest_infrastructure(current_tick=1, households=households)

    # Verification

    # 1. Bond Issuance (Synchronous)
    # Gov assets should have increased by 4000 (to cover deficit)
    # NOTE: invest_infrastructure calculates 'needed' and calls issue_treasury_bonds_synchronous.
    # This transfers 4000 from Bank to Gov immediately.
    # The SPENDING (5000) is returned as transactions, NOT executed immediately.
    # So Gov assets should be 1000 + 4000 = 5000.

    assert gov.assets == 5000.0
    assert bank.assets == 6000.0 # 10000 - 4000

    # 2. Transactions
    # TD-177: Transactions now include bond purchase (4000) and infrastructure spending (5000)
    assert len(transactions) > 0

    spending_txs = [tx for tx in transactions if tx.transaction_type == "infrastructure_spending"]
    bond_txs = [tx for tx in transactions if tx.transaction_type == "bond_purchase"]

    assert len(spending_txs) > 0
    total_payout = sum(tx.price * tx.quantity for tx in spending_txs)
    assert total_payout == 5000.0

    # Verify bond transactions were captured
    if bond_txs:
         total_raised = sum(tx.price * tx.quantity for tx in bond_txs)
         assert total_raised == 4000.0

    # 3. Transaction Details
    tx = spending_txs[0]
    assert tx.buyer_id == gov.id
    assert tx.seller_id == h1.id
    assert tx.transaction_type == "infrastructure_spending"

def test_education_spending_generates_transactions_only():
    # Setup
    config = MockConfig()
    settlement_system = SettlementSystem()

    gov = Government(id=1, initial_assets=100.0, config_module=config)
    gov.settlement_system = settlement_system
    gov.revenue_this_tick = 10000.0 # High revenue to trigger high budget
    # Budget = 10000 * 0.2 = 2000.

    bank = Bank(id=2, initial_assets=10000.0, config_manager=config, settlement_system=settlement_system)
    bank.settlement_system = settlement_system
    bank.set_government(gov)

    central_bank = MagicMock()
    central_bank.get_base_rate.return_value = 0.05
    finance_system = FinanceSystem(gov, central_bank, bank, config, settlement_system)
    gov.finance_system = finance_system

    # Setup Household
    household = MagicMock() # spec=Household removed to avoid AttributeError on private attrs
    household.id = 10
    household._econ_state = MagicMock()
    household._econ_state.education_level = 0
    household._econ_state.assets = 100.0
    household._bio_state = MagicMock()
    household._bio_state.is_active = True
    # Needed for education logic check
    household._bio_state.age = 20
    household._econ_state.talent.base_learning_rate = 1.0

    # Mock update methods since they might be called
    household.update_education = MagicMock()

    households = [household]

    # Execution
    # Cost for Level 1 is 500.
    # Gov Assets 100. Deficit 400.
    # Note: MinistryOfEducation does NOT perform synchronous bond issuance.
    # It relies on budget based on REVENUE, not current ASSETS.

    transactions = gov.run_public_education(households, config, current_tick=1)

    # Verification

    # 1. No Bond Issuance (Assets unchanged)
    assert gov.assets == 100.0
    assert bank.assets == 10000.0

    # 2. Transactions
    # Should be 1 transaction of 500 (Grant)
    assert len(transactions) == 1
    tx = transactions[0]
    assert tx.price == 500.0
    assert tx.buyer_id == gov.id
    assert tx.transaction_type == "education_spending"

if __name__ == "__main__":
    test_infrastructure_investment_generates_transactions_and_issues_bonds()
    test_education_spending_generates_transactions_only()
