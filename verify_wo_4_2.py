import logging
import sys
from utils.simulation_builder import create_simulation
from modules.system.api import DEFAULT_CURRENCY

# Configure logging to capture warnings/errors but avoid spamming stdout with INFO
logging.basicConfig(level=logging.WARNING, stream=sys.stdout)

def verify_wo_4_2():
    print("Starting verification for WO-4.2...")
    sim = create_simulation()

    # Run 100 ticks
    for i in range(1, 101):
        sim.run_tick()

        # Monitor M2
        money_supply = sim.world_state.calculate_total_money().get(DEFAULT_CURRENCY, 0.0)

        # Check Government money issued/destroyed
        # sim.world_state.governments is a list
        if sim.world_state.governments:
            gov = sim.world_state.governments[0]
            issued = gov.total_money_issued.get(DEFAULT_CURRENCY, 0.0)
            destroyed = gov.total_money_destroyed.get(DEFAULT_CURRENCY, 0.0)

            # Check baseline match (approximate check from logs logic)
            # The tick orchestrator logs warnings if delta > 1.0
            # We can check the delta ourselves if we want, but just printing is enough for manual verification
            # if the orchestrator logs warnings, they will appear in stdout (due to basicConfig).

            # Print status every 10 ticks
            if i % 10 == 0:
                print(f"Tick {i}: M2={money_supply:.2f}, Gov Issued={issued:.2f}, Gov Destroyed={destroyed:.2f}")
        else:
             print(f"Tick {i}: M2={money_supply:.2f} (No Government agent found)")

    print("Verification run completed.")

if __name__ == "__main__":
    verify_wo_4_2()
