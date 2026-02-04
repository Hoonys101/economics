import pytest
from unittest.mock import MagicMock
from simulation.components.finance_department import FinanceDepartment
from simulation.firms import Firm
from modules.system.api import DEFAULT_CURRENCY

class TestFinanceDepartmentBankruptcy:
    @pytest.fixture
    def config(self):
        mock_config = MagicMock()
        mock_config.bankruptcy_consecutive_loss_threshold = 5
        mock_config.brand_resilience_factor = 0.5 # 1 point of awareness = 0.5 tick resilience?
        # Wait, implementation was: resilience_ticks = int(awareness * factor)
        # So factor should be e.g. 0.5 means 2 awareness -> 1 tick.
        # Let's use 0.1. 10 awareness -> 1 tick.
        mock_config.brand_resilience_factor = 0.1
        mock_config.profit_history_ticks = 10
        return mock_config

    @pytest.fixture
    def firm_setup(self, config):
        firm = MagicMock(spec=Firm)
        firm.brand_manager = MagicMock()
        firm.brand_manager.awareness = 0.0
        firm.is_bankrupt = False
        finance = FinanceDepartment(firm, config)
        return firm, finance

    def test_bankruptcy_threshold_no_resilience(self, firm_setup):
        firm, finance = firm_setup
        firm.brand_manager.awareness = 0.0 # Resilience = 0

        # Threshold is 5.
        # Simulate 4 losses
        for _ in range(4):
            finance.current_profit[DEFAULT_CURRENCY] = -100.0
            finance.check_bankruptcy()
            assert not firm.is_bankrupt

        # 5th loss
        finance.current_profit[DEFAULT_CURRENCY] = -100.0
        finance.check_bankruptcy()
        assert firm.is_bankrupt

    def test_bankruptcy_resilience(self, firm_setup):
        firm, finance = firm_setup
        # Resilience factor 0.1.
        # Give awareness 20. Resilience = int(20 * 0.1) = 2 ticks.
        firm.brand_manager.awareness = 20.0

        # Threshold is 5. Effective threshold = 5 + 2 = 7?
        # Logic: effective_loss_ticks = consecutive - resilience.
        # effective >= threshold.
        # consecutive - resilience >= 5
        # consecutive >= 5 + resilience = 7.

        # So firm should survive 6 losses.
        for _ in range(6):
            finance.current_profit[DEFAULT_CURRENCY] = -100.0
            finance.check_bankruptcy()
            assert not firm.is_bankrupt

        # 7th loss
        finance.current_profit[DEFAULT_CURRENCY] = -100.0
        finance.check_bankruptcy()
        assert firm.is_bankrupt

    def test_bankruptcy_reset_on_profit(self, firm_setup):
        firm, finance = firm_setup

        # 3 losses
        for _ in range(3):
            finance.current_profit[DEFAULT_CURRENCY] = -100.0
            finance.check_bankruptcy()

        # 1 profit
        finance.current_profit[DEFAULT_CURRENCY] = 100.0
        finance.check_bankruptcy()
        assert finance.consecutive_loss_turns == 0

        # 3 losses again
        for _ in range(3):
            finance.current_profit[DEFAULT_CURRENCY] = -100.0
            finance.check_bankruptcy()
            assert not firm.is_bankrupt
