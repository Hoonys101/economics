import pytest
from unittest.mock import MagicMock, ANY
from typing import List, Dict, Optional
from modules.common.interfaces import IPropertyOwner, IResident, IMortgageBorrower
from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
from simulation.models import Transaction
from modules.system.escrow_agent import EscrowAgent
from modules.system.api import DEFAULT_CURRENCY

class MockAgent:
    def __init__(self, id, assets=None):
        self.id = id
        self.assets = assets or {DEFAULT_CURRENCY: 100000.0}
        self.current_wage = 5000.0
        self.owned_properties: List[int] = []
        self.residing_property_id: Optional[int] = None
        self.is_homeless: bool = True

    def add_property(self, property_id: int) -> None:
        self.owned_properties.append(property_id)

    def remove_property(self, property_id: int) -> None:
        if property_id in self.owned_properties:
            self.owned_properties.remove(property_id)

def test_housing_handler_with_protocol_agent():
    # Setup
    handler = HousingTransactionHandler()

    buyer = MockAgent(id=101)
    # Ensure buyer implements protocols (runtime check)
    assert isinstance(buyer, IMortgageBorrower)
    assert isinstance(buyer, IPropertyOwner)
    assert isinstance(buyer, IResident)

    seller = MockAgent(id=102)
    seller.add_property(999)

    # Context mocks
    context = MagicMock()
    context.time = 1

    # Escrow Agent
    escrow = EscrowAgent(id=9999)
    context.agents = {
        101: buyer,
        102: seller,
        9999: escrow
    }

    # Unit
    unit = MagicMock()
    unit.id = 999
    unit.liens = []
    context.real_estate_units = [unit]

    # Config
    context.config_module.housing = {"max_ltv_ratio": 0.8, "mortgage_term_ticks": 300}
    context.config_module.MORTGAGE_INTEREST_RATE = 0.05
    context.config_module.WORK_HOURS_PER_DAY = 8.0
    context.config_module.TICKS_PER_YEAR = 100.0

    # Bank
    context.bank = MagicMock()
    context.bank.grant_loan.return_value = ({"loan_id": "loan_1"}, MagicMock())
    context.bank.withdraw_for_customer.return_value = True
    context.bank.id = 8888

    # Settlement
    context.settlement_system.transfer.return_value = True

    # Transaction
    tx = Transaction(
        buyer_id=101,
        seller_id=102,
        item_id="unit_999",
        quantity=1,
        price=1000.0,
        market_id="housing_market",
        transaction_type="housing",
        time=1,
        metadata={}
    )

    # Execute
    result = handler.handle(tx, buyer, seller, context)

    # Verify
    assert result is True
    assert 999 in buyer.owned_properties
    # Mock unit update
    assert unit.owner_id == 101

    # Verify banking logic was triggered (grant_loan called)
    context.bank.grant_loan.assert_called()

    # Verify remove property called on seller
    assert 999 not in seller.owned_properties

def test_protocol_compliance():
    """Verify MockAgent satisfies protocols via isinstance check."""
    agent = MockAgent(1)
    assert isinstance(agent, IMortgageBorrower)
    assert isinstance(agent, IPropertyOwner)
    assert isinstance(agent, IResident)
