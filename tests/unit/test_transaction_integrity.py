import pytest
from unittest.mock import MagicMock
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.settlement_system import SettlementSystem
from simulation.models import Transaction

class TestTransactionIntegrity:

    def test_commerce_system_transaction_total_pennies(self):
        """
        Verify that CommerceSystem.plan_consumption_and_leisure creates transactions with total_pennies set.
        """
        config = MagicMock()
        config.DEFAULT_FALLBACK_PRICE = 5.0

        system = CommerceSystem(config)

        # Mock Context
        context = {
            "households": [],
            "breeding_planner": MagicMock(),
            "market_data": {"basic_food_current_sell_price": 5.0},
            "time": 1,
            "household_time_allocation": {},
            "agents": {}
        }

        # Setup Breeding Planner to return a 'buy' decision
        # Ensure survival_threshold is a float to match comparison logic
        context["breeding_planner"].survival_threshold = 50.0
        context["breeding_planner"].decide_consumption_batch.return_value = {
            "consume": [0.0],
            "buy": [1.0], # Buy 1 unit
            "price": 5.0  # Price $5.00
        }

        # Create a mock household
        household = MagicMock()
        household.id = 1
        household._bio_state.is_active = True
        household._econ_state.is_employed = True
        # Assets handling in CommerceSystem: cash = assets.get(DEFAULT_CURRENCY)
        # Using a dict for assets
        household._econ_state.assets = { "USD": 1000 }

        # Mocking needs.get
        # survival_need = household._bio_state.needs.get("survival", 0.0)
        # We need household._bio_state.needs to be a dict or behave like one
        household._bio_state.needs = {"survival": 40.0}

        context["households"] = [household]

        # Execute
        planned, transactions = system.plan_consumption_and_leisure(context)

        assert len(transactions) == 1
        tx = transactions[0]

        # Expected: 1 unit * $5.00 = 500 pennies
        assert getattr(tx, 'total_pennies', 0) == 500
        assert tx.price == 5.0

    def test_settlement_system_record_total_pennies(self):
        """
        Verify that SettlementSystem._create_transaction_record sets total_pennies.
        """
        system = SettlementSystem()

        # Call private method directly for testing
        tx = system._create_transaction_record(
            buyer_id=1,
            seller_id=2,
            amount=100, # 100 pennies transfer
            memo="test",
            tick=1
        )

        assert tx is not None
        assert getattr(tx, 'total_pennies', 0) == 100
        assert tx.quantity == 1.0
        # If amount is 100 pennies, and quantity is 1.0, then price per unit is 1.00 dollar
        # total_pennies 100 = 1.00 dollar.
        # quantity 1.0.
        # price * quantity = 1.00 * 1.0 = 1.00. Correct.
        assert tx.price == 1.0
