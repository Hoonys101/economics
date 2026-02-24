import pytest
from unittest.mock import MagicMock, patch
from dataclasses import replace

from simulation.firms import Firm
from modules.firm.api import (
    FinanceDecisionInputDTO, BudgetPlanDTO,
    HRDecisionInputDTO, HRDecisionOutputDTO,
    FirmSnapshotDTO, HRIntentDTO, SalesIntentDTO, ProductionIntentDTO,
    FirmBrainScanContextDTO, FirmBrainScanResultDTO,
    FirmConfigDTO,
    IFinanceEngine, IHREngine, IProductionEngine, ISalesEngine, IPricingEngine,
    IAssetManagementEngine, IRDEngine, IBrandEngine
)
from modules.simulation.dtos.api import FirmConfigDTO as OriginalFirmConfigDTO
from simulation.models import Order
from simulation.dtos import DecisionInputDTO
from modules.system.api import MarketSnapshotDTO
from modules.simulation.api import AgentID

class TestFirmBrainScan:

    @pytest.fixture
    def mock_firm(self):
        # Create a Firm with mocked engines
        mock_core_config = MagicMock()
        mock_core_config.id = 1
        mock_core_config.name = "TestFirm"
        mock_core_config.initial_needs = {}

        mock_decision_engine = MagicMock()
        # Use simple MagicMock for config to avoid spec issues with dataclasses
        mock_config_dto = MagicMock()
        # Populate required fields
        mock_config_dto.firm_min_production_target = 10.0
        mock_config_dto.ipo_initial_shares = 1000
        mock_config_dto.dividend_rate = 0.1
        mock_config_dto.profit_history_ticks = 10
        mock_config_dto.default_unit_cost = 10
        mock_config_dto.goods = {"food": {}}
        # Add fields used in brain_scan logic
        mock_config_dto.labor_alpha = 0.5
        mock_config_dto.automation_labor_reduction = 0.1
        mock_config_dto.labor_elasticity_min = 0.1
        mock_config_dto.capital_depreciation_rate = 0.05

        firm = Firm(
            core_config=mock_core_config,
            engine=mock_decision_engine,
            specialization="food",
            productivity_factor=1.0,
            config_dto=mock_config_dto
        )

        # Inject Mock Engines
        firm.finance_engine = MagicMock(spec=IFinanceEngine)
        firm.hr_engine = MagicMock(spec=IHREngine)
        firm.production_engine = MagicMock(spec=IProductionEngine)
        firm.sales_engine = MagicMock(spec=ISalesEngine)
        firm.pricing_engine = MagicMock(spec=IPricingEngine)
        firm.asset_management_engine = MagicMock(spec=IAssetManagementEngine)
        firm.rd_engine = MagicMock(spec=IRDEngine)
        firm.brand_engine = MagicMock(spec=IBrandEngine)

        firm.action_executor = MagicMock() # Mock execute_internal_orders delegate
        firm.execute_internal_orders = MagicMock() # Mock directly too

        return firm

    def test_brain_scan_calls_engines_purely(self, mock_firm):
        # Setup Inputs
        current_tick = 100
        context = FirmBrainScanContextDTO(
            agent_id=AgentID(mock_firm.id),
            current_tick=current_tick
        )

        # Setup Engine Returns
        # BudgetPlanDTO is frozen dataclass, use MagicMock without spec or explicit mock
        mock_budget = MagicMock()
        mock_budget.labor_budget_pennies = 10000
        mock_firm.finance_engine.plan_budget.return_value = mock_budget

        mock_hr_result = HRIntentDTO(
            hiring_target=1,
            wage_updates={},
            fire_employee_ids=[]
        )
        mock_firm.hr_engine.decide_workforce.return_value = mock_hr_result

        mock_prod_result = ProductionIntentDTO(
            target_production_quantity=10.0,
            materials_to_use={},
            estimated_cost_pennies=100
        )
        mock_firm.production_engine.decide_production.return_value = mock_prod_result

        mock_sales_result = SalesIntentDTO(
            price_adjustments={"food": 1100},
            sales_orders=[],
            marketing_spend_pennies=0
        )
        mock_firm.sales_engine.decide_pricing.return_value = mock_sales_result

        # Act
        result = mock_firm.brain_scan(context)

        # Assert
        assert isinstance(result, FirmBrainScanResultDTO)
        assert result.agent_id == mock_firm.id
        assert result.tick == current_tick
        assert result.intent_type == "FULL_SCAN"

        payload = result.intent_payload
        assert payload["budget_plan"] == mock_budget
        assert payload["hr_intent"] == mock_hr_result
        assert payload["production_intent"] == mock_prod_result
        assert payload["sales_intent"] == mock_sales_result

        # Verify Engines Called
        mock_firm.finance_engine.plan_budget.assert_called_once()
        mock_firm.hr_engine.decide_workforce.assert_called_once()
        mock_firm.production_engine.decide_production.assert_called_once()
        mock_firm.sales_engine.decide_pricing.assert_called_once()

        # Verify NO Side Effects
        mock_firm.execute_internal_orders.assert_not_called()
        mock_firm.action_executor.execute.assert_not_called()

    def test_brain_scan_respects_market_snapshot_override(self, mock_firm):
        # Setup Override
        override_snapshot = MagicMock() # spec=MarketSnapshotDTO causes issues if fields are missing
        override_snapshot.labor = MagicMock()
        override_snapshot.labor.avg_wage = 50.0 # High wage

        context = FirmBrainScanContextDTO(
            agent_id=AgentID(mock_firm.id),
            current_tick=100,
            market_snapshot_override=override_snapshot
        )

        # Setup Engine Returns (Dummy)
        mock_firm.finance_engine.plan_budget.return_value = MagicMock()
        mock_firm.hr_engine.decide_workforce.return_value = MagicMock(spec=HRIntentDTO)
        mock_firm.production_engine.decide_production.return_value = MagicMock(spec=ProductionIntentDTO)
        mock_firm.sales_engine.decide_pricing.return_value = MagicMock(spec=SalesIntentDTO)

        # Act
        mock_firm.brain_scan(context)

        # Assert
        # Check that plan_budget received the override snapshot
        call_args = mock_firm.finance_engine.plan_budget.call_args[0][0]
        assert isinstance(call_args, FinanceDecisionInputDTO)
        assert call_args.market_snapshot == override_snapshot

        # Check HR wage extraction
        # 50.0 * 100 = 5000 pennies
        hr_call_args = mock_firm.hr_engine.decide_workforce.call_args[0][0]
        assert hr_call_args.labor_market_avg_wage == 5000
        assert hr_call_args.market_snapshot == override_snapshot

    def test_brain_scan_respects_config_override(self, mock_firm):
        # Setup Override
        override_config = MagicMock()
        override_config.firm_min_employees = 999
        override_config.goods = {}
        override_config.labor_alpha = 0.5
        override_config.automation_labor_reduction = 0.1
        override_config.labor_elasticity_min = 0.1
        override_config.capital_depreciation_rate = 0.05
        # Add attributes needed by brain_scan logic when accessing config_override
        # brain_scan accesses these from context.config_override directly

        context = FirmBrainScanContextDTO(
            agent_id=AgentID(mock_firm.id),
            current_tick=100,
            config_override=override_config
        )

        # Setup Engine Returns (Dummy)
        mock_firm.finance_engine.plan_budget.return_value = MagicMock()
        mock_firm.hr_engine.decide_workforce.return_value = MagicMock(spec=HRIntentDTO)
        mock_firm.production_engine.decide_production.return_value = MagicMock(spec=ProductionIntentDTO)
        mock_firm.sales_engine.decide_pricing.return_value = MagicMock(spec=SalesIntentDTO)

        # Act
        mock_firm.brain_scan(context)

        # Assert
        # Check Finance received override config
        fin_args = mock_firm.finance_engine.plan_budget.call_args[0][0]
        assert fin_args.config == override_config

        # Check HR Context received override values
        hr_args = mock_firm.hr_engine.decide_workforce.call_args[0][0]
        assert hr_args.min_employees == 999
