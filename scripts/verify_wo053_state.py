import sys
import os
sys.path.append(os.getcwd())
from main import create_simulation

def verify_wo053():
    print("--- VERIFY WO-053 STATE ---")
    sim = create_simulation()

    # Run one orchestration to calculate initial stats
    # orchestrate_production_and_tech handles HCI calculation and Tech Update
    sim.orchestrate_production_and_tech(0)

    # Access TechnologyManager
    tech_manager = sim.world_state.technology_manager
    if not tech_manager:
        print("ERROR: TechnologyManager not found!")
        return

    print(f"Human Capital Index: {tech_manager.human_capital_index}")

    # Check a firm's productivity multiplier
    if sim.firms:
        firm = sim.firms[0]
        mult = tech_manager.get_productivity_multiplier(firm.id)
        print(f"Firm {firm.id} Productivity Multiplier: {mult}")
    else:
        print("No firms found.")

    # Check unlocked techs
    if hasattr(tech_manager, 'unlocked_techs'):
        print(f"Unlocked Technologies: {tech_manager.unlocked_techs}")
    else:
        print(f"TechnologyManager attributes: {dir(tech_manager)}")

if __name__ == "__main__":
    verify_wo053()
