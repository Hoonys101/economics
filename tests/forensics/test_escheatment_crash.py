import pytest
from unittest.mock import MagicMock
from simulation.systems.handlers.escheatment_handler import EscheatmentHandler
from simulation.models import Transaction

def test_escheatment_handler_null_metadata_crash():
    """
    Regression Test for TD-FORENSIC-001.
    Reproduces the crash by passing a Transaction with metadata=None.
    """
    # 1. Setup
    handler = EscheatmentHandler()
    
    # Create a malformed transaction (metadata is explicitly None)
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="test", quantity=1, price=1, 
        total_pennies=100, market_id="m", transaction_type="escheatment", time=1
    )
    tx.metadata = None # Simulate the corruption
    
    context = MagicMock()
    context.settlement_system.get_balance.return_value = 1000
    
    # 2. Execute & Assert
    # Expectation: Should NOT raise AttributeError. Should return True (success) or handle gracefully.
    try:
        success = handler.handle(tx, buyer=MagicMock(id=1), seller=MagicMock(id=2), context=context)
        # If it returns success or even False, it's fine as long as it doesn't CRASH.
        # But per logic, if balance > 0 and gov exists, it should succeed.
        assert success is not None
    except AttributeError as e:
        pytest.fail(f"Regression Failed: EscheatmentHandler crashed on null metadata: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error in EscheatmentHandler: {e}")
