import pytest
from unittest.mock import Mock, MagicMock
from modules.finance.system import FinanceSystem
from modules.finance.api import BondDTO
from simulation.agents.government import Government
from simulation.firms import Firm
from modules.analysis.fiscal_monitor import FiscalMonitor


class TestSovereignDebt:
    @pytest.fixture
    def setup_system(self):
        self.govt = MagicMock(spec=Government)
        self.govt.id = 1
        self.central_bank = MagicMock()
        self.bank = MagicMock()
        self.bank.assets = 10000.0
        self.bank.id = 2
        self.bank.deposit = MagicMock()
        self.bank.withdraw = MagicMock()

        self.config = MagicMock()

        # Mock config.get properly
        def config_get(key, default=None):
            if "RISK_PREMIUM" in key:
                return {1.2: 0.05, 0.9: 0.02}
            return default

        self.config.get.side_effect = config_get

        self.settlement_system = MagicMock()
        self.settlement_system.transfer.return_value = True

        self.finance_system = FinanceSystem(
            government=self.govt,
            central_bank=self.central_bank,
            bank=self.bank,
            config_module=self.config,
            settlement_system=self.settlement_system,
        )
        self.finance_system.fiscal_monitor = MagicMock(spec=FiscalMonitor)
        self.finance_system.fiscal_monitor.get_debt_to_gdp_ratio.return_value = (
            0.5  # Safe
        )

        return self.finance_system

    def test_issue_treasury_bonds_calls_settlement_system(self, setup_system):
        fs = setup_system
        fs.central_bank.get_base_rate.return_value = 0.05

        bonds = fs.issue_treasury_bonds(100.0, 1)

        assert len(bonds) == 1
        assert len(fs.outstanding_bonds) == 1

        # Verify Settlement Call
        # Should transfer from Bank to Govt
        fs.settlement_system.transfer.assert_called_once()
        args = fs.settlement_system.transfer.call_args
        assert args[0][0] == fs.bank  # Debtor
        assert args[0][1] == fs.government  # Creditor
        assert args[0][2] == 100.0  # Amount

    def test_collect_corporate_tax_calls_settlement_system(self, setup_system):
        fs = setup_system
        firm = MagicMock(spec=Firm)
        firm.id = 101

        success = fs.collect_corporate_tax(firm, 50.0)

        assert success is True
        fs.settlement_system.transfer.assert_called_once()
        args = fs.settlement_system.transfer.call_args
        assert args[0][0] == firm  # Debtor
        assert args[0][1] == fs.government  # Creditor
        assert args[0][2] == 50.0

    def test_risk_premium_calculation(self, setup_system):
        fs = setup_system
        fs.central_bank.get_base_rate.return_value = 0.05
        # High debt ratio -> high risk
        fs.fiscal_monitor.get_debt_to_gdp_ratio.return_value = 1.3

        bonds = fs.issue_treasury_bonds(100.0, 1)
        # Base 0.05 + Risk 0.05 = 0.10
        # Note: 0.05 + 0.05 = 0.1
        assert abs(bonds[0].yield_rate - 0.10) < 1e-6

    def test_insufficient_funds_fails_issuance(self, setup_system):
        fs = setup_system
        fs.central_bank.get_base_rate.return_value = 0.05
        fs.bank.assets = 0.0  # Bank has no money

        bonds = fs.issue_treasury_bonds(100.0, 1)

        assert len(bonds) == 0
        fs.settlement_system.transfer.assert_not_called()
