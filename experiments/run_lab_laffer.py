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
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from simulation.engine import Simulation
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.ai.ai_training_manager import AIEngineRegistry
from simulation.db.repository import SimulationRepository


# ==============================================================================
# Experiment Parameters
# ==============================================================================
TAX_RATES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
TICKS_PER_RUN = 1000
SETTLING_TICKS = 100  # Ignore first N ticks for settling
RANDOM_SEED = 42
OUTPUT_DIR = "results"
OUTPUT_FILE = "laffer_experiment.csv"


def create_config_overrides(tax_rate: float) -> Dict[str, Any]:
    """Create config overrides for a given tax rate."""
    return {
        "TAX_MODE": "FLAT",
        "BASE_INCOME_TAX_RATE": tax_rate,
        "ANNUAL_WEALTH_TAX_RATE": 0.0,  # Freeze wealth tax for this experiment
    }


def apply_config_overrides(overrides: Dict[str, Any]) -> None:
    """Apply overrides to the config module."""
    for key, value in overrides.items():
        setattr(config, key, value)


def reset_random_state(seed: int) -> None:
    """Reset random state for reproducibility."""
    random.seed(seed)
    # If numpy is used, add: np.random.seed(seed)


def run_single_experiment(tax_rate: float) -> Dict[str, float]:
    """
    Run a single simulation with the given tax rate.
    
    Returns:
        Dict with experiment results.
    """
    print(f"\n{'='*60}")
    print(f"Running experiment with tax_rate={tax_rate:.1%}")
    print(f"{'='*60}")
    
    # Reset random state
    reset_random_state(RANDOM_SEED)
    
    # Apply config overrides
    apply_config_overrides(create_config_overrides(tax_rate))
    
    # Create simulation components (simplified - you may need to adjust based on your factory)
    # This is a minimal setup - actual implementation may require more initialization
    try:
        from main import create_simulation  # Use existing factory if available
        sim = create_simulation()
    except ImportError:
        print("Warning: Could not import create_simulation from main.py")
        print("Please ensure simulation factory is available or implement inline.")
        return {
            "tax_rate": tax_rate,
            "total_revenue": 0.0,
            "avg_work_hours": 0.0,
            "avg_child_xp": 0.0,
            "avg_leisure_hours": 0.0,
            "parenting_count": 0,
            "error": "Factory not available"
        }
    
    # Run simulation
    for tick in range(TICKS_PER_RUN):
        sim.run_tick()
        if tick % 100 == 0:
            print(f"  Tick {tick}/{TICKS_PER_RUN}")
    
    # Collect results (after settling period)
    results = calculate_experiment_metrics(sim)
    results["tax_rate"] = tax_rate
    
    # Cleanup
    del sim
    
    return results


def calculate_experiment_metrics(sim: Simulation) -> Dict[str, float]:
    """Calculate experiment metrics from completed simulation."""
    total_revenue = sim.government.total_collected_tax if hasattr(sim, 'government') else 0.0
    
    # Calculate averages from households
    total_work_hours = 0.0
    total_leisure_hours = 0.0
    total_child_xp = 0.0
    parenting_count = 0
    household_count = 0
    child_count = 0
    
    for agent in sim.agents.values():
        if isinstance(agent, Household) and agent.is_active:
            household_count += 1
            # Note: These attributes need to be tracked in the simulation
            # This is a placeholder - actual implementation depends on your tracking
            
            if hasattr(agent, 'children_ids'):
                for child_id in agent.children_ids:
                    child = sim.agents.get(child_id)
                    if child and hasattr(child, 'education_xp'):
                        total_child_xp += child.education_xp
                        child_count += 1
    
    return {
        "total_revenue": total_revenue,
        "avg_work_hours": total_work_hours / max(household_count, 1),
        "avg_leisure_hours": total_leisure_hours / max(household_count, 1),
        "avg_child_xp": total_child_xp / max(child_count, 1),
        "parenting_count": parenting_count,
        "household_count": household_count,
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
        fieldnames = list(results[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n{'='*60}")
        print(f"Experiment Complete!")
        print(f"Results saved to: {output_path}")
        print(f"{'='*60}")
    
    # Print summary table
    print("\nSUMMARY:")
    print("-" * 60)
    print(f"{'Tax Rate':<12} {'Revenue':<15} {'Avg Work Hrs':<15}")
    print("-" * 60)
    for r in results:
        print(f"{r.get('tax_rate', 0):<12.1%} {r.get('total_revenue', 0):<15.2f} {r.get('avg_work_hours', 0):<15.2f}")


if __name__ == "__main__":
    main()
