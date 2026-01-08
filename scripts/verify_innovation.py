
import logging
import sys
import os
import random
import matplotlib.pyplot as plt
from typing import List, Dict

# Ensure simulation module is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import create_simulation
from simulation.ai.enums import Personality
from simulation.firms import Firm

def run_verification():
    """
    Phase 16-B Verification: The Innovation War.
    Compares two firms:
    1. Conservative Firm (CASH_COW): Low R&D, High Dividends.
    2. Visionary Firm (GROWTH_HACKER): High R&D, Low Dividends.

    Expectation: Visionary Firm should achieve higher Quality and Productivity.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("VERIFY_INNOVATION")

    # Override Configuration
    overrides = {
        "NUM_FIRMS": 0,
        "NUM_HOUSEHOLDS": 50,
        "MAX_TICKS": 200,
        "GOVERNMENT_STIMULUS_ENABLED": True,
    }

    sim = create_simulation(overrides)

    def force_conservative_vector(*args, **kwargs):
        from simulation.schemas import FirmActionVector
        return FirmActionVector(
            rd_aggressiveness=0.0,
            dividend_aggressiveness=0.8,
            capital_aggressiveness=0.1
        )

    def force_visionary_vector(*args, **kwargs):
        from simulation.schemas import FirmActionVector
        return FirmActionVector(
            rd_aggressiveness=1.0, # MAX R&D
            dividend_aggressiveness=0.0,
            capital_aggressiveness=0.8
        )

    # Manually instantiate Engines to avoid sharing/pickling issues
    # We will just construct them fresh.
    from simulation.ai.firm_ai import FirmAI
    from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
    from simulation.ai_model import AIEngineRegistry

    # Conservative Engine
    # Note: get_engine needs to return the *wrapped* engine.
    # But we can just create the AI wrapper manually if we don't care about persistence for this test.

    # Simpler: Modify the AI Engine associated with the firm IN PLACE, assuming it's unique if we ask for different key.
    # But keys are shared.

    # Let's create fresh instances
    ai_engine_c = FirmAI(agent_id="1001", ai_decision_engine=None)
    decision_engine_c = AIDrivenFirmDecisionEngine(ai_engine_c, sim.config_module, logger)
    decision_engine_c.ai_engine.decide_action_vector = force_conservative_vector # Mock

    firm_c = Firm(
        id=1001,
        initial_capital=50000,
        initial_liquidity_need=100,
        specialization="food",
        productivity_factor=1.0,
        decision_engine=decision_engine_c,
        value_orientation="profit",
        config_module=sim.config_module,
        personality=Personality.CASH_COW
    )

    # Visionary Engine
    ai_engine_v = FirmAI(agent_id="1002", ai_decision_engine=None)
    decision_engine_v = AIDrivenFirmDecisionEngine(ai_engine_v, sim.config_module, logger)
    decision_engine_v.ai_engine.decide_action_vector = force_visionary_vector # Mock

    firm_v = Firm(
        id=1002,
        initial_capital=50000,
        initial_liquidity_need=100,
        specialization="food",
        productivity_factor=1.0,
        decision_engine=decision_engine_v,
        value_orientation="growth",
        config_module=sim.config_module,
        personality=Personality.GROWTH_HACKER
    )

    # Inject into simulation
    sim.agents[firm_c.id] = firm_c
    sim.firms.append(firm_c)
    sim.agents[firm_v.id] = firm_v
    sim.firms.append(firm_v)

    # Employees
    for i in range(5):
        h = sim.households[i]
        firm_c.employees.append(h)
        h.employer_id = firm_c.id
        h.is_employed = True
        firm_c.employee_wages[h.id] = 15.0

    for i in range(5, 10):
        h = sim.households[i]
        firm_v.employees.append(h)
        h.employer_id = firm_v.id
        h.is_employed = True
        firm_v.employee_wages[h.id] = 15.0

    # Data Collection
    history = {
        "tick": [],
        "c_quality": [], "v_quality": [],
        "c_prod": [], "v_prod": [],
        "c_assets": [], "v_assets": []
    }

    print("Starting Innovation War Verification...")
    for tick in range(100):
        sim.run_tick()

        history["tick"].append(tick)
        history["c_quality"].append(firm_c.base_quality)
        history["v_quality"].append(firm_v.base_quality)
        history["c_prod"].append(firm_c.productivity_factor)
        history["v_prod"].append(firm_v.productivity_factor)
        history["c_assets"].append(firm_c.assets)
        history["v_assets"].append(firm_v.assets)

        if tick % 10 == 0:
            print(f"Tick {tick}: C_Qual={firm_c.base_quality:.2f} V_Qual={firm_v.base_quality:.2f}")

    # Analysis
    final_v_qual = history["v_quality"][-1]
    final_c_qual = history["c_quality"][-1]

    print(f"Final Results (Tick 100):")
    print(f"Conservative: Quality={final_c_qual:.3f}, Prod={history['c_prod'][-1]:.3f}")
    print(f"Visionary:    Quality={final_v_qual:.3f}, Prod={history['v_prod'][-1]:.3f}")

    if final_v_qual > final_c_qual:
        print("SUCCESS: Visionary firm achieved higher quality.")
    else:
        print("FAILURE: Visionary firm did not outperform.")

    # Plotting
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(history["tick"], history["c_quality"], label="Conservative (Cash Cow)", linestyle="--")
        plt.plot(history["tick"], history["v_quality"], label="Visionary (Growth Hacker)", linewidth=2)
        plt.title("Innovation War: Quality Trajectory")
        plt.xlabel("Tick")
        plt.ylabel("Base Product Quality")
        plt.legend()
        plt.savefig("reports/innovation_war_result.png")
        print("Plot saved to reports/innovation_war_result.png")
    except Exception as e:
        print(f"Plotting failed: {e}")

if __name__ == "__main__":
    run_verification()
