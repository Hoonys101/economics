import os
import sys
from pathlib import Path
import pandas as pd
import logging

# Add parent directory to path to import simulation modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai.api import Personality
from simulation.ai_model import AIEngineRegistry
from simulation.db.repository import SimulationRepository
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
import config

from simulation.ai.household_ai import HouseholdAI
from simulation.ai.firm_ai import FirmAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine

# Setup logging
logging.basicConfig(level=logging.WARNING)

def run_phase4_verification(ticks=100, output_file="phase4_verification.csv"):
    print(f"--- Starting Phase 4 Verification Run ({ticks} ticks) ---")
    
    # Initialize components
    # config module is used directly
    repo = SimulationRepository()
    
    state_builder = StateBuilder()
    action_proposal_engine = ActionProposalEngine(config_module=config)
    ai_registry = AIEngineRegistry(
        action_proposal_engine=action_proposal_engine, state_builder=state_builder
    )
    
    # Format goods_data
    goods_data_list = [
        {"id": k, **v} for k, v in config.GOODS.items()
    ]
    
    # Create Dummy Agents
    households = []
    for i in range(20):
        vo = "wealth_and_needs"
        
        # Manually create decision engine
        ai_engine_shared = ai_registry.get_engine(vo)
        household_ai = HouseholdAI(
            agent_id=i,
            ai_decision_engine=ai_engine_shared,
            gamma=0.9, epsilon=0.1, base_alpha=0.1, learning_focus=0.5
        )
        decision_engine = AIDrivenHouseholdDecisionEngine(
            ai_engine=household_ai,
            config_module=config,
            logger=logging.getLogger("dummy")
        )

        h = Household(
            id=i,
            talent=Talent(0.1, {}),
            goods_data=goods_data_list,
            initial_assets=1000.0 if i < 18 else 50.0, # Some poor agents
            initial_needs={
                "survival": 0.0,
                "asset": 10.0,
                "social": 10.0,
                "improvement": 10.0
            },
            decision_engine=decision_engine,
            value_orientation=vo,
            personality=Personality.MISER,
            config_module=config
        )
        # Set some to unemployed to trigger welfare
        h.is_employed = False
        if i >= 18:
            h.needs["survival"] = 60.0 # High need
        households.append(h)

    firms = []
    # Create 1 firm to hire
    f_id = 20
    vo_firm = "profit_max" # Or just reuse existing, Firm ignores VO usually or defaults
    # Actually Firm might share same registry or have its own. AIEngineRegistry uses VO strings.
    # Let's use "wealth_and_needs" for firm too or check if valid.
    # main.py loops over ["wealth_and_needs", "needs_and_growth", "needs_and_social_status"]
    
    ai_engine_shared = ai_registry.get_engine("wealth_and_needs")
    firm_ai = FirmAI(
        agent_id=f_id,
        ai_decision_engine=ai_engine_shared,
        gamma=0.9, epsilon=0.1, base_alpha=0.1, learning_focus=0.5
    )
    firm_decision_engine = AIDrivenFirmDecisionEngine(
        ai_engine=firm_ai,
        config_module=config,
        logger=logging.getLogger("dummy")
    )

    f = Firm(
        id=f_id,
        initial_capital=50000.0,
        initial_liquidity_need=100.0,
        specialization="basic_food",
        productivity_factor=10.0,
        decision_engine=firm_decision_engine,
        value_orientation=vo_firm,
        config_module=config
    )
    firms.append(f)
    
    # Initialize Simulation
    sim = Simulation(
        households=households,
        firms=firms,
        ai_trainer=ai_registry,
        repository=repo,
        config_module=config,
        goods_data=goods_data_list
    )

    data_rows = []

    for t in range(1, ticks + 1):
        sim.run_tick()
        
        # Collect Metrics
        gov = sim.government
        
        # Gini
        wealth_dist = sim.inequality_tracker.calculate_wealth_distribution(sim.households, sim.stock_market)
        gini = wealth_dist.get("gini_total_assets", 0.0)
        
        # Credit Jail Count
        jailed_count = sum(1 for h in sim.households if h.credit_frozen_until_tick > t)
        
        # Welfare Spending (Stimulus + Benefit)
        # Assuming run_welfare_check ran and updated Government stats
        # Note: 'welfare_spending' in current_tick_stats is reset every tick in finalize_tick
        # But we capture it from government history or just peek current tick stats before reset?
        # finalize_tick runs at end of run_tick.
        # We can read from history.
        welfare_flow = 0.0
        tax_flow = 0.0
        
        if gov.welfare_history and gov.welfare_history[-1]["tick"] == t:
            last = gov.welfare_history[-1]
            welfare_flow = last.get("welfare", 0.0) + last.get("stimulus", 0.0)
            
        if gov.tax_history and gov.tax_history[-1]["tick"] == t:
            tax_flow = gov.tax_history[-1]["total"]

        row = {
            "Tick": t,
            "Gini_Coefficient": gini,
            "Welfare_Spending": welfare_flow,
            "Tax_Revenue": tax_flow,
            "Credit_Jailed_Count": jailed_count,
            "Gov_Assets": gov.assets
        }
        data_rows.append(row)
        
        if t % 10 == 0:
            print(f"Tick {t}: Gini={gini:.4f}, Welfare={welfare_flow:.2f}, Tax={tax_flow:.2f}, Jailed={jailed_count}")

    # Export CSV
    df = pd.DataFrame(data_rows)
    df.to_csv(output_file, index=False)
    print(f"--- Verification Complete. Data saved to {output_file} ---")
    
    # Check if Welfare was paid (Logic Check)
    total_welfare = df["Welfare_Spending"].sum()
    if total_welfare > 0:
        print("✅ SUCCESS: Welfare payments detected.")
    else:
        print("⚠️ WARNING: No welfare payments detected. Check unemployment logic.")

if __name__ == "__main__":
    run_phase4_verification()
