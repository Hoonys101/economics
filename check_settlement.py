import logging
from simulation.firms import Firm
from simulation.core_agents import Household
from simulation.systems.settlement_system import SettlementSystem
from modules.system.api import DEFAULT_CURRENCY
from unittest.mock import MagicMock

logging.basicConfig(level=logging.INFO)

# Setup
firm = MagicMock(spec=Firm)
firm.id = 101
firm.balance_pennies = 10000000
firm.get_balance.side_effect = lambda c=DEFAULT_CURRENCY: 10000000
firm._withdraw.side_effect = lambda a, c=DEFAULT_CURRENCY: setattr(firm, 'balance_pennies', firm.balance_pennies - a)
firm.withdraw.side_effect = lambda a, c=DEFAULT_CURRENCY: setattr(firm, 'balance_pennies', firm.balance_pennies - a)

hh = MagicMock(spec=Household)
hh.id = 201
hh.balance_pennies = 0
hh.get_balance.side_effect = lambda c=DEFAULT_CURRENCY: hh.balance_pennies
hh._deposit.side_effect = lambda a, c=DEFAULT_CURRENCY: setattr(hh, 'balance_pennies', hh.balance_pennies + a)
hh.deposit.side_effect = lambda a, c=DEFAULT_CURRENCY: setattr(hh, 'balance_pennies', hh.balance_pennies + a)

settlement = SettlementSystem()

# Test transfer
print(f"Initial - Firm: {firm.get_balance()}, HH: {hh.get_balance()}")
success = settlement.transfer(firm, hh, 2000, "test_transfer")
print(f"Success: {success}")
print(f"Final - Firm: {firm.get_balance()}, HH: {hh.get_balance()}")

if success and firm.get_balance() == 9998000 and hh.get_balance() == 2000:
    print("Direct transfer works!")
else:
    print("Direct transfer FAILED!")

# Test settle_atomic
firm.balance_pennies = 10000000
hh.balance_pennies = 0
print(f"Atomic Initial - Firm: {firm.get_balance()}, HH: {hh.get_balance()}")
success = settlement.settle_atomic(firm, [(hh, 2000, "labor")], 0)
print(f"Atomic Success: {success}")
print(f"Atomic Final - Firm: {firm.get_balance()}, HH: {hh.get_balance()}")
