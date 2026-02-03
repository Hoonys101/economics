import pytest
from unittest.mock import MagicMock
from modules.government.taxation.system import TaxationSystem
from simulation.models import Transaction
from simulation.dtos.settlement_dtos import SettlementResultDTO

class MockConfig:
    taxation = {"corporate_tax_rate": 0.25}
    # For backward compatibility test if code falls back to attributes
    SALES_TAX_RATE = 0.05
    TAX_BRACKETS = []
    TAX_RATE_BASE = 0.1
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    GOODS_INITIAL_PRICE = {"basic_food": 5.0}
    TAX_MODE = "PROGRESSIVE"
    INCOME_TAX_PAYER = "HOUSEHOLD"

def test_generate_corporate_tax_intents():
    config = MockConfig()
    system = TaxationSystem(config)

    firm1 = MagicMock()
    firm1.is_active = True
    firm1.id = 1
    # Profit = 1000 - 500 = 500
    firm1.finance.revenue_this_turn = 1000.0
    firm1.finance.cost_this_turn = 500.0

    firm2 = MagicMock()
    firm2.is_active = True
    firm2.id = 2
    # Profit = 200 - 300 = -100 (Loss)
    firm2.finance.revenue_this_turn = 200.0
    firm2.finance.cost_this_turn = 300.0

    firms = [firm1, firm2]

    intents = system.generate_corporate_tax_intents(firms)

    assert len(intents) == 1
    tx = intents[0]
    assert tx.buyer_id == 1
    assert tx.item_id == "corporate_tax"
    assert tx.price == 125.0 # 500 * 0.25

def test_record_revenue_success():
    config = MockConfig()
    system = TaxationSystem(config)

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="corporate_tax",
        quantity=1, price=100.0, market_id="system", transaction_type="tax", time=1
    )
    result = SettlementResultDTO(
        original_transaction=tx,
        success=True,
        amount_settled=100.0
    )

    # Just ensure no error, logic is logging
    system.record_revenue([result])

def test_record_revenue_failure():
    config = MockConfig()
    system = TaxationSystem(config)

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="corporate_tax",
        quantity=1, price=100.0, market_id="system", transaction_type="tax", time=1
    )
    result = SettlementResultDTO(
        original_transaction=tx,
        success=False,
        amount_settled=0.0
    )

    system.record_revenue([result])
