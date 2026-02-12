import pytest
from unittest.mock import MagicMock, Mock
from simulation.components.engines.hr_engine import HREngine
from simulation.components.engines.sales_engine import SalesEngine
from simulation.components.engines.finance_engine import FinanceEngine
from simulation.components.state.firm_state_models import HRState, SalesState, FinanceState
from simulation.dtos.hr_dtos import HRPayrollContextDTO, TaxPolicyDTO
from simulation.dtos.sales_dtos import SalesPostAskContextDTO, SalesMarketingContextDTO
from simulation.dtos.context_dtos import FinancialTransactionContext
from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.models import Transaction, Order
from modules.system.api import DEFAULT_CURRENCY

class TestHREngine:
    def test_create_fire_transaction(self):
        engine = HREngine()
        hr_state = HRState()
        employee = MagicMock()
        employee.id = 101
        hr_state.employees.append(employee)

        # Test sufficient funds
        tx = engine.create_fire_transaction(
            hr_state, firm_id=1, wallet_balance=1000.0, employee_id=101, severance_pay=500.0, current_time=10
        )
        assert tx is not None
        assert tx.buyer_id == 1
        assert tx.seller_id == 101
        assert tx.price == 500.0
        assert tx.transaction_type == "severance"

        # Test insufficient funds
        tx_fail = engine.create_fire_transaction(
            hr_state, firm_id=1, wallet_balance=100.0, employee_id=101, severance_pay=500.0, current_time=10
        )
        assert tx_fail is None

    def test_process_payroll(self):
        engine = HREngine()
        hr_state = HRState()
        employee = MagicMock()
        employee.id = 101
        employee.employer_id = 1
        employee.is_employed = True
        employee.labor_skill = 1.0
        employee.education_level = 0.0
        # Initialize mutable lists/dicts on MagicMock to avoid interaction issues if code iterates/updates them
        # Actually hr_state is real object, employee is mock.
        hr_state.employees.append(employee)
        hr_state.employee_wages[101] = 100.0

        config = MagicMock(spec=FirmConfigDTO)
        config.halo_effect = 0.0
        config.severance_pay_weeks = 2.0
        config.ticks_per_year = 365

        context = HRPayrollContextDTO(
            exchange_rates={DEFAULT_CURRENCY: 1.0},
            tax_policy=TaxPolicyDTO(income_tax_rate=0.1, survival_cost=10.0, government_agent_id=999),
            current_time=10,
            firm_id=1,
            wallet_balances={DEFAULT_CURRENCY: 1000.0},
            labor_market_min_wage=10.0,
            ticks_per_year=365,
            severance_pay_weeks=2.0
        )

        result = engine.process_payroll(hr_state, context, config)
        transactions = result.transactions

        assert len(transactions) >= 1
        # Expect Wage + Tax
        wage_tx = next((t for t in transactions if t.transaction_type == "wage"), None)
        assert wage_tx is not None
        # Wage is 100, Tax is 100*0.1 = 10. Net = 90.
        assert wage_tx.price == 90.0

        tax_tx = next((t for t in transactions if t.transaction_type == "tax"), None)
        assert tax_tx is not None
        assert tax_tx.price == 10.0

class TestSalesEngine:
    def test_post_ask(self):
        engine = SalesEngine()
        state = SalesState()

        context = SalesPostAskContextDTO(
            firm_id=1,
            item_id="apple",
            price=10.0,
            quantity=5.0,
            market_id="goods_market",
            current_tick=10,
            inventory_quantity=3.0, # Less than quantity
            brand_snapshot={}
        )

        order = engine.post_ask(state, context)

        assert order.agent_id == 1
        assert order.item_id == "apple"
        assert order.quantity == 3.0 # Limited by inventory
        assert order.price_limit == 10.0
        assert state.last_prices["apple"] == 10.0

    def test_generate_marketing_transaction(self):
        engine = SalesEngine()
        state = SalesState()
        state.marketing_budget_pennies = 50

        # Sufficient funds
        context = SalesMarketingContextDTO(
            firm_id=1,
            wallet_balance=100.0,
            government_id=999,
            current_time=10
        )

        tx = engine.generate_marketing_transaction(state, context)
        assert tx is not None
        assert tx.buyer_id == 1
        assert tx.seller_id == 999
        assert tx.price == 50.0

        # Insufficient funds
        context_fail = SalesMarketingContextDTO(
            firm_id=1,
            wallet_balance=10.0,
            government_id=999,
            current_time=10
        )
        tx_fail = engine.generate_marketing_transaction(state, context_fail)
        assert tx_fail is None

class TestFinanceEngine:
    def test_generate_financial_transactions(self):
        engine = FinanceEngine()
        state = FinanceState()
        config = MagicMock(spec=FirmConfigDTO)
        config.inventory_holding_cost_rate = 0.1
        config.firm_maintenance_fee = 10.0 # 1000 pennies
        config.bailout_repayment_ratio = 0.1

        context = FinancialTransactionContext(
            government_id=999,
            tax_rates={},
            market_context={"exchange_rates": {DEFAULT_CURRENCY: 1.0}},
            shareholder_registry=None
        )

        # Test balances - using dict instead of Wallet object
        balances = {DEFAULT_CURRENCY: 2000} # 20.00

        # Inventory value 50.00 -> holding cost 5.00 -> 500 pennies
        transactions = engine.generate_financial_transactions(
            state, firm_id=1, balances=balances, config=config, current_time=10, context=context, inventory_value=50.0
        )

        # Expect Holding Cost + Maintenance
        # Maintenance 1000 pennies. Holding 500 pennies.
        # Total cost 1500. Balance 2000. OK.

        assert len(transactions) >= 2
        holding_tx = next((t for t in transactions if t.item_id == "holding_cost"), None)
        assert holding_tx.price == 500

        maint_tx = next((t for t in transactions if t.item_id == "firm_maintenance"), None)
        assert maint_tx.price == 1000
