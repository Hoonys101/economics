import time
print("Starting import check...")
start = time.time()

print("Importing Firm...")
from simulation.firms import Firm
print(f"Firm imported in {time.time() - start:.4f}s")

print("Importing Household...")
from simulation.core_agents import Household
print(f"Household imported in {time.time() - start:.4f}s")

print("Importing DeathSystem...")
from simulation.systems.lifecycle.death_system import DeathSystem
print(f"DeathSystem imported in {time.time() - start:.4f}s")
