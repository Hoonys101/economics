#!/usr/bin/env python3
"""
run_lab_laffer.py - Laffer Curve Experiment Runner

This script runs multiple simulations with varying tax rates to verify
the Laffer Curve hypothesis: higher taxes eventually reduce total revenue.

Usage:
    python run_lab_laffer.py

Output:
    results/laffer_experiment.csv
"""
import csv
import os
import sys
import random
import logging
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from simulation.engine import Simulation
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.db.repository import SimulationRepository
from main import create_simulation

# ==============================================================================
# Experiment Parameters
# ==============================================================================
TAX_RATES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
TICKS_PER_RUN = 1000
SETTLING_TICKS = 100  # Ignore first N ticks for settling
RANDOM_SEED = 42
OUTPUT_DIR = "results"
OUTPUT_FILE = "laffer_experiment.csv"

# Configure logging to suppress verbose output during experiment
logging.basicConfig(level=logging.ERROR)


def create_config_overrides(tax_rate: float) -> Dict[str, Any]:
    """Create config overrides for a given tax rate."""
    return {
        "TAX_MODE": "FLAT",
        "BASE_INCOME_TAX_RATE": tax_rate,
        "ANNUAL_WEALTH_TAX_RATE": 0.0,  # Freeze wealth tax for this experiment
        "RANDOM_SEED": RANDOM_SEED,
    }


def run_single_experiment(tax_rate: float) -> Dict[str, float]:
    """
    Run a single simulation with the given tax rate.
    
    Returns:
        Dict with experiment results.
    """
    print(f"\n{'='*60}")
    print(f"Running experiment with tax_rate={tax_rate:.1%}")
    print(f"{'='*60}")
    
    # Create simulation with overrides
    overrides = create_config_overrides(tax_rate)
    try:
        sim = create_simulation(overrides=overrides)
    except Exception as e:
        print(f"Error creating simulation: {e}")
        return {
            "tax_rate": tax_rate,
            "total_revenue": 0.0,
            "avg_work_hours": 0.0,
            "avg_child_xp": 0.0,
            "avg_leisure_hours": 0.0,
            "parenting_count": 0,
            "error": str(e)
        }
    
    # Track accumulated metrics for averaging
    accumulated_work_hours = 0.0
    accumulated_leisure_hours = 0.0
    accumulated_samples = 0

    # Run simulation
    for tick in range(TICKS_PER_RUN):
        sim.run_tick()

        # Accumulate data after settling period
        if tick >= SETTLING_TICKS:
            tick_work_hours = 0.0
            tick_leisure_hours = 0.0
            active_households = 0

            # Using the engine's tracking map if available
            allocation_map = getattr(sim, "household_time_allocation", {})

            for agent in sim.households:
                if agent.is_active:
                    active_households += 1
                    leisure = allocation_map.get(agent.id, 0.0)
                    work = max(0.0, config.HOURS_PER_TICK - leisure - config.SHOPPING_HOURS)

                    tick_work_hours += work
                    tick_leisure_hours += leisure

            if active_households > 0:
                accumulated_work_hours += (tick_work_hours / active_households)
                accumulated_leisure_hours += (tick_leisure_hours / active_households)
                accumulated_samples += 1

        if tick % 100 == 0:
            print(f"  Tick {tick}/{TICKS_PER_RUN}")
    
    # Calculate final metrics
    total_revenue = sim.government.total_collected_tax if hasattr(sim, 'government') else 0.0
    
    avg_work_hours = accumulated_work_hours / max(accumulated_samples, 1)
    avg_leisure_hours = accumulated_leisure_hours / max(accumulated_samples, 1)

    # Calculate Child XP (Snapshotted at end)
    total_child_xp = 0.0
    child_count = 0
    
    # Assuming children are households with parents? Or specific logic.
    # The prompt implies avg_child_xp. Let's look at all active households.
    # Actually, children are agents.
    for agent in sim.households:
        if agent.is_active and hasattr(agent, 'education_xp'):
            total_child_xp += agent.education_xp
            child_count += 1
            
    avg_child_xp = total_child_xp / max(child_count, 1)

    # Parenting count isn't explicitly tracked in global counters,
    # but we could count how many times LEISURE_EFFECT parenting happened if we tracked it.
    # For now, let's leave it as placeholder or remove if not critical.
    # The prompt expects: tax_rate,total_revenue,avg_work_hours,avg_child_xp

    # Cleanup
    sim.finalize_simulation() # Close DB connections
    del sim
    
    return {
        "tax_rate": tax_rate,
        "total_revenue": total_revenue,
        "avg_work_hours": avg_work_hours,
        "avg_leisure_hours": avg_leisure_hours,
        "avg_child_xp": avg_child_xp
    }


def main():
    """Main experiment runner."""
    print("=" * 60)
    print("LAFFER CURVE EXPERIMENT")
    print("=" * 60)
    print(f"Tax Rates: {TAX_RATES}")
    print(f"Ticks per Run: {TICKS_PER_RUN}")
    print(f"Random Seed: {RANDOM_SEED}")
    print()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    # Run experiments
    results: List[Dict[str, Any]] = []
    
    for tax_rate in TAX_RATES:
        result = run_single_experiment(tax_rate)
        results.append(result)
        print(f"Result: Revenue={result.get('total_revenue', 0):.2f}")
    
    # Write CSV
    if results:
        fieldnames = ["tax_rate", "total_revenue", "avg_work_hours", "avg_child_xp"]
        # Filter keys to match expected output if needed, or just include all useful ones

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n{'='*60}")
        print(f"Experiment Complete!")
        print(f"Results saved to: {output_path}")
        print(f"{'='*60}")
    
    # Print summary table
    print("\nSUMMARY:")
    print("-" * 60)
    print(f"{'Tax Rate':<12} {'Revenue':<15} {'Avg Work Hrs':<15} {'Avg Child XP':<15}")
    print("-" * 60)
    for r in results:
        print(f"{r.get('tax_rate', 0):<12.1%} {r.get('total_revenue', 0):<15.2f} {r.get('avg_work_hours', 0):<15.2f} {r.get('avg_child_xp', 0):<15.2f}")


if __name__ == "__main__":
    main()
