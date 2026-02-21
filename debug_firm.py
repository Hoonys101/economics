
from simulation.firms import Firm
print(f"Firm MRO: {Firm.mro()}")
print(f"Has get_balance: {hasattr(Firm, 'get_balance')}")
if hasattr(Firm, 'get_balance'):
    print(f"get_balance source: {Firm.get_balance}")
