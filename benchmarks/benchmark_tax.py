import time
import os
from types import SimpleNamespace
from modules.government.tax.service import TaxService
from modules.government.api import ITaxableHousehold
from modules.finance.api import IFinancialEntity
from modules.system.api import AgentID

class DummyConfig:
    ANNUAL_WEALTH_TAX_RATE = 0.05
    TICKS_PER_YEAR = 100
    WEALTH_TAX_THRESHOLD = 5000000

class DummyAgent:
    def __init__(self, net_worth):
        self.is_active = True
        self.balance_pennies = net_worth
        self.is_employed = True
        self.needs = None
        self.id = AgentID(1)
        self.name = "dummy"

# Register the class as conforming to the protocol to satisfy isinstance
ITaxableHousehold.register(DummyAgent)

def run_benchmark():
    config = DummyConfig()
    service = TaxService(config)

    # Generate 100,000 dummy agents
    agents = [DummyAgent(10000000) for _ in range(100000)]

    start_time = time.perf_counter()
    # Call collect_wealth_tax to execute calculate_wealth_tax for each agent
    service.collect_wealth_tax(agents)
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    print(f"Time taken to collect wealth tax for 100,000 agents: {elapsed:.4f} seconds")

if __name__ == "__main__":
    for i in range(5):
        run_benchmark()
