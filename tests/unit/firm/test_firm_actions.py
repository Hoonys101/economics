import pytest
from unittest.mock import Mock, MagicMock
from modules.firm.orchestrators.firm_action_executor import FirmActionExecutor
from simulation.firms import Firm
from simulation.models import Order
from modules.system.api import DEFAULT_CURRENCY
from modules.firm.api import AssetManagementResultDTO, RDResultDTO

class TestFirmActionExecutor:

    @pytest.fixture
    def executor(self):
        return FirmActionExecutor()

    @pytest.fixture
    def firm(self):
        firm = MagicMock()
        firm.id = 1
        firm.wallet = MagicMock()
        firm.settlement_system = MagicMock()
        firm.production_state = MagicMock()
        firm.asset_management_engine = MagicMock()
        firm.rd_engine = MagicMock()
        firm.finance_engine = MagicMock()
        firm.hr_engine = MagicMock()
        firm.hr_state = MagicMock()
        firm.finance_state = MagicMock()
        firm.get_snapshot_dto.return_value = Mock()
        firm.wallet.get_balance.return_value = 1000
        return firm

    def test_invest_automation_success(self, executor, firm):
        order = Order(agent_id=1, side='INVEST_AUTOMATION', item_id='automation', quantity=0, price_pennies=int(0 * 100), price_limit=0, monetary_amount={'amount_pennies': 100, 'currency': DEFAULT_CURRENCY}, market_id='internal')
        firm.asset_management_engine.invest.return_value = AssetManagementResultDTO(success=True, automation_level_increase=0.1, capital_stock_increase=0.0, actual_cost=100)
        firm.settlement_system.transfer.return_value = True
        executor.execute(firm, [order], None, 0)
        firm.asset_management_engine.invest.assert_called_once()
        firm.settlement_system.transfer.assert_called_once()

    def test_invest_rd_success(self, executor, firm):
        order = Order(agent_id=1, side='INVEST_RD', item_id='rd_project', quantity=0, price_pennies=int(0 * 100), price_limit=0, monetary_amount={'amount_pennies': 100, 'currency': DEFAULT_CURRENCY}, market_id='internal')
        firm.rd_engine.research.return_value = RDResultDTO(success=True, quality_improvement=0.1, productivity_multiplier_change=1.1)
        firm.settlement_system.transfer.return_value = True
        executor.execute(firm, [order], None, 0)
        firm.rd_engine.research.assert_called_once()
        firm.settlement_system.transfer.assert_called_once()

    def test_fire_employee(self, executor, firm):
        order = Order(agent_id=1, side='FIRE', item_id='labor', quantity=0, price_pennies=int(50 * 100), price_limit=50, target_agent_id=2, market_id='internal')
        mock_tx = Mock()
        mock_tx.price = 50
        mock_tx.currency = DEFAULT_CURRENCY
        firm.hr_engine.create_fire_transaction.return_value = mock_tx
        firm.settlement_system.transfer.return_value = True
        emp = Mock()
        emp.id = 2
        firm.hr_state.employees = [emp]
        executor.execute(firm, [order], None, 0)
        firm.hr_engine.create_fire_transaction.assert_called_once()
        firm.hr_engine.finalize_firing.assert_called_with(firm.hr_state, 2)