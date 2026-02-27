import time
print("Starting import check (Post-Fix)...")
start = time.time()

print("Importing DeathSystem...")
from simulation.systems.lifecycle.death_system import DeathSystem
print(f"DeathSystem imported in {time.time() - start:.4f}s")
