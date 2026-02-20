
import pytest
from unittest.mock import MagicMock, Mock, create_autospec
from uuid import uuid4
from typing import Dict, Any, List

from simulation.dtos.commands import GodCommandDTO, GodResponseDTO
from modules.system.services.command_service import CommandService
from modules.system.api import IGlobalRegistry, IAgentRegistry, OriginType, DEFAULT_CURRENCY, RegistryEntry
from modules.system.constants import ID_CENTRAL_BANK
from simulation.finance.api import ISettlementSystem, IFinancialAgent
from modules.finance.api import IBank
from modules.simulation.api import IInventoryHandler

# --- Mocks ---

class MockAgent(IFinancialAgent, IInventoryHandler):
    def __init__(self, agent_id, balance=0, inventory=None, sector=None):
        self.id = agent_id
        self._balance = balance
        self._inventory = inventory or {}
        self.sector = sector

    def get_balance(self, currency=DEFAULT_CURRENCY):
        return self._balance

    def _deposit(self, amount, currency=DEFAULT_CURRENCY):
        self._balance += amount

    def _withdraw(self, amount, currency=DEFAULT_CURRENCY):
        if self._balance >= amount:
            self._balance -= amount
        else:
            raise ValueError("Insufficient funds")

    def get_all_balances(self):
        return {DEFAULT_CURRENCY: self._balance}

    def get_assets_by_currency(self):
        return self.get_all_balances()

    # Inventory
    def get_all_items(self, slot=None):
        return self._inventory

    def remove_item(self, item_id, quantity, transaction_id=None, slot=None):
        if self._inventory.get(item_id, 0) >= quantity:
            self._inventory[item_id] -= quantity
            return True
        return False

    def add_item(self, item_id, quantity, transaction_id=None, quality=1.0, slot=None):
        self._inventory[item_id] = self._inventory.get(item_id, 0) + quantity
        return True

    def get_quantity(self, item_id, slot=None):
        return self._inventory.get(item_id, 0)

    def get_quality(self, item_id, slot=None):
        return 1.0

    def clear_inventory(self, slot=None):
        self._inventory = {}


class MockBank(MockAgent, IBank): # Inherits basic agent props
    def __init__(self, agent_id, balance=0):
        super().__init__(agent_id, balance)
        self.customer_balances = {} # Deposits
        self.id = agent_id

    # IBank required methods dummy impl
    def grant_loan(self, borrower_id, amount, interest_rate, due_tick=None, borrower_profile=None): return None
    def stage_loan(self, borrower_id, amount, interest_rate, due_tick=None, borrower_profile=None): return None
    def repay_loan(self, loan_id, amount: int) -> int: return amount
    def get_debt_status(self, borrower_id): return None
    def terminate_loan(self, loan_id): return None
    def set_finance_system(self, fs): pass
    def update_base_rate(self, rate): pass
    def run_tick(self, agents_dict, tick): return []
    def get_total_deposits_pennies(self) -> int: return self.get_total_deposits()
    def close_account(self, agent_id: "AgentID") -> int: return self.customer_balances.pop(agent_id, 0)
    def receive_repayment(self, borrower_id: "AgentID", amount: int) -> int: return amount

    def get_customer_balance(self, agent_id):
        return self.customer_balances.get(agent_id, 0)

    def withdraw_for_customer(self, agent_id, amount):
        if self.customer_balances.get(agent_id, 0) >= amount:
            self.customer_balances[agent_id] -= amount
            return True
        return False

    def deposit_for_customer(self, agent_id, amount):
        self.customer_balances[agent_id] = self.customer_balances.get(agent_id, 0) + amount

    def get_total_deposits(self):
        return sum(self.customer_balances.values())


class MockSettlementSystem:
    def __init__(self, agents):
        self.agents = agents
        self.settlement_accounts = {} # Mock needed for audit?
        # Actually audit_total_m2 in real system checks settlement_accounts.
        # We will mock audit_total_m2 to return True or implement simple version.

    def mint_and_distribute(self, target_agent_id, amount, tick, reason):
        # Find agent
        agent = next((a for a in self.agents if a.id == target_agent_id), None)
        if agent:
            agent._deposit(amount)
            return True
        return False

    def audit_total_m2(self, expected_total=None):
        # Calculate M2 from agents
        total_cash = 0
        total_deposits = 0
        bank_reserves = 0

        for agent in self.agents:
            if agent.id == ID_CENTRAL_BANK: continue

            cash = agent.get_balance()
            total_cash += cash

            if isinstance(agent, MockBank):
                bank_reserves += cash
                total_deposits += agent.get_total_deposits()

        # M2 = (Cash - Reserves) + Deposits
        current_m2 = (total_cash - bank_reserves) + total_deposits

        if expected_total is not None:
            return current_m2 == expected_total
        return True

    def transfer_and_destroy(self, source, sink_authority, amount, reason, tick):
        source._withdraw(amount)
        # Sink (CB) logic omitted (infinite sink)
        return True

    def transfer(self, debit_agent, credit_agent, amount, memo, tick):
        # Implement transfer for test
        try:
            debit_agent._withdraw(amount)
            credit_agent._deposit(amount)
            return True # In real system returns Transaction
        except Exception:
            return None

    def get_account_holders(self, bank_id):
        # ST-002: Mock reverse index logic
        # For this test, we assume we can just look at the bank attached to this mock.
        if hasattr(self, 'bank') and self.bank.id == bank_id:
            return list(self.bank.customer_balances.keys())
        return []

# --- Fixtures ---

@pytest.fixture
def test_env():
    # Agents
    cb = MockAgent(ID_CENTRAL_BANK, balance=0)
    bank = MockBank("BANK_01", balance=10000) # Bank has reserves
    h1 = MockAgent(101, balance=500, inventory={"food": 10})
    h2 = MockAgent(102, balance=500, inventory={"food": 20})
    f1 = MockAgent(201, balance=2000, inventory={"widget": 100}, sector="MANUFACTURING")

    # Setup Deposits
    bank.deposit_for_customer(101, 1000)
    bank.deposit_for_customer(102, 1000)
    bank.deposit_for_customer(201, 5000)

    agents = [cb, bank, h1, h2, f1]

    # Registries
    # Not using spec=IAgentRegistry because get_all_agents is not in the interface definition but used by CommandService
    agent_registry = MagicMock()
    agent_registry.get_all_agents.return_value = agents
    agent_registry.get_agent = lambda id: next((a for a in agents if a.id == id or str(a.id) == str(id)), None)
    agent_registry.get_all_financial_agents.return_value = agents

    registry = create_autospec(IGlobalRegistry, instance=True)
    registry.get.return_value = 1.0
    registry.set.return_value = True

    settlement = MockSettlementSystem(agents)
    settlement.bank = bank # Link bank

    service = CommandService(registry, settlement, agent_registry)

    return {
        "service": service,
        "agents": agents,
        "bank": bank,
        "registry": registry,
        "settlement": settlement
    }

# --- Tests ---

def test_hyperinflation_scenario(test_env):
    """
    ST-001: Inject massive cash and verify M2 integrity.
    """
    service = test_env["service"]
    h1 = test_env["agents"][2]

    # Initial M2 check (Implicitly done by execute_command_batch if baseline passed)
    # Baseline M2:
    # Cash: Bank(10000) + H1(500) + H2(500) + F1(2000) = 13000
    # Reserves: 10000
    # Deposits: 1000 + 1000 + 5000 = 7000
    # M2 = (13000 - 10000) + 7000 = 3000 + 7000 = 10000

    baseline_m2 = 10000

    # Command: Inject 10,000 to H1
    cmd = GodCommandDTO(
        command_id=uuid4(),
        command_type="INJECT_ASSET",
        target_domain="Economy",
        parameter_key="101", # Target H1
        new_value=10000
    )

    results = service.execute_command_batch([cmd], tick=100, baseline_m2=baseline_m2)

    assert len(results) == 1
    assert results[0].success is True
    assert h1.get_balance() == 10500 # 500 + 10000

    # M2 should now be 20000 (10000 initial + 10000 injection)
    # Verify Audit Logic in Settlement
    # Cash: 13000 + 10000 = 23000
    # Reserves: 10000
    # Deposits: 7000
    # M2 = 13000 + 7000 = 20000. Correct.

def test_bank_run_scenario(test_env):
    """
    ST-002: Force withdraw all deposits.
    """
    service = test_env["service"]
    bank = test_env["bank"]
    h1 = test_env["agents"][2]

    baseline_m2 = 10000

    # Command: FORCE_WITHDRAW_ALL
    cmd = GodCommandDTO(
        command_id=uuid4(),
        command_type="TRIGGER_EVENT",
        target_domain="System",
        parameter_key="FORCE_WITHDRAW_ALL",
        new_value={"bank_id": "BANK_01"}
    )

    results = service.execute_command_batch([cmd], tick=101, baseline_m2=baseline_m2)

    assert results[0].success is True

    # Verify H1 withdrawn
    # H1 had 1000 deposit. 500 cash.
    # Now should have 0 deposit. 1500 cash.
    assert bank.get_customer_balance(101) == 0
    assert h1.get_balance() == 1500

    # Verify Bank Deposits total 0
    assert bank.get_total_deposits() == 0

    # Verify Bank Cash Reserves Decreased (Zero-Sum Check)
    # Total withdrawn = 1000 (H1) + 1000 (H2) + 5000 (F1) = 7000
    # Bank Initial Cash = 10000
    # Bank Final Cash should be 3000
    assert bank.get_balance() == 3000

    # Verify M2 Integrity
    # Cash: Bank(3000) + H1(1500) + H2(1500) + F1(7000) = 13000
    # Reserves: 3000
    # Deposits: 0
    # M2 = (13000 - 3000) + 0 = 10000.
    # M2 Preserved!

def test_inventory_destruction_scenario(test_env):
    """
    ST-003: Destroy inventory.
    """
    service = test_env["service"]
    f1 = test_env["agents"][4] # F1

    # F1 has 100 widgets
    assert f1.get_quantity("widget") == 100

    # Command: DESTROY_INVENTORY ratio 0.5
    cmd = GodCommandDTO(
        command_id=uuid4(),
        command_type="TRIGGER_EVENT",
        target_domain="System",
        parameter_key="DESTROY_INVENTORY",
        new_value={"ratio": 0.5}
    )

    # Baseline M2 irrelevant for this command but required by sig
    service.execute_command_batch([cmd], tick=102, baseline_m2=10000)

    # Verify destruction
    # 100 * 0.5 = 50 destroyed. Remaining 50.
    assert f1.get_quantity("widget") == 50

def test_parameter_rollback(test_env):
    """
    ST-004: Set param, Undo, Verify.
    """
    service = test_env["service"]
    registry = test_env["registry"]

    # 1. Set Param
    cmd = GodCommandDTO(
        command_id=uuid4(),
        command_type="SET_PARAM",
        target_domain="Gov",
        parameter_key="tax_rate",
        new_value=0.5
    )

    # Mock current value 0.1
    registry.get.return_value = 0.1
    # Mock previous entry for rollback logic (CommandService uses get_entry to snapshot)
    registry.get_entry.return_value = RegistryEntry(key="tax_rate", value=0.1, origin=OriginType.CONFIG)

    service.execute_command_batch([cmd], tick=103, baseline_m2=10000)

    # Verify Set called
    registry.set.assert_called_with("tax_rate", 0.5, origin=OriginType.GOD_MODE)

    # 2. Undo (Rollback Last Tick)
    # CommandService rollback is triggered by failure OR manual undo?
    # CommandService has `rollback_last_tick` but it is internal usually.
    # However, `CommandService.undo_stack` is public-ish.
    # We can manually call `rollback_last_tick` to simulate UNDO command (if we had one exposed).
    # The plan says "Undo Last Command".
    # Assuming we add an endpoint or just call the method for test.

    success = service.rollback_last_tick()
    assert success is True

    # Verify Set called with original value
    registry.set.assert_called_with("tax_rate", 0.1, origin=OriginType.CONFIG)
