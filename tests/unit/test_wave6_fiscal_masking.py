import pytest
from unittest.mock import MagicMock
from typing import List, Dict, Any

from modules.government.taxation.system import TaxationSystem
from modules.government.dtos import TaxBracketDTO
from simulation.components.engines.hr_engine import HREngine
from modules.firm.api import HRDecisionInputDTO, HRDecisionOutputDTO, BudgetPlanDTO
from modules.simulation.dtos.api import FirmStateDTO, HRStateDTO, FinanceStateDTO, ProductionStateDTO, FirmConfigDTO
from modules.system.api import MarketSnapshotDTO
from simulation.models import Order

class TestFiscalMasking:
    def test_progressive_taxation_logic(self):
        """
        Verifies that TaxationSystem correctly calculates tax using descending thresholds
        when TaxBracketDTOs are provided.
        """
        # Setup brackets:
        # > 50000 @ 30%
        # > 10000 @ 20%
        # > 0     @ 10%
        brackets = [
            TaxBracketDTO(threshold=50000, rate=0.3),
            TaxBracketDTO(threshold=10000, rate=0.2),
            TaxBracketDTO(threshold=0, rate=0.1)
        ]

        # Test Case 1: Income 60,000
        # Exp:
        # > 50k: (60k-50k)*0.3 = 10k*0.3 = 3000
        # > 10k: (50k-10k)*0.2 = 40k*0.2 = 8000
        # > 0k:  (10k-0k) *0.1 = 10k*0.1 = 1000
        # Total: 12000

        system = TaxationSystem(config_module=MagicMock())

        income = 60000

        # Calling with named argument tax_brackets which will be added
        tax = system.calculate_income_tax(
            income=income,
            survival_cost=0,
            current_income_tax_rate=0.0, # Should be ignored if brackets are present
            tax_mode="PROGRESSIVE",
            tax_brackets=brackets
        )

        assert tax == 12000

    def test_wage_scaling_logic(self):
        """
        Verifies that HREngine.manage_workforce identifies underpaid employees
        and schedules wage updates.
        """
        engine = HREngine()

        # Mock Firm State
        hr_state = MagicMock(spec=HRStateDTO)
        hr_state.employees = [101, 102]
        # Mocking access to employees_data.
        # HRStateDTO is a dataclass, so attributes are accessible.
        hr_state.employees_data = {
            101: {'wage': 1000, 'skill': 1.0, 'education_level': 0}, # Underpaid
            102: {'wage': 5000, 'skill': 1.0, 'education_level': 0}  # Well paid
        }
        # Adaptive Learning History Mocks
        hr_state.target_hires_prev_tick = 0
        hr_state.hires_prev_tick = 0
        hr_state.wage_offer_prev_tick = 0

        firm_snapshot = MagicMock(spec=FirmStateDTO)
        firm_snapshot.id = 1
        firm_snapshot.hr = hr_state
        firm_snapshot.finance = MagicMock(spec=FinanceStateDTO)
        firm_snapshot.finance.profit_history = [10000] # Positive profit
        firm_snapshot.production = MagicMock(spec=ProductionStateDTO)
        firm_snapshot.production.productivity_factor = 1.0
        firm_snapshot.production.inventory = {}
        firm_snapshot.production.specialization = "widget"
        firm_snapshot.production.production_target = 10

        # Config
        config = MagicMock(spec=FirmConfigDTO)
        config.firm_min_employees = 1
        config.firm_max_employees = 100
        config.severance_pay_weeks = 2

        # Input DTO
        input_dto = HRDecisionInputDTO(
            firm_snapshot=firm_snapshot,
            budget_plan=MagicMock(spec=BudgetPlanDTO, labor_budget_pennies=100000),
            market_snapshot=MagicMock(spec=MarketSnapshotDTO),
            config=config,
            current_tick=100,
            labor_market_avg_wage=2000 # Market avg is 2000
        )

        # Run
        result = engine.manage_workforce(input_dto)

        # Assertions
        assert isinstance(result, HRDecisionOutputDTO)

        # 101 should be updated. 1000 < 2000.
        # Target wage calculation involves premium.
        # Base = 2000. Premium based on profit.
        # Let's assume at least base wage is target.
        # So new wage >= 2000.

        assert 101 in result.wage_updates, "Underpaid employee 101 should receive a wage update"
        assert result.wage_updates[101] >= 2000, f"New wage {result.wage_updates[101]} should be >= market avg 2000"

        # 102 (5000) should NOT be updated (sticky wages downward).
        assert 102 not in result.wage_updates, "Well-paid employee 102 should not receive a wage update"
