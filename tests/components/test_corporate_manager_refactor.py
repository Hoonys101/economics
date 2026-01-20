import pytest
from unittest.mock import Mock, patch
from simulation.components.finance_department import FinanceDepartment
from simulation.decisions.corporate_manager import CorporateManager
from simulation.firms import Firm

class TestCorporateManagerRefactor:
    @pytest.fixture
    def mock_firm(self):
        firm = Mock(spec=Firm)
        firm.id = 1
        firm.assets = 10000.0
        firm.automation_level = 0.5
        firm.base_quality = 1.0
        firm.productivity_factor = 1.0
        firm.finance = Mock(spec=FinanceDepartment)
        firm.finance.firm = firm
        firm.capital_stock = 1000.0
        return firm

    @pytest.fixture
    def corp_manager(self):
        config = Mock()
        config.AUTOMATION_COST_PER_PCT = 1000.0
        config.FIRM_SAFETY_MARGIN = 1000.0
        config.AUTOMATION_TAX_RATE = 0.05
        # Ensure getattr returns primitive for these
        config.CAPITAL_TO_OUTPUT_RATIO = 2.0
        return CorporateManager(config)

    def test_manage_automation_delegates_to_finance(self, corp_manager, mock_firm):
        """Test that _manage_automation calls firm.finance.invest_in_automation."""
        guidance = {"target_automation": 0.6}
        mock_firm.assets = 10000.0

        corp_manager._manage_automation(mock_firm, aggressiveness=1.0, guidance=guidance, current_time=1, government=Mock())

        mock_firm.finance.invest_in_automation.assert_called_once()
        args, _ = mock_firm.finance.invest_in_automation.call_args
        assert args[0] > 0

    def test_manage_rd_delegates_to_finance(self, corp_manager, mock_firm):
        """Test that _manage_r_and_d calls firm.finance.invest_in_rd."""
        mock_firm.revenue_this_turn = 5000.0
        mock_firm.assets = 10000.0
        mock_firm.research_history = {"total_spent": 0.0, "success_count": 0}
        mock_firm.employees = []

        corp_manager._manage_r_and_d(mock_firm, aggressiveness=0.8, current_time=1)

        mock_firm.finance.invest_in_rd.assert_called_once()
        args, _ = mock_firm.finance.invest_in_rd.call_args
        assert args[0] > 0

    def test_manage_capex_delegates_to_finance(self, corp_manager, mock_firm):
        """Test that _manage_capex calls firm.finance.invest_in_capex."""
        mock_firm.assets = 10000.0

        corp_manager._manage_capex(mock_firm, aggressiveness=0.8, reflux_system=Mock(), current_time=1)

        mock_firm.finance.invest_in_capex.assert_called_once()
        args, _ = mock_firm.finance.invest_in_capex.call_args
        assert args[0] > 0
