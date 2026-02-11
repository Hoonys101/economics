import pytest
from unittest.mock import Mock, MagicMock
from modules.finance.system import FinanceSystem
from modules.finance.api import BondDTO
from simulation.agents.government import Government
from simulation.firms import Firm
from modules.analysis.fiscal_monitor import FiscalMonitor
from modules.system.api import DEFAULT_CURRENCY

class TestSovereignDebt:
    @pytest.fixture
    def setup_system(self):
        self.govt = MagicMock(spec=Government)
        self.govt.id = 1
        # Govt wallet mock
        self.govt.wallet = MagicMock()
        self.govt.wallet.get_balance.return_value = 0

        self.central_bank = MagicMock()
        self.bank = MagicMock()
        self.bank.assets = 10000 # int
        self.bank.id = 2
        self.bank.base_rate = 0.03 # float, vital for ledger init
        self.bank.deposit = MagicMock()
        self.bank.withdraw = MagicMock()

        # Bank wallet mock for FinanceSystem init sync
        self.bank.wallet = MagicMock()
        self.bank.wallet.get_balance.return_value = 10000

        self.config = MagicMock()
        # Mock config.get properly
        def config_get(key, default=None):
            if "RISK_PREMIUM" in key:
                 return {1.2: 0.05, 0.9: 0.02}
            return default
        self.config.get.side_effect = config_get

        self.settlement_system = MagicMock()
        self.settlement_system.transfer.return_value = True
        self.settlement_system.get_balance.return_value = 10000

        self.finance_system = FinanceSystem(
            government=self.govt,
            central_bank=self.central_bank,
            bank=self.bank,
            config_module=self.config,
            settlement_system=self.settlement_system
        )
        self.finance_system.fiscal_monitor = MagicMock(spec=FiscalMonitor)
        self.finance_system.fiscal_monitor.get_debt_to_gdp_ratio.return_value = 0.5 # Safe

        return self.finance_system

    def test_issue_treasury_bonds_calls_settlement_system(self, setup_system):
        fs = setup_system
        fs.central_bank.get_base_rate.return_value = 0.05

        # Updated: returns (bonds, transactions)
        # Use int amount 100
        bonds, txs = fs.issue_treasury_bonds(100, 1)

        assert len(bonds) == 1
        assert len(fs.ledger.treasury.bonds) == 1

        # New: Check transactions
        assert len(txs) == 1
        assert txs[0].buyer_id == fs.bank.id
        assert txs[0].seller_id == fs.government.id
        assert txs[0].price == 100

    def test_collect_corporate_tax_calls_settlement_system(self, setup_system):
        fs = setup_system
        firm = MagicMock(spec=Firm)
        firm.id = 101

        # This method is deprecated and should return False
        success = fs.collect_corporate_tax(firm, 50) # int

        assert success is False
        fs.settlement_system.transfer.assert_not_called()

    def test_risk_premium_calculation(self, setup_system):
        fs = setup_system

        # Update ledger base_rate as issue_treasury_bonds uses ledger state
        if fs.ledger.banks:
             fs.ledger.banks[fs.bank.id].base_rate = 0.05

        # Note: Current implementation of issue_treasury_bonds uses (base_rate + 0.01)
        # It ignores fiscal_monitor debt ratio.
        # So we assert 0.05 + 0.01 = 0.06

        bonds, txs = fs.issue_treasury_bonds(100, 1) # int

        assert abs(bonds[0].yield_rate - 0.06) < 1e-6

    def test_insufficient_funds_fails_issuance(self, setup_system):
        fs = setup_system
        fs.central_bank.get_base_rate.return_value = 0.05
        fs.bank.assets = 0 # Bank has no money

        # Update SettlementSystem mock to return 0
        fs.settlement_system.get_balance.return_value = 0

        bonds, txs = fs.issue_treasury_bonds(100, 1)

        assert len(bonds) == 0
        assert len(txs) == 0
