import pytest
from unittest.mock import MagicMock, Mock
from modules.government.taxation.system import TaxationSystem
from modules.government.taxation.api import TaxIntentDTO

@pytest.fixture
def config_module():
    mock = MagicMock()
    mock.SALES_TAX_RATE = 0.05
    mock.INCOME_TAX_PAYER = "HOUSEHOLD"
    mock.TAX_MODE = "FLAT"
    mock.TAX_BRACKETS = []
    mock.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    mock.GOODS_INITIAL_PRICE = {"basic_food": 5.0}
    mock.TAX_RATE_BASE = 0.1
    return mock

@pytest.fixture
def taxation_system(config_module):
    return TaxationSystem(config_module)

def test_sales_tax_calculation(taxation_system, config_module):
    # Setup
    tx = Mock()
    tx.buyer_id = 1
    tx.seller_id = 2
    tx.transaction_type = "goods"
    tx.quantity = 10
    tx.price = 10.0 # Trade Value = 100

    buyer = Mock()
    buyer.id = 1
    seller = Mock()
    seller.id = 2
    government = Mock()
    government.id = 99

    state = Mock()
    state.agents = {1: buyer, 2: seller}
    state.government = government
    state.market_data = {}

    # Execute
    intents = taxation_system.generate_tax_intents(tx, state)

    # Verify
    assert len(intents) == 1
    intent = intents[0]
    assert intent['payer_id'] == buyer.id
    assert intent['payee_id'] == government.id
    assert intent['amount'] == 100 * 0.05 # 5.0
    assert "sales_tax" in intent['tax_type']

def test_income_tax_household_payer(taxation_system, config_module):
    # Setup
    config_module.INCOME_TAX_PAYER = "HOUSEHOLD"

    tx = Mock()
    tx.buyer_id = 10
    tx.seller_id = 20
    tx.transaction_type = "labor"
    tx.quantity = 1
    tx.price = 100.0

    buyer = Mock()
    buyer.id = 10 # Firm
    seller = Mock()
    seller.id = 20 # Household (Worker)

    government = Mock()
    government.id = 99
    government.income_tax_rate = 0.1

    state = Mock()
    state.agents = {10: buyer, 20: seller}
    state.government = government
    state.market_data = {}

    # Execute
    intents = taxation_system.generate_tax_intents(tx, state)

    # Verify
    assert len(intents) == 1
    intent = intents[0]
    assert intent['payer_id'] == seller.id # Household pays
    assert intent['amount'] == 100.0 * 0.1 # 10.0 (Flat rate mocked)
    assert intent['tax_type'] == "income_tax_household"

def test_income_tax_firm_payer(taxation_system, config_module):
    # Setup
    config_module.INCOME_TAX_PAYER = "FIRM"

    tx = Mock()
    tx.buyer_id = 10
    tx.seller_id = 20
    tx.transaction_type = "labor"
    tx.quantity = 1
    tx.price = 100.0

    buyer = Mock()
    buyer.id = 10
    seller = Mock()
    seller.id = 20

    government = Mock()
    government.id = 99
    government.income_tax_rate = 0.1

    state = Mock()
    state.agents = {10: buyer, 20: seller}
    state.government = government
    state.market_data = {}

    # Execute
    intents = taxation_system.generate_tax_intents(tx, state)

    # Verify
    assert len(intents) == 1
    intent = intents[0]
    assert intent['payer_id'] == buyer.id # Firm pays
    assert intent['amount'] == 100.0 * 0.1
    assert intent['tax_type'] == "income_tax_firm"

def test_escheatment(taxation_system):
    tx = Mock()
    tx.buyer_id = 666
    tx.seller_id = 99
    tx.transaction_type = "escheatment"
    tx.quantity = 1
    tx.price = 500.0

    buyer = Mock()
    buyer.id = 666 # Deceased
    seller = Mock() # Gov
    government = Mock()
    government.id = 99

    state = Mock()
    state.agents = {666: buyer}
    state.government = government
    state.market_data = {}

    intents = taxation_system.generate_tax_intents(tx, state)

    assert len(intents) == 1
    intent = intents[0]
    assert intent['payer_id'] == buyer.id
    assert intent['payee_id'] == government.id
    assert intent['amount'] == 500.0
    assert intent['tax_type'] == "escheatment"
