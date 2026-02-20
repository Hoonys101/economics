import pytest
from unittest.mock import MagicMock
from simulation.components.engines.finance_engine import FinanceEngine
from simulation.components.engines.hr_engine import HREngine
from modules.firm.api import (
    FinanceDecisionInputDTO, HRDecisionInputDTO, BudgetPlanDTO,
    FirmSnapshotDTO, FirmStrategy
)
from modules.simulation.dtos.api import FirmConfigDTO, FinanceStateDTO, HRStateDTO, ProductionStateDTO, SalesStateDTO
from modules.system.api import DEFAULT_CURRENCY

class TestFinanceEngine:
    @pytest.fixture
    def engine(self):
        return FinanceEngine()

    @pytest.fixture
    def mock_input(self):
        # Create full snapshot hierarchy
        fin_state = MagicMock(spec=FinanceStateDTO)
        fin_state.balance = {DEFAULT_CURRENCY: 100000}
        fin_state.total_debt_pennies = 0
        fin_state.profit_history = [5000]
        fin_state.dividend_rate = 0.1

        prod_state = MagicMock(spec=ProductionStateDTO)
        sales_state = MagicMock(spec=SalesStateDTO)
        hr_state = MagicMock(spec=HRStateDTO)

        snapshot = MagicMock(spec=FirmSnapshotDTO)
        snapshot.finance = fin_state
        snapshot.production = prod_state
        snapshot.sales = sales_state
        snapshot.hr = hr_state
        snapshot.strategy = FirmStrategy.PROFIT_MAXIMIZATION

        config = MagicMock(spec=FirmConfigDTO)

        return FinanceDecisionInputDTO(
            firm_snapshot=snapshot,
            market_snapshot=MagicMock(),
            config=config,
            current_tick=10,
            credit_rating=0.0
        )

    def test_plan_budget_basics(self, engine, mock_input):
        plan = engine.plan_budget(mock_input)

        assert isinstance(plan, BudgetPlanDTO)
        assert plan.total_budget_pennies == 100000
        assert plan.is_solvent == True

        # Check defaults logic
        # 60% labor, 20% capital (ProfitMax), 10% marketing
        assert plan.labor_budget_pennies == 60000
        assert plan.capital_budget_pennies == 20000

    def test_plan_budget_with_debt(self, engine, mock_input):
        mock_input.firm_snapshot.finance.total_debt_pennies = 1000000

        plan = engine.plan_budget(mock_input)

        # 1% repayment = 10000
        assert plan.debt_repayment_pennies == 10000
        assert plan.total_budget_pennies == 100000 # Balance
        # Available for ops = 90000

        # 60% of 90000
        assert plan.labor_budget_pennies == 54000

    def test_plan_budget_returns_integers(self, engine, mock_input):
        """Zero-Sum Boundary Check: Output must be quantized integer pennies."""
        mock_input.firm_snapshot.finance.balance = {DEFAULT_CURRENCY: 100001} # Odd number

        plan = engine.plan_budget(mock_input)

        assert isinstance(plan.total_budget_pennies, int)
        assert isinstance(plan.labor_budget_pennies, int)
        assert isinstance(plan.capital_budget_pennies, int)
        assert isinstance(plan.marketing_budget_pennies, int)
        assert isinstance(plan.dividend_payout_pennies, int)
        assert isinstance(plan.debt_repayment_pennies, int)

class TestHREngine:
    @pytest.fixture
    def engine(self):
        return HREngine()

    @pytest.fixture
    def mock_input(self):
        # Config
        config = MagicMock(spec=FirmConfigDTO)
        config.firm_min_employees = 1
        config.firm_max_employees = 100
        config.severance_pay_weeks = 2
        config.halo_effect = 0.0

        # State
        prod_state = MagicMock(spec=ProductionStateDTO)
        prod_state.specialization = "food"
        prod_state.production_target = 100
        prod_state.inventory = {"food": 0}
        prod_state.productivity_factor = 10.0
        # Needed labor = 100 / 10 = 10

        hr_state = MagicMock(spec=HRStateDTO)
        hr_state.employees = [1, 2, 3, 4, 5] # 5 employees
        hr_state.employees_data = {
            1: {"wage": 1000, "skill": 1.0},
            2: {"wage": 1000, "skill": 1.0},
            3: {"wage": 1000, "skill": 1.0},
            4: {"wage": 1000, "skill": 1.0},
            5: {"wage": 1000, "skill": 1.0},
        }

        fin_state = MagicMock(spec=FinanceStateDTO)
        fin_state.profit_history = [10000]

        snapshot = MagicMock(spec=FirmSnapshotDTO)
        snapshot.finance = fin_state
        snapshot.production = prod_state
        snapshot.hr = hr_state
        snapshot.id = 999

        budget = MagicMock(spec=BudgetPlanDTO)
        budget.labor_budget_pennies = 100000 # Plenty

        return HRDecisionInputDTO(
            firm_snapshot=snapshot,
            budget_plan=budget,
            market_snapshot=MagicMock(),
            config=config,
            current_tick=10,
            labor_market_avg_wage=1000
        )

    def test_manage_workforce_hiring(self, engine, mock_input):
        # Target = 10, Current = 5 -> Hire 5
        result = engine.manage_workforce(mock_input)

        assert len(result.hiring_orders) == 1
        order = result.hiring_orders[0]
        assert order.side == "BUY"
        assert order.quantity == 5.0
        assert order.market_id == "labor"

    def test_manage_workforce_firing(self, engine, mock_input):
        # Target = 2, Current = 5 -> Fire 3
        mock_input.firm_snapshot.production.production_target = 20
        # Needed = 20 / 10 = 2

        result = engine.manage_workforce(mock_input)

        assert len(result.hiring_orders) == 3 # Firing orders are returned in hiring_orders list (as orders)
        assert result.hiring_orders[0].side == "FIRE"
        assert len(result.firing_ids) == 3

    def test_manage_workforce_wage_scaling(self, engine, mock_input):
        """
        Verify that the offered wage scales with the market average wage.
        This confirms the fix for 'Logic & Spec Gaps: Disconnected Wage Logic'.
        """
        # Set market wage to 2000 (Non-default)
        # Mock input is a frozen dataclass, so we must replace it (or create new)
        # Actually HREngine uses input_dto.labor_market_avg_wage

        from dataclasses import replace
        new_input = replace(mock_input, labor_market_avg_wage=2000)

        # Ensure we need to hire
        new_input.firm_snapshot.production.production_target = 100 # Need 10, have 5

        result = engine.manage_workforce(new_input)

        assert len(result.hiring_orders) == 1
        order = result.hiring_orders[0]

        # Base wage 2000.
        # Profit premium calculation: avg_profit=10000.
        # profit_based_premium = 10000 / (2000 * 10) = 0.5
        # wage_premium = min(0.5 * 0.1, 2.0) = 0.05
        # offered = 2000 * 1.05 = 2100

        assert order.price_pennies == 2100
        assert order.price_limit == 21.0
