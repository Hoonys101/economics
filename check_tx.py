from simulation.models import Transaction
import inspect

print(f"Transaction signature: {inspect.signature(Transaction)}")
try:
    tx = Transaction(1, 2, "test", 1.0, 1.0, "market", "type", 1)
    print("Created successfully without total_pennies?")
    print(tx)
except TypeError as e:
    print(f"Failed as expected: {e}")
