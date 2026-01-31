import pytest
from unittest.mock import MagicMock, Mock
from typing import List, Dict, Any

from modules.government.taxation.system import TaxationSystem
from simulation.systems.settlement_system import SettlementSystem
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.models import Transaction
from simulation.finance.api import PaymentIntentDTO, IFinancialEntity
from modules.finance.api import InsufficientFundsError
from modules.government.taxation.api import TaxIntentDTO

# --- Mocks ---

class MockEntity:
    def __init__(self, id, assets=0.0):
        self.id = id
        self._assets = float(assets)
        self.fail_deposit = False
        self.inventory = {}
        self.inventory_quality = {}
        self.shares_owned = {}
        self.check_solvency_called = False

    @property
    def assets(self):
        return self._assets

    def deposit(self, amount):
        if self.fail_deposit:
            raise Exception("Deposit failed!")
        self._assets += amount

    def withdraw(self, amount):
        if self._assets < amount:
            raise InsufficientFundsError(f"Insufficient funds: {self._assets} < {amount}")
        self._assets -= amount

    def check_solvency(self, government):
        pass

class MockGovernment(MockEntity):
    def __init__(self, id, assets=0.0):
        super().__init__(id, assets)
        self.taxation_system = None
        self.income_tax_rate = 0.1
        self.corporate_tax_rate = 0.2

class MockConfig:
    SALES_TAX_RATE = 0.10
    TAX_MODE = "PROGRESSIVE"
    TAX_BRACKETS = []
    TAX_RATE_BASE = 0.1
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    GOODS_INITIAL_PRICE = {"basic_food": 5.0}
    INCOME_TAX_PAYER = "FIRM" # Default
    GOODS = {}
    RAW_MATERIAL_SECTORS = []
    RND_PRODUCTIVITY_MULTIPLIER = 1.0

class MockState:
    def __init__(self):
        self.transactions = []
        self.agents = {}
        self.government = None
        self.settlement_system = None
        self.market_data = {}
        self.time = 0
        self.logger = MagicMock()
        self.stock_market = None
        self.real_estate_units = []
        self.effects_queue = []

# --- Tests ---

def test_taxation_calculation():
    config = MockConfig()
    tax_system = TaxationSystem(config)

    gov = MockGovernment(id=999)
    buyer = MockEntity(id=1, assets=1000)
    seller = MockEntity(id=2, assets=1000)

    state = MockState()
    state.government = gov
    state.agents = {1: buyer, 2: seller}

    # Test Goods (Sales Tax)
    tx = Transaction(buyer_id=1, seller_id=2, item_id="apple", quantity=10, price=10.0,
                     market_id="goods", transaction_type="goods", time=1)
    # Trade Value = 100. Tax Rate = 0.10. Tax = 10.

    intents = tax_system.generate_tax_intents(tx, state)
    assert len(intents) == 1
    assert intents[0]['payer_id'] == 1
    assert intents[0]['payee_id'] == 999
    assert intents[0]['amount'] == 10.0
    assert intents[0]['tax_type'] == "sales_tax_goods"

def test_settlement_atomic_success():
    settlement = SettlementSystem()
    payer = MockEntity(id=1, assets=200.0)
    payee1 = MockEntity(id=2, assets=0.0)
    payee2 = MockEntity(id=3, assets=0.0)

    intents: List[PaymentIntentDTO] = [
        {"payee": payee1, "amount": 100.0, "memo": "payment1"},
        {"payee": payee2, "amount": 50.0, "memo": "payment2"}
    ]

    success = settlement.settle_escrow(payer, intents, tick=1)

    assert success is True
    assert payer.assets == 50.0 # 200 - 150
    assert payee1.assets == 100.0
    assert payee2.assets == 50.0

def test_settlement_atomic_rollback():
    settlement = SettlementSystem()
    payer = MockEntity(id=1, assets=200.0)
    payee1 = MockEntity(id=2, assets=0.0)
    payee2 = MockEntity(id=3, assets=0.0)
    payee2.fail_deposit = True # Trigger failure

    intents: List[PaymentIntentDTO] = [
        {"payee": payee1, "amount": 100.0, "memo": "payment1"},
        {"payee": payee2, "amount": 50.0, "memo": "payment2"} # This will fail
    ]

    success = settlement.settle_escrow(payer, intents, tick=1)

    assert success is False
    assert payer.assets == 200.0 # Fully restored
    assert payee1.assets == 0.0 # Rolled back
    assert payee2.assets == 0.0 # Failed

def test_transaction_processor_goods_flow():
    config = MockConfig()

    gov = MockGovernment(id=999, assets=0.0)
    tax_system = TaxationSystem(config)
    gov.taxation_system = tax_system

    settlement = SettlementSystem()

    tp = TransactionProcessor(config)

    buyer = MockEntity(id=1, assets=200.0)
    seller = MockEntity(id=2, assets=0.0)

    state = MockState()
    state.government = gov
    state.settlement_system = settlement
    state.agents = {1: buyer, 2: seller}
    state.time = 1

    tx = Transaction(buyer_id=1, seller_id=2, item_id="apple", quantity=10, price=10.0,
                     market_id="goods", transaction_type="goods", time=1)
    state.transactions = [tx]

    tp.execute(state)

    # Verify Financials
    # Trade: 100. Tax: 10 (10%). Total Cost: 110.
    assert buyer.assets == 90.0 # 200 - 110
    assert seller.assets == 100.0

    # Verify Tax Revenue Ledger
    assert tax_system.tax_revenue_ledger.get("sales_tax_goods") == 10.0

    # Verify Government Access
    tick_revenue = tax_system.get_tick_revenue(1)
    assert tick_revenue["sales_tax_goods"] == 10.0

def test_transaction_processor_labor_flow_withholding():
    config = MockConfig()
    config.INCOME_TAX_PAYER = "FIRM" # Withholding

    gov = MockGovernment(id=999, assets=0.0)
    tax_system = TaxationSystem(config)
    gov.taxation_system = tax_system

    settlement = SettlementSystem()

    tp = TransactionProcessor(config)

    firm = MockEntity(id=1, assets=200.0) # Buyer of Labor
    worker = MockEntity(id=2, assets=0.0) # Seller of Labor

    state = MockState()
    state.government = gov
    state.settlement_system = settlement
    state.agents = {1: firm, 2: worker}

    # Labor Transaction
    tx = Transaction(buyer_id=1, seller_id=2, item_id="labor_hours", quantity=1, price=100.0,
                     market_id="labor", transaction_type="labor", time=1)
    state.transactions = [tx]

    # Gov Income Tax Rate is 0.1 (10%)
    # Tax = 10.0.
    # Payer is Firm (INCOME_TAX_PAYER="FIRM").
    # Intent: Firm -> Gov (10.0).
    # Logic in TP:
    #   Net Trade Value = 100 (Price) - 0 (Deduction from Seller) = 100?
    #   Wait, if Payer is Firm, it is an "Add-on" cost or "Deduction"?
    #   Usually Wage is Gross. Firm pays Gross.
    #   If Payer is Firm, it means Firm pays Tax ON TOP of Wage? Or Firm pays Tax FROM Wage?
    #   In `TaxationSystem`:
    #   if tax_payer_type == "FIRM": payer_id = buyer.id
    #   If Firm pays, it's usually Employer Payroll Tax (on top).
    #   If Worker pays (but withheld), payer_id is Worker (Seller).

    # Let's verify TP logic:
    # if ti['payer_id'] == seller.id: net_trade_value -= ti['amount']

    # Case A: Payroll Tax (Firm Pays). ti['payer_id'] == buyer.id.
    #   net_trade_value = 100.
    #   Tax Intent = 10 (Firm -> Gov).
    #   Total Firm Pay = 110. Worker gets 100. Gov gets 10.

    tp.execute(state)

    # Taxable = 100 - 10 (Survival Cost) = 90. Tax = 9.0.
    # Total Cost = 100 + 9 = 109.
    assert firm.assets == 91.0 # 200 - 109
    assert worker.assets == 100.0
    assert tax_system.tax_revenue_ledger.get("income_tax_firm") == 9.0

def test_transaction_processor_labor_flow_worker_pays():
    config = MockConfig()
    config.INCOME_TAX_PAYER = "HOUSEHOLD" # Worker pays (Withholding logic in TP)

    gov = MockGovernment(id=999, assets=0.0)
    tax_system = TaxationSystem(config)
    gov.taxation_system = tax_system

    settlement = SettlementSystem()

    tp = TransactionProcessor(config)

    firm = MockEntity(id=1, assets=200.0)
    worker = MockEntity(id=2, assets=0.0)

    state = MockState()
    state.government = gov
    state.settlement_system = settlement
    state.agents = {1: firm, 2: worker}

    tx = Transaction(buyer_id=1, seller_id=2, item_id="labor_hours", quantity=1, price=100.0,
                     market_id="labor", transaction_type="labor", time=1)
    state.transactions = [tx]

    # Logic:
    # Tax = 10.
    # Payer = Seller (Worker).
    # TP Logic:
    #   if ti['payer_id'] == seller.id: net_trade_value -= ti['amount']
    #   net_trade_value = 100 - 10 = 90.
    #   Tax Intent: Firm -> Gov (10). (Constructed in TP loop)
    #   Firm pays 90 to Worker, 10 to Gov. Total 100.

    tp.execute(state)

    # Tax = 9.0.
    # Net Wage = 100 - 9 = 91.
    assert firm.assets == 100.0 # 200 - 100.
    assert worker.assets == 91.0 # Received Net Wage
    assert tax_system.tax_revenue_ledger.get("income_tax_household") == 9.0
