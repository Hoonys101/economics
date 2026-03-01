import pytest
from unittest.mock import MagicMock, Mock
from typing import List, Any, Dict
from simulation.systems.central_bank_system import CentralBankSystem
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.systems.handlers.monetary_handler import MonetaryTransactionHandler
from simulation.systems.settlement_system import SettlementSystem
from simulation.models import Order, Transaction
from modules.finance.api import OMOInstructionDTO, IFinancialEntity, IFinancialAgent, InsufficientFundsError
from modules.system.constants import ID_CENTRAL_BANK
from modules.system.api import IAgentRegistry, DEFAULT_CURRENCY
from modules.government.components.monetary_ledger import MonetaryLedger

class OMOTestAgent: # Implements IFinancialEntity and IFinancialAgent
    def __init__(self, agent_id, assets=0):
        self.id = agent_id
        self._assets = int(assets)
        # Legacy attributes required by TransactionManager checks
        self.total_money_issued = 0
        self.total_money_destroyed = 0
        self._econ_state = MagicMock()
        self._econ_state.assets = self._assets
        # Attach Monetary Ledger to simulate Government
        if agent_id == 2: # Mock Government
             self.monetary_ledger = MonetaryLedger()

    @property
    def balance_pennies(self) -> int:
        return self._assets

    def deposit(self, amount: int, currency=DEFAULT_CURRENCY):
        self._deposit(amount, currency)

    def withdraw(self, amount: int, currency=DEFAULT_CURRENCY):
        self._withdraw(amount, currency)

    def _deposit(self, amount: int, currency=DEFAULT_CURRENCY):
        if amount < 0: raise ValueError("Negative deposit")
        self._assets += amount
        self._econ_state.assets = self._assets

    def _withdraw(self, amount: int, currency=DEFAULT_CURRENCY):
        if amount < 0: raise ValueError("Negative withdraw")
        # Allow Central Bank to go negative (Minting)
        if self.id != ID_CENTRAL_BANK and self._assets < amount:
            raise InsufficientFundsError(f"Insufficient Funds: {self._assets} < {amount}")
        self._assets -= amount
        self._econ_state.assets = self._assets

    def get_balance(self, currency=DEFAULT_CURRENCY) -> int:
        return self._assets

    def get_all_balances(self) -> Dict[str, int]:
        return {DEFAULT_CURRENCY: self._assets}

    @property
    def total_wealth(self) -> int:
        return self._assets

    def get_liquid_assets(self, currency="USD") -> float:
        return float(self._assets)

    def get_total_debt(self) -> float:
        return 0.0

    # ICentralBank methods
    def execute_open_market_operation(self, instruction): return []
    def process_omo_settlement(self, transaction): pass

class MockRegistry:
    def __init__(self, agents: List[Any]):
        self.agents = {agent.id: agent for agent in agents}

    def get_agent(self, agent_id: Any) -> Any:
        return self.agents.get(agent_id)

    def get_all_financial_agents(self) -> List[Any]:
        return list(self.agents.values())

    def set_state(self, state: Any) -> None:
        pass

@pytest.fixture
def omo_setup():
    # SettlementSystem checks for "CENTRAL_BANK" ID or "CentralBank" class name to allow overdraft (Minting)
    # Ensure distinct IDs to avoid Registry collision (ID_CENTRAL_BANK might be 0)
    cb_agent = OMOTestAgent(agent_id=ID_CENTRAL_BANK, assets=0)
    gov_agent = OMOTestAgent(agent_id=2, assets=1000) # Changed from 0 to 2
    household = OMOTestAgent(agent_id=1, assets=500)

    # Setup Registry
    registry = MockRegistry([cb_agent, gov_agent, household])

    logger = MagicMock()
    settlement = SettlementSystem(logger=logger)
    settlement.agent_registry = registry # Inject Registry

    cb_system = CentralBankSystem(
        central_bank_agent=cb_agent,
        settlement_system=settlement,
        security_market_id="security_market",
        logger=logger
    )

    # Mock Simulation State
    state = MagicMock()
    state.agents = {
        cb_agent.id: cb_agent, # Use dynamic ID
        gov_agent.id: gov_agent,
        household.id: household
    }
    state.primary_government = gov_agent
    state.government = gov_agent # Compatibility
    state.transactions = []
    state.time = 1
    state.settlement_system = settlement
    state.central_bank = cb_agent
    state.logger = logger
    state.bank = None
    state.inactive_agents = {}
    state.taxation_system = None
    state.stock_market = None
    state.real_estate_units = []
    state.market_data = {}
    state.shareholder_registry = None

    tp = TransactionProcessor(config_module=MagicMock())
    tp.register_handler("omo_purchase", MonetaryTransactionHandler())
    tp.register_handler("omo_sale", MonetaryTransactionHandler())

    return cb_system, tp, state, cb_agent, gov_agent, household, settlement

def test_execute_omo_purchase_order_creation(omo_setup):
    cb_system, _, _, _, _, _, _ = omo_setup

    # Use DTO and sufficient amount for at least 1 bond (Price ~10000)
    instruction = OMOInstructionDTO(
        operation_type="purchase",
        target_amount=1_000_000 # 1M pennies
    )

    orders = cb_system.execute_open_market_operation(instruction)

    assert len(orders) == 1
    assert orders[0].agent_id == cb_system.id
    assert orders[0].order_type == "buy"
    # Quantity = 1,000,000 // 10000 = 100
    assert orders[0].quantity == 100
    assert orders[0].price > 0 # High price for purchase
    assert orders[0].market_id == "security_market"

def test_execute_omo_sale_order_creation(omo_setup):
    cb_system, _, _, _, _, _, _ = omo_setup

    # Use DTO and sufficient amount
    instruction = OMOInstructionDTO(
        operation_type="sale",
        target_amount=500_000 # 500k pennies
    )

    orders = cb_system.execute_open_market_operation(instruction)

    assert len(orders) == 1
    assert orders[0].agent_id == cb_system.id
    assert orders[0].order_type == "sell"
    # Quantity = 500,000 // 10000 = 50
    assert orders[0].quantity == 50
    assert orders[0].price > 0 # Limit price is no longer 0
    assert orders[0].market_id == "security_market"

def test_process_omo_purchase_transaction(omo_setup):
    cb_system, tp, state, cb_agent, gov_agent, household, settlement = omo_setup

    # Household sells bond to CB (OMO Purchase by CB)
    # CB pays Household (Minting new money)
    trade_price = 100
    tx = Transaction(
        buyer_id=cb_agent.id,
        seller_id=household.id,
        item_id="government_bond",
        quantity=10,
        price=10, # Unit price 10. Total = 100
        market_id="security_market",
        transaction_type="omo_purchase",
        time=1
        , total_pennies=100)
    state.transactions = [tx]

    # Use SSoT for initial state
    initial_hh_assets = settlement.get_balance(household.id)

    # Manually reset government ledger flow counters for clean slate
    gov_agent.monetary_ledger.reset_tick_flow()

    tp.execute(state)

    # Post-Processing: Manually invoke ledger processing as per Phase3_Transaction logic
    gov_agent.monetary_ledger.process_transactions([tx])

    # Verify Household got paid via SSoT
    assert settlement.get_balance(household.id) == initial_hh_assets + trade_price

    # Verify Gov Ledger Updated via MonetaryLedger (SSoT for M2 Tracking)
    delta = gov_agent.monetary_ledger.get_monetary_delta()
    # 100 pennies created. get_monetary_delta returns Pennies (100)
    assert delta == 100

def test_process_omo_sale_transaction(omo_setup):
    cb_system, tp, state, cb_agent, gov_agent, household, settlement = omo_setup

    # Household buys bond from CB (OMO Sale by CB)
    # Household pays CB (Burning money)
    trade_price = 100
    tx = Transaction(
        buyer_id=household.id,
        seller_id=cb_agent.id,
        item_id="government_bond",
        quantity=5,
        price=20, # Unit price 20. Total = 100
        market_id="security_market",
        transaction_type="omo_sale",
        time=1
        , total_pennies=100)
    state.transactions = [tx]

    initial_hh_assets = settlement.get_balance(household.id)

    # Manually reset government ledger flow counters for clean slate
    gov_agent.monetary_ledger.reset_tick_flow()

    tp.execute(state)

    # Post-Processing
    gov_agent.monetary_ledger.process_transactions([tx])

    # Verify Household paid via SSoT
    assert settlement.get_balance(household.id) == initial_hh_assets - trade_price

    # Verify Gov Ledger Updated (Burning)
    delta = gov_agent.monetary_ledger.get_monetary_delta()
    # 100 pennies destroyed. get_monetary_delta returns Pennies (-100)
    assert delta == -100
