import sys
import os
import logging
from unittest.mock import MagicMock
from typing import List, Tuple

# Add project root to path
sys.path.append(os.getcwd())

from simulation.systems.inheritance_manager import InheritanceManager
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY
from modules.system.constants import ID_SYSTEM

# Mock Objects to simplify dependency tree
class MockHousehold:
    def __init__(self, id, cash=0.0):
        self.id = id
        self._econ_state = MagicMock()
        self._econ_state.assets = {DEFAULT_CURRENCY: cash}
        self._econ_state.portfolio.holdings = {}
        self._bio_state = MagicMock()
        self._bio_state.children_ids = []
        self._bio_state.is_active = True

    @property
    def assets(self):
        return self._econ_state.assets

class MockGovernment:
    def __init__(self, id):
        self.id = id

class MockSimulationState:
    def __init__(self, tp):
        self.time = 100
        self.transaction_processor = tp
        self.stock_market = None # Simplified
        self.real_estate_units = []
        self.agents = MagicMock()
        self.agents.get.return_value = None

def audit_inheritance_leaks():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("AuditInheritance")
    logger.info("Starting Audit: Inheritance Leaks")

    errors = []

    # --- Scenario 1: Distribution Failure (Escheatment Fallback Check) ---
    logger.info("\n--- Scenario 1: Distribution Failure (Testing Fallback) ---")

    # Setup
    deceased = MockHousehold(1, cash=1000.0) # 1000 Cash
    government = MockGovernment(99)

    # Mock TransactionProcessor
    tp = MagicMock()
    sim_state = MockSimulationState(tp)

    # Configure TP to FAIL the main distribution
    def execute_side_effect(simulation, txs):
        if not txs: return []
        tx = txs[0]
        # Simulate failure for "escheatment" (initial attempt) or "inheritance_distribution"
        if tx.transaction_type == "escheatment" and tx.item_id == "escheatment":
            # Let's say we have no heirs, so it tries escheatment first.
            # We want to simulate that THIS fails (maybe network error, or logic error).
            # The manager should catch this failure and try a fallback or log it.
            # But wait, the manager currently just tries once.
            # Let's simulate failure.
            return [MagicMock(success=False)]

        return [MagicMock(success=True)]

    tp.execute.side_effect = execute_side_effect

    # Initialize Manager
    config = MagicMock()
    # Ensure config values are not Mocks
    type(config).INHERITANCE_TAX_RATE = MagicMock(return_value=0.4) # Mock property/attr
    # Better yet, just set attributes directly
    config.INHERITANCE_TAX_RATE = 0.4
    config.INHERITANCE_DEDUCTION = 10000.0

    manager = InheritanceManager(config_module=config)

    # Execute Process Death (No heirs -> Escheatment)
    # The current code tries "escheatment" transaction.
    # Our mock will make it fail.
    transactions = manager.process_death(deceased, government, sim_state)

    # Check if a FALLBACK transaction was attempted.
    # If the first failed, did it retry?
    # In current code, it does NOT retry. So we expect 1 call, failure, and leak.

    # Verify leak:
    # We can't easily check 'leak' on the mock object state because the manager relies on TP to move funds.
    # If TP failed, funds are still on deceased (conceptually).
    # We check if TP was called with a *fallback* transaction.

    # Count calls to execute with transaction_type="escheatment"
    escheat_calls = [
        call[0][1][0] for call in tp.execute.call_args_list
        if call[0][1][0].transaction_type == "escheatment"
    ]

    logger.info(f"Escheatment attempts: {len(escheat_calls)}")

    if len(escheat_calls) < 2:
        # If we only see 1 call (which we forced to fail), and no second attempt (fallback),
        # then the fix is missing.
        msg = "FAILURE: No fallback escheatment attempted after initial failure."
        logger.error(msg)
        errors.append(msg)
    else:
        logger.info("SUCCESS: Fallback escheatment detected.")


    # --- Scenario 2: Final Sweep Check ---
    logger.info("\n--- Scenario 2: Final Sweep (Leftover Balance) ---")

    # Reset
    deceased_2 = MockHousehold(2, cash=1000.05) # 1000.05
    tp_2 = MagicMock()
    sim_state_2 = MockSimulationState(tp_2)

    # Configure TP to SUCCEED for tax (say 400)
    # And SUCCEED for distribution (say 600)
    # Leaving 0.05 on the table due to some calculation error (simulated).

    def execute_success(simulation, txs):
        return [MagicMock(success=True)]
    tp_2.execute.side_effect = execute_success

    # Ensure config values are set for manager_2
    config.INHERITANCE_TAX_RATE = 0.4
    config.INHERITANCE_DEDUCTION = 10000.0

    manager_2 = InheritanceManager(config_module=config)

    # We need to simulate the 'cash' tracking variable in the manager having a leftover.
    # The manager calculates `cash` from assets.
    # `tax` = 40% of 1000 = 400.
    # `distribute` = 600.
    # If deceased had 1000.05, and code only saw 1000 (maybe rounding error), 0.05 is left.
    # But `process_death` reads `cash = round(cash, 2)`.
    # Let's say `assets` has 1000.004 (float error) -> rounds to 1000.00.
    # This might not capture the leak if rounding is perfect.

    # Let's force a leak by saying the distribution transaction only moved PART of the money.
    # But `InheritanceManager` constructs the transaction with `quantity=1.0, price=cash`.
    # It assumes `cash` covers everything.

    # The "Final Sweep" fix implies checking `deceased.get_balance()` at the very end.
    # If > 0, create "final_sweep".
    # In my mock, `deceased_2` has 1000.05.
    # The manager reads it.
    # Let's say the manager logic calculates distribution for 1000.00 (maybe config deduction error).
    # Then 0.05 is left.

    # Mocking behavior:
    # 1. Manager reads cash.
    # 2. Manager pays tax.
    # 3. Manager distributes.
    # 4. (New Fix) Manager checks balance again.

    # To test this, I need `deceased.assets` (or balance) to still be > 0 after the logic runs.
    # Since `TransactionProcessor` is mocked, it DOES NOT update `deceased` balance automatically.
    # So `deceased` balance remains 1000.05 throughout.
    # The manager *should* assume it moved the money if TP returns success.
    # UNLESS the fix explicitly re-checks the wallet (which is what we want).

    # If the manager logic relies on its internal `cash` variable, it thinks it's done.
    # If it re-checks `deceased._econ_state.assets` (or wallet), it sees 1000.05.
    # Since TP is mocked and doesn't reduce balance, the manager sees 1000.05.
    # It should trigger "final_sweep".

    transactions_2 = manager_2.process_death(deceased_2, government, sim_state_2)

    # Check for "final_sweep" transaction
    final_sweep_calls = [
        call[0][1][0] for call in tp_2.execute.call_args_list
        if call[0][1][0].transaction_type == "final_sweep"
    ]

    logger.info(f"Final Sweep attempts: {len(final_sweep_calls)}")

    if len(final_sweep_calls) == 0:
        msg = "FAILURE: No final sweep detected for leftover balance."
        logger.error(msg)
        errors.append(msg)
    else:
        logger.info("SUCCESS: Final Sweep transaction detected.")

    if errors:
        logger.error(f"Audit Failed with {len(errors)} errors.")
        sys.exit(1)

    logger.info("Audit Completed Successfully: Inheritance Integrity Verified.")

if __name__ == "__main__":
    audit_inheritance_leaks()
