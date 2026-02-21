import pytest
from unittest.mock import MagicMock
from simulation.components.engines.hr_engine import HREngine
from simulation.components.engines.sales_engine import SalesEngine
from simulation.components.engines.finance_engine import FinanceEngine
from simulation.components.engines.production_engine import ProductionEngine
from simulation.components.state.firm_state_models import HRState, SalesState, FinanceState, ProductionState
from simulation.dtos.hr_dtos import HRPayrollContextDTO, TaxPolicyDTO
from simulation.dtos.sales_dtos import SalesPostAskContextDTO, SalesMarketingContextDTO
from simulation.dtos.context_dtos import FinancialTransactionContext
from modules.simulation.dtos.api import FirmConfigDTO
from simulation.models import Transaction, Order
from modules.system.api import DEFAULT_CURRENCY
from modules.firm.api import FirmSnapshotDTO, ProductionInputDTO, ProductionResultDTO, FinanceStateDTO, HRStateDTO, SalesStateDTO, ProductionStateDTO

class TestHREngine:
    def test_create_fire_transaction(self):
        engine = HREngine()
        hr_state = HRState()
        employee = MagicMock()
        employee.id = 101
        hr_state.employees.append(employee)

        # Test sufficient funds
        # severance_pay is 50000 pennies ($500.00)
        tx = engine.create_fire_transaction(
            hr_state, firm_id=1, wallet_balance=100000, employee_id=101, severance_pay=50000, current_time=10
        )
        assert tx is not None
        assert tx.buyer_id == 1
        assert tx.seller_id == 101
        assert tx.transaction_type == "severance"
        # Total pennies must match input
        assert tx.total_pennies == 50000
        # Price (float) must be pennies / 100.0
        assert tx.price == 500.0

        # Test insufficient funds
        tx_fail = engine.create_fire_transaction(
            hr_state, firm_id=1, wallet_balance=1000, employee_id=101, severance_pay=50000, current_time=10
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

        hr_state.employees.append(employee)
        hr_state.employee_wages[101] = 10000 # 100.00 pennies

        config = MagicMock(spec=FirmConfigDTO)
        config.halo_effect = 0.0
        config.severance_pay_weeks = 2.0
        config.ticks_per_year = 365

        context = HRPayrollContextDTO(
            exchange_rates={DEFAULT_CURRENCY: 1.0},
            tax_policy=TaxPolicyDTO(income_tax_rate=0.1, survival_cost=1000, government_agent_id=999),
            current_time=10,
            firm_id=1,
            wallet_balances={DEFAULT_CURRENCY: 100000}, # 1000.00
            labor_market_min_wage=1000, # 10.00
            ticks_per_year=365,
            severance_pay_weeks=2.0
        )

        result = engine.process_payroll(hr_state, context, config)
        transactions = result.transactions

        assert len(transactions) >= 1
        # Expect Wage + Tax
        wage_tx = next((t for t in transactions if t.transaction_type == "wage"), None)
        assert wage_tx is not None
        # Wage is 10000, Tax is 10000*0.1 = 1000. Net = 9000.
        assert wage_tx.total_pennies == 9000
        assert wage_tx.price == 90.0

        tax_tx = next((t for t in transactions if t.transaction_type == "tax"), None)
        assert tax_tx is not None
        assert tax_tx.total_pennies == 1000
        assert tax_tx.price == 10.0

class TestSalesEngine:
    def test_post_ask(self):
        engine = SalesEngine()
        state = SalesState()

        # Update to use price_pennies
        context = SalesPostAskContextDTO(
            firm_id=1,
            item_id="apple",
            price_pennies=1000, # 1000 pennies = $10.00
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
        # price_pennies should be 1000 (no multiplier)
        assert order.price_pennies == 1000
        assert order.price_limit == 10.0
        assert state.last_prices["apple"] == 1000

    def test_generate_marketing_transaction(self):
        engine = SalesEngine()
        state = SalesState()
        state.marketing_budget_pennies = 5000 # 5000 pennies = $50.00

        # Sufficient funds
        context = SalesMarketingContextDTO(
            firm_id=1,
            wallet_balance=10000,
            government_id=999,
            current_time=10
        )

        tx = engine.generate_marketing_transaction(state, context)
        assert tx is not None
        assert tx.buyer_id == 1
        assert tx.seller_id == 999
        assert tx.total_pennies == 5000
        assert tx.price == 50.0

        # Insufficient funds
        context_fail = SalesMarketingContextDTO(
            firm_id=1,
            wallet_balance=1000,
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
        config.firm_maintenance_fee = 1000 # 1000 pennies (converted inside engine)
        config.bailout_repayment_ratio = 0.1

        context = FinancialTransactionContext(
            government_id=999,
            tax_rates={},
            market_context={"exchange_rates": {DEFAULT_CURRENCY: 1.0}},
            shareholder_registry=None
        )

        # Test balances - using dict instead of Wallet object
        balances = {DEFAULT_CURRENCY: 2000} # 20.00

        # Inventory value 50.00 dollars -> 5000 pennies
        # holding cost 5000 * 0.1 = 500 pennies
        transactions = engine.generate_financial_transactions(
            state, firm_id=1, balances=balances, config=config, current_time=10, context=context, inventory_value=5000
        )

        # Expect Holding Cost + Maintenance
        # Maintenance 1000 pennies (10.0 * 100). Holding 500 pennies.
        # Total cost 1500. Balance 2000. OK.

        assert len(transactions) >= 2
        holding_tx = next((t for t in transactions if t.item_id == "holding_cost"), None)
        assert holding_tx.total_pennies == 500
        assert holding_tx.price == 5.0

        maint_tx = next((t for t in transactions if t.item_id == "firm_maintenance"), None)
        assert maint_tx.total_pennies == 1000
        assert maint_tx.price == 10.0

class TestProductionEngine:
    def test_produce_depreciation(self):
        engine = ProductionEngine()

        # Setup Snapshot
        config = MagicMock(spec=FirmConfigDTO)
        config.capital_depreciation_rate = 0.01 # 1%
        config.labor_alpha = 0.5
        config.automation_labor_reduction = 0.5
        config.labor_elasticity_min = 0.1
        config.goods = {"GENERIC": {"quality_sensitivity": 0.5}}

        production_state = ProductionState()
        production_state.capital_stock = 100000 # 1000.00 pennies
        production_state.automation_level = 0.5
        production_state.specialization = "GENERIC"

        hr_state = HRState()
        # Mock employees
        emp = MagicMock()
        emp.get.return_value = 1.0 # skill
        hr_state.employees_data = {1: emp}

        finance_state = FinanceStateDTO(
            balance={}, revenue_this_turn={}, expenses_this_tick={}, consecutive_loss_turns=0, profit_history=[],
            altman_z_score=0, valuation=0, total_shares=0, treasury_shares=0, dividend_rate=0, is_publicly_traded=False, total_debt_pennies=0, average_interest_rate=0.0
        )
        sales_state = SalesStateDTO(
            inventory_last_sale_tick={}, price_history={}, brand_awareness=0, perceived_quality=0, marketing_budget=0
        )
        hr_dto = HRStateDTO(employees=[], employees_data={})

        production_dto = ProductionStateDTO(
            current_production=0, productivity_factor=1.0, production_target=0,
            capital_stock=100000, # int
            base_quality=1.0, automation_level=0.5, specialization="GENERIC",
            inventory={}, input_inventory={}, inventory_quality={}
        )

        hr_dto_mock = HRStateDTO(
            employees=[1],
            employees_data={1: {"skill": 1.0}}
        )

        snapshot = FirmSnapshotDTO(
            id=1, is_active=True, config=config,
            finance=finance_state, production=production_dto, sales=sales_state, hr=hr_dto_mock
        )

        input_dto = ProductionInputDTO(
            firm_snapshot=snapshot,
            productivity_multiplier=1.0
        )

        result = engine.produce(input_dto)

        # Check Depreciation
        # 100000 * 0.01 = 1000.
        assert result.capital_depreciation == 1000 # int check
        assert isinstance(result.capital_depreciation, int)
