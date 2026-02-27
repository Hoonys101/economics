import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.death_system import DeathSystem
from simulation.systems.lifecycle.api import DeathConfigDTO, IDeathContext
from simulation.interfaces.market_interface import IMarket
from typing import Protocol, runtime_checkable, Any, Dict, List
from simulation.models import Transaction

# Lightweight Protocols
@runtime_checkable
class IFirm(Protocol):
    id: int
    is_active: bool
    hr_state: Any
    capital_stock: float
    def get_all_items(self) -> Dict[str, float]: ...
    def liquidate_assets(self, tick: int) -> Dict[str, float]: ...
    def get_all_claims(self, context: Any) -> List[Any]: ...
    def get_equity_stakes(self, context: Any) -> List[Any]: ...

@runtime_checkable
class IHousehold(Protocol):
    id: int
    is_active: bool
    def clear_inventory(self): ...

class TestDeathSystem:
    @pytest.fixture
    def death_system(self):
        config = MagicMock(spec=DeathConfigDTO)
        config.default_fallback_price_pennies = 1000

        inheritance_manager = MagicMock()
        liquidation_manager = MagicMock()
        settlement_system = MagicMock()
        public_manager = MagicMock()
        logger = MagicMock()

        return DeathSystem(config, inheritance_manager, liquidation_manager, settlement_system, public_manager, logger)

    def test_firm_liquidation(self, death_system):
        firm = MagicMock(spec=IFirm)
        firm.is_active = False
        firm.id = 1
        firm.get_all_items.return_value = {}

        firm.hr_state = MagicMock()
        firm.hr_state.employees = []

        firm.capital_stock = 100
        # Ensure ILiquidatable methods are present (Firm has them)

        context = MagicMock(spec=IDeathContext)
        context.firms = [firm]
        context.households = []
        context.agents = {1: firm}
        context.time = 1
        context.markets = {} # Ensure markets exists
        context.inactive_agents = {}
        context.primary_government = None # Prevent inheritance logic if any
        context.currency_registry_handler = None
        context.currency_holders = None
        context.settlement_system = None

        death_system.execute(context)

        death_system.liquidation_manager.initiate_liquidation.assert_called_once_with(firm, context)

        # Verify removal from global list
        assert firm not in context.firms

    def test_firm_liquidation_cancels_orders(self, death_system):
        firm = MagicMock(spec=IFirm)
        firm.is_active = False
        firm.id = 1
        firm.get_all_items.return_value = {}
        firm.hr_state = MagicMock()
        firm.hr_state.employees = []
        firm.liquidate_assets.return_value = {}

        # Setup Market
        # Use spec=IMarket so isinstance(mock_market, IMarket) returns True
        mock_market = MagicMock(spec=IMarket)
        # Ensure methods exist on the mock
        mock_market.cancel_orders = MagicMock()
        mock_market.id = "test_market"
        mock_market.buy_orders = {}
        mock_market.sell_orders = {}
        mock_market.matched_transactions = []

        context = MagicMock(spec=IDeathContext)
        context.firms = [firm]
        context.households = []
        context.agents = {1: firm}
        context.time = 1
        context.markets = {"test_market": mock_market}
        context.inactive_agents = {}
        context.primary_government = None
        context.currency_registry_handler = None
        context.currency_holders = None

        death_system.execute(context)

        mock_market.cancel_orders.assert_called_with(firm.id)

    def test_death_system_emits_settlement_transactions(self, death_system):
        # Setup deceased household
        household = MagicMock(spec=IHousehold)
        household.is_active = False
        household.id = 2
        household.inventory = {} # No inventory to trigger asset buyout for now

        # Setup Inheritance Manager to return dummy transactions
        dummy_tx = Transaction(
            buyer_id=2, seller_id=1, item_id="tax", quantity=1, price=100,
            market_id="system", transaction_type="tax", time=1, total_pennies=10000
        )
        death_system.inheritance_manager.process_death.return_value = [dummy_tx]

        context = MagicMock(spec=IDeathContext)
        context.firms = []
        context.households = [household]
        context.agents = {2: household}
        context.time = 1
        context.markets = {}
        context.inactive_agents = {}
        context.primary_government = MagicMock() # Needs gov for inheritance
        context.currency_registry_handler = None
        context.currency_holders = None
        context.settlement_system = MagicMock()

        transactions = death_system.execute(context)

        # Assertions
        assert len(transactions) == 1
        assert transactions[0] == dummy_tx
        death_system.inheritance_manager.process_death.assert_called_once()
        assert household not in context.households
