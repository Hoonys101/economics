import pytest
from unittest.mock import MagicMock
from simulation.models import Transaction, Order
from modules.system.execution.public_manager import PublicManager
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.systems.handlers.public_manager_handler import PublicManagerTransactionHandler
from simulation.systems.registry import Registry
from simulation.systems.accounting import AccountingSystem
from modules.system.api import MarketSignalDTO, DEFAULT_CURRENCY
from modules.simulation.api import IInventoryHandler, InventorySlot

class MockAgent(IInventoryHandler):
    def __init__(self, agent_id, assets=0.0):
        self.id = agent_id
        self.assets = assets
        self.inventory = {}
        self.inventory_quality = {}
        self.total_money_issued = 0.0 # for central bank checks if any

    def withdraw(self, amount, currency=DEFAULT_CURRENCY):
        if self.assets < amount:
            raise Exception(f"Insufficient funds: {self.assets} < {amount}")
        self.assets -= amount

    def deposit(self, amount, currency=DEFAULT_CURRENCY):
        self.assets += amount

    def get_balance(self, currency=DEFAULT_CURRENCY):
        return self.assets

    def get_all_balances(self):
        return {DEFAULT_CURRENCY: self.assets}

    @property
    def total_wealth(self):
        return self.assets

    def add_item(self, item_id, quantity, quality=1.0, slot=None):
        self.inventory[item_id] = self.inventory.get(item_id, 0.0) + quantity

    def consume(self, item_id, quantity, time):
        pass

    @property
    def current_consumption(self):
        return 0.0

    @current_consumption.setter
    def current_consumption(self, value):
        pass

    @property
    def current_food_consumption(self):
        return 0.0

    @current_food_consumption.setter
    def current_food_consumption(self, value):
        pass

class TestPublicManagerIntegration:
    def test_full_liquidation_cycle(self):
        # 1. Setup PublicManager
        config = MagicMock()
        config.LIQUIDATION_SELL_RATE = 1.0 # Sell all for test
        config.LIQUIDATION_ASK_UNDERCUT = 0.0
        # Setup GOODS config for Registry
        config.GOODS = {
            "gold": {"is_service": False, "is_essential": False}
        }
        config.RAW_MATERIAL_SECTORS = []
        config.SALES_TAX_RATE = 0.0
        config.INCOME_TAX_PAYER = "HOUSEHOLD"
        config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        config.GOODS_INITIAL_PRICE = {}

        pm = PublicManager(config)

        # 2. Simulate Bankruptcy Event
        event = {
            "agent_id": 99,
            "tick": 1,
            "inventory": {"gold": 10.0}
        }
        pm.process_bankruptcy_event(event)
        assert pm.managed_inventory["gold"] == 10.0

        # 3. Generate Liquidation Orders (Phase 4.5)
        # Mock Market Signals
        signals = {
            "gold": MarketSignalDTO(
                market_id="gold",
                item_id="gold",
                best_ask=100.0,
                best_bid=90.0,
                last_traded_price=95.0,
                last_trade_tick=1,
                price_history_7d=[],
                volatility_7d=0.0,
                order_book_depth_buy=1,
                order_book_depth_sell=1,
                total_bid_quantity=0.0,
                total_ask_quantity=0.0,
                is_frozen=False
            )
        }
        orders = pm.generate_liquidation_orders(signals, MagicMock(), MagicMock())
        assert len(orders) == 1
        order = orders[0]
        assert order.quantity == 10.0
        assert order.price == 100.0
        assert pm.managed_inventory["gold"] == 10.0 # NOT Tentatively decremented

        # 4. Simulate Market Matching (Phase 2/5)
        # Assume market matched it perfectly
        buyer = MockAgent(2, assets=500000.0) # Enough assets for 100000 pennies

        tx = Transaction(
            item_id="gold",
            quantity=10.0,
            price=100.0,
            buyer_id=buyer.id,
            seller_id="PUBLIC_MANAGER", # Explicitly set seller to PM
            market_id="gold",
            transaction_type="goods",
            time=1
        , total_pennies=100000)

        # 5. Execute Transaction (Phase 3)
        # Setup TransactionProcessor
        tp = TransactionProcessor(config_module=config)
        tp.register_public_manager_handler(PublicManagerTransactionHandler())

        # Mock Settlement System
        settlement = MagicMock()

        def transfer_side_effect(buyer_agent, seller_agent, amount, memo):
             buyer_agent.withdraw(amount)
             if seller_agent == pm:
                 pm.deposit_revenue(amount)
             return True

        def settle_atomic_side_effect(payer, credits, time):
             total_amount = sum(c[1] for c in credits)
             payer.withdraw(total_amount)
             for payee, amount, memo in credits:
                 if payee == pm:
                     pm.deposit_revenue(amount)
             return True

        settlement.transfer.side_effect = transfer_side_effect
        settlement.settle_atomic.side_effect = settle_atomic_side_effect

        # Setup State
        state = MagicMock()
        state.transactions = [tx]
        state.agents = {buyer.id: buyer}
        state.inactive_agents = {}
        state.public_manager = pm
        state.market_data = {}
        state.config_module = config
        state.time = 1
        state.settlement_system = settlement
        state.taxation_system = None # Should be auto-initialized by TP
        state.stock_market = None
        state.real_estate_units = []
        state.logger = MagicMock()
        state.bank = None
        state.central_bank = None
        state.shareholder_registry = None

        # Mock Government in state because settle_atomic calculates tax credits to government
        state.government = MagicMock()

        tp.execute(state)

        # 6. Verify Outcome
        # PublicManager treasury should increase
        assert pm.system_treasury[DEFAULT_CURRENCY] == 100000.0

        # PublicManager inventory should decrease (via confirm_sale)
        assert pm.managed_inventory["gold"] == 0.0

        # Buyer inventory should increase
        assert buyer.inventory["gold"] == 10.0

        # Buyer assets check
        assert buyer.assets == 400000.0
