import pytest
from unittest.mock import MagicMock, ANY, call
from modules.governance.judicial.system import JudicialSystem
from modules.system.event_bus.event_bus import EventBus
from modules.events.dtos import LoanDefaultedEvent, DebtRestructuringRequiredEvent
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry
from modules.finance.api import IShareholderRegistry, IPortfolioHandler, ICreditFrozen, IFinancialEntity, ILiquidatable
from modules.simulation.api import IEducated

class MockAgent:
    def __init__(self, id, assets=500.0):
        self.id = id
        self.education_xp = 100.0
        self._credit_frozen_until_tick = 0
        self._assets = assets # Liquid assets
        self.portfolio_mock = MagicMock()
        mock_asset = MagicMock()
        mock_asset.asset_type = 'stock'
        mock_asset.asset_id = '99'
        mock_asset.quantity = 10
        self.portfolio_mock.assets = [mock_asset]
        self.inventory_value = 0.0

    @property
    def credit_frozen_until_tick(self) -> int:
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int):
        self._credit_frozen_until_tick = value

    def get_portfolio(self):
        return self.portfolio_mock

    def clear_portfolio(self):
        self.portfolio_mock.assets = []

    def receive_portfolio(self, portfolio):
        pass

    @property
    def assets(self) -> float:
        return self._assets

    def deposit(self, amount, currency="USD"):
        self._assets += amount

    def withdraw(self, amount, currency="USD"):
        self._assets -= amount

    def get_balance(self, currency="USD"):
        return self._assets

    def liquidate_assets(self, tick):
        # Simulate gaining cash from inventory liquidation
        gain = self.inventory_value
        self._assets += gain
        self.inventory_value = 0
        return {"USD": gain}

    def get_all_claims(self, ctx):
        return []

    def get_equity_stakes(self, ctx):
        return []

@pytest.fixture
def mock_dependencies():
    event_bus = EventBus()
    settlement_system = MagicMock(spec=ISettlementSystem)
    agent_registry = MagicMock(spec=IAgentRegistry)
    shareholder_registry = MagicMock(spec=IShareholderRegistry)
    config_manager = MagicMock()

    # Setup Config defaults
    def get_config(key, default=None):
        return default
    config_manager.get.side_effect = get_config

    return {
        "event_bus": event_bus,
        "settlement_system": settlement_system,
        "agent_registry": agent_registry,
        "shareholder_registry": shareholder_registry,
        "config_manager": config_manager
    }

def test_judicial_system_waterfall_full_recovery(mock_dependencies):
    deps = mock_dependencies

    # Setup Transfer Side Effect
    def transfer_side_effect(debit_agent, credit_agent, amount, memo, tick, currency="USD"):
        debit_agent.withdraw(amount)
        credit_agent.deposit(amount)
        return True
    deps["settlement_system"].transfer.side_effect = transfer_side_effect

    system = JudicialSystem(
        event_bus=deps["event_bus"],
        settlement_system=deps["settlement_system"],
        agent_registry=deps["agent_registry"],
        shareholder_registry=deps["shareholder_registry"],
        config_manager=deps["config_manager"]
    )

    agent_id = 1
    creditor_id = 2
    agent = MockAgent(agent_id, assets=1500.0) # Enough to cover 1000 debt
    creditor = MockAgent(creditor_id)

    deps["agent_registry"].get_agent.side_effect = lambda aid: agent if aid == agent_id else (creditor if aid == creditor_id else None)

    event: LoanDefaultedEvent = {
        "event_type": "LOAN_DEFAULTED",
        "tick": 10,
        "agent_id": agent_id,
        "loan_id": "loan_1",
        "defaulted_amount": 1000.0,
        "creditor_id": creditor_id
    }

    deps["event_bus"].publish(event)

    # Assertions
    # 1. Cash Seizure (Stage 1)
    deps["settlement_system"].transfer.assert_called_with(
        debit_agent=agent,
        credit_agent=creditor,
        amount=1000.0,
        memo=ANY,
        tick=10
    )
    # Since debt is fully paid, no stock/inventory seizure should happen (optimization check)
    assert not deps["shareholder_registry"].register_shares.called

def test_judicial_system_waterfall_partial_recovery_and_restructuring(mock_dependencies):
    deps = mock_dependencies

    # Setup Transfer Side Effect
    def transfer_side_effect(debit_agent, credit_agent, amount, memo, tick, currency="USD"):
        debit_agent.withdraw(amount)
        credit_agent.deposit(amount)
        return True
    deps["settlement_system"].transfer.side_effect = transfer_side_effect

    system = JudicialSystem(
        event_bus=deps["event_bus"],
        settlement_system=deps["settlement_system"],
        agent_registry=deps["agent_registry"],
        shareholder_registry=deps["shareholder_registry"],
        config_manager=deps["config_manager"]
    )

    # Mock EventBus publish to capture emitted events
    deps["event_bus"].publish = MagicMock()

    agent_id = 1
    creditor_id = 2
    agent = MockAgent(agent_id, assets=100.0) # Only 100 cash
    agent.inventory_value = 50.0 # 50 inventory
    creditor = MockAgent(creditor_id)

    deps["agent_registry"].get_agent.side_effect = lambda aid: agent if aid == agent_id else (creditor if aid == creditor_id else None)

    # Mock Shareholder Registry for Stage 2
    deps["shareholder_registry"].get_shareholders_of_firm.return_value = [{'agent_id': creditor_id, 'quantity': 5}]

    event: LoanDefaultedEvent = {
        "event_type": "LOAN_DEFAULTED",
        "tick": 10,
        "agent_id": agent_id,
        "loan_id": "loan_1",
        "defaulted_amount": 1000.0,
        "creditor_id": creditor_id
    }

    system.handle_financial_event(event)

    # 1. Cash Seizure (Stage 1) - 100.0. Agent assets become 0.
    # 2. Stock Seizure (Stage 2) - agent has 10 shares of 99.
    #    Should transfer to creditor.
    # 3. Inventory Seizure (Stage 3) - Liquidate 50.0. Agent assets become 50.
    #    Seize 50.0. Agent assets become 0.
    # Total Seized: 150.0 (Cash).
    # Remaining Debt: 850.0

    # Verify Cash Transfers
    # Call 1: 100.0
    # Call 2: 50.0 (from inventory)
    calls = deps["settlement_system"].transfer.call_args_list
    assert len(calls) == 2
    assert calls[0][1]['amount'] == 100.0
    assert calls[1][1]['amount'] == 50.0

    # Verify Stock Transfer
    # 1. Remove from agent
    deps["shareholder_registry"].register_shares.assert_any_call(99, agent_id, 0)
    # 2. Add to creditor (5 existing + 10 new = 15)
    deps["shareholder_registry"].register_shares.assert_any_call(99, creditor_id, 15.0)

    # Verify DebtRestructuringEvent
    # Check that publish was called with the event
    published_events = [args[0] for args, _ in deps["event_bus"].publish.call_args_list]
    restructuring_event = next((e for e in published_events if e['event_type'] == "DEBT_RESTRUCTURING_REQUIRED"), None)

    assert restructuring_event is not None
    assert restructuring_event['remaining_debt'] == 850.0
