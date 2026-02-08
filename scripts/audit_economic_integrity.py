import sys
import os
import logging
import math
from typing import Dict, Any, List

# Add project root to sys.path
sys.path.append(os.getcwd())

from simulation.models import Transaction, RealEstateUnit
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.systems.handlers.monetary_handler import MonetaryTransactionHandler
from simulation.systems.handlers.asset_transfer_handler import AssetTransferHandler
from modules.government.taxation.system import TaxationSystem, TaxIntent
from modules.system.api import DEFAULT_CURRENCY
from simulation.dtos.settlement_dtos import SettlementResultDTO
from simulation.systems.transaction_processor import TransactionProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AUDIT")

def audit_sales_tax_atomicity():
    logger.info("--- Auditing Sales Tax Atomicity ---")

    # Mock Context
    class MockConfig:
        SALES_TAX_RATE = 0.05
        DEFAULT_FALLBACK_PRICE = 5.0
        GOODS_INITIAL_PRICE = {"basic_food": 5.0}
        HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0

    class MockContext(dict):
        def __getattr__(self, key):
            return self.get(key)
        def __setattr__(self, key, value):
            self[key] = value

    config = MockConfig()
    tax_system = TaxationSystem(config)
    commerce_system = CommerceSystem(config)

    # Test Cases: Price, Quantity
    test_cases = [
        (10.0, 1.0),   # Simple
        (10.123, 1.0), # Rounding edge case
        (9.99, 3.0),   # Quantity > 1
        (0.01, 100.0), # Small price, large quantity
        (12345.67, 1.0) # Large price
    ]

    failures = 0

    for price, quantity in test_cases:
        # 1. Commerce System Calculation (What it thinks it costs)
        # Emulate CommerceSystem logic
        tax_rate = config.SALES_TAX_RATE

        # New logic: Use the new method
        commerce_cost = commerce_system.calculate_total_cost(price, quantity, tax_rate)

        # 2. Goods Handler Calculation (What it actually costs to execute)
        # Emulate GoodsTransactionHandler logic
        # trade_value = round(tx.quantity * tx.price, 2)
        trade_value = round(quantity * price, 2)

        # Emulate TaxationSystem logic used by GoodsHandler
        # tax_amount = self._round_currency(trade_value * sales_tax_rate)
        tax_amount = round(trade_value * tax_rate, 2)

        execution_cost = trade_value + tax_amount

        diff = abs(commerce_cost - execution_cost)

        logger.info(f"Price: {price}, Qty: {quantity}")
        logger.info(f"  Commerce Cost: {commerce_cost:.5f}")
        logger.info(f"  Execution Cost: {execution_cost:.5f}")
        logger.info(f"  Diff: {diff:.5f}")

        if diff > 0.00001: # Tolerance for float comparison
             # Check if this difference matters for affordability check
             # If agent has exactly execution_cost, Commerce says it costs less/more?

             # Case 1: Commerce < Execution. Agent has Commerce cost but not Execution cost.
             if commerce_cost < execution_cost:
                 logger.error("  FAILURE: Commerce underestimates cost! Transaction will fail if agent has exact amount.")
                 failures += 1

             # Case 2: Commerce > Execution. Agent has Execution cost but Commerce says no.
             elif commerce_cost > execution_cost:
                 logger.warning("  WARNING: Commerce overestimates cost. Agent might be denied purchase unnecessarily.")
                 # failures += 1 # Strict audit might fail this too, but underestimation is worse.

    if failures == 0:
        logger.info("Sales Tax Atomicity Audit PASSED (No underestimation failures).")
    else:
        logger.error(f"Sales Tax Atomicity Audit FAILED with {failures} failures.")

def audit_inheritance_leaks():
    logger.info("--- Auditing Inheritance Leaks & Duplication ---")

    # Check for code duplication in MonetaryTransactionHandler vs AssetTransferHandler
    monetary_handler = MonetaryTransactionHandler()
    asset_handler = AssetTransferHandler()

    # We can't easily check for code duplication programmatically without parsing AST or text.
    # But we can check if they handle the same logic differently.

    # 1. Check if `MonetaryTransactionHandler` delegates to `AssetTransferHandler`
    logger.info("Checking MonetaryTransactionHandler implementation...")
    import inspect

    try:
        # Check if the method exists (it should NOT exist anymore if refactored)
        inspect.getsource(MonetaryTransactionHandler._apply_asset_liquidation_effects)
        logger.warning("MonetaryTransactionHandler still has _apply_asset_liquidation_effects (Duplication present).")
    except AttributeError:
        logger.info("MonetaryTransactionHandler._apply_asset_liquidation_effects is gone (Duplication removed).")

    # Check handle method to see if it uses AssetTransferHandler
    handle_source = inspect.getsource(MonetaryTransactionHandler.handle)
    if "self.asset_handler._apply_asset_effects" in handle_source:
        logger.info("MonetaryTransactionHandler delegates to AssetTransferHandler (Good).")
    else:
        logger.error("FAILURE: MonetaryTransactionHandler does not seem to delegate to AssetTransferHandler.")

if __name__ == "__main__":
    audit_sales_tax_atomicity()
    audit_inheritance_leaks()
