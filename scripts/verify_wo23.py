import logging
import sys
from pathlib import Path
import os
import random
from typing import List

# Ensure module path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import run_simulation
from simulation.db.repository import SimulationRepository
from modules.analytics.loader import DataLoader
import config

# Setup Logging
from utils.logging_manager import setup_logging

setup_logging()
logger = logging.getLogger("VERIFY_WO23")


def run_test_plan_b():
    """
    Test Plan B: Innovation & Differentiation (WO-023)
    1. Visionary Logic: Force mutation and check if 'consumer_goods' sector is chosen.
    2. Maslow Constraint: Check if households with low food buy consumer goods (Should act as barrier).
    """
    logger.info("Starting Test Plan B: WO-023 Verification")

    # 1. Configure for High Mutability & Specific Environment
    # Function to tweak engine.py randomness?
    # Hard to force random.random() < 0.05 from here without mocking.
    # Instead, we rely on running enough spawns or patching.
    # PRO-TIP: We can monkey-patch random.random to return 0.0 once to force Visionary?
    # Or just increase probability via config if we made it a config param?
    # I didn't make MUTATION_RATE a config param in engine.py (hardcoded 0.05).
    # So I will Monkey Patch engine.random.random for the check.

    # 2. Run Simulation
    # Run for 50 ticks is enough to spawn firms?
    # Genesis spawns initial firms. Does spawn_firm run at Genesis?
    # No, genesis uses main.py loop calling Firm().
    # spawn_firm is for Entrepreneurship (ticks).
    # So we need to wait for entrepreneurship.
    # To speed up, we can set STARTUP_COST low.

    overrides = {
        "STARTUP_COST": 1000.0,  # Cheap to spawn
        "SIMULATION_TICKS": 100,
        "TARGET_FOOD_BUFFER_QUANTITY": 5.0,
        "VISIONARY_MUTATION_RATE": 1.0,  # Force Visionary Spawn
        "INITIAL_HOUSEHOLD_ASSETS_MEAN": 5000.0,  # WO-023: Verify Logic - Ensure rich enough to spawn
    }

    for k, v in overrides.items():
        setattr(config, k, v)

    output_file = "wo23_test_results.csv"

    # Run simulation
    run_simulation(output_filename=output_file)

    # 3. Analyze Results
    repo = SimulationRepository()
    # run_id = repo._get_latest_run_id()
    repo.cursor.execute("SELECT MAX(run_id) FROM simulation_runs")
    run_id = repo.cursor.fetchone()[0]

    # 3.1 Verify Visionary / Consumer Goods Production
    # Check if any firm produced 'consumer_goods' or has sector 'GOODS'
    # load firm data?
    # We can check economic_indicators 'total_capital_income' (irrelevant)
    # Check 'market_history' for 'consumer_goods'.

    mh_data = repo.get_market_history(
        market_id="goods_market", start_tick=0, end_tick=100, item_id="consumer_goods"
    )

    has_consumer_goods = False
    if mh_data:
        logger.info(f"Consumer Goods Market Activity detected: {len(mh_data)} records.")
        has_consumer_goods = True
    else:
        # Check active firms directly via accessing the simulation instance if possible?
        # run_simulation returns nothing.
        # We can check DB for 'consumer_goods' transactions.
        txs = repo.get_transactions(
            start_tick=0, end_tick=100, market_id="goods_market"
        )
        cg_txs = [t for t in txs if t.item_id == "consumer_goods"]
        if cg_txs:
            logger.info(f"Found {len(cg_txs)} transactions for consumer_goods.")
            has_consumer_goods = True

    if has_consumer_goods:
        logger.info("SUCCESS: Visionary Firms created and producing Consumer Goods.")
    else:
        logger.warning(
            "WARNING: No Consumer Goods activity found. Visionary spawn might have failed or taken too long."
        )

    # 3.2 Verify Maslow Constraint
    # We need to find a transaction for consumer_goods where buyer had low food.
    # But we don't save buyer's inventory snapshot at exact transaction time in DB easily.
    # However, we can check logs if we enable debug logging for MASLOW?
    # I didn't add logging for Maslow rejection in my edit (just 'continue').
    # I should have attached a log.
    # But I can check the transactions we HAVE.
    # Retrospectively check buyer's state?
    # If a buyer bought consumer_goods, they MUST have had > 5.0 food.
    # Let's check AgentState for that tick? AgentState is saved daily.
    # Crude check: For every buyer of consumer_goods, check their food inventory in AgentState at that tick.
    # If inventory < 5.0, it's a suspicious pass (or they bought food same tick).

    if cg_txs:
        violations = 0
        for tx in cg_txs:
            buyer_id = tx.buyer_id
            tick = tx.tick
            # Get agent state
            states = repo.get_agent_states(
                agent_id=buyer_id, start_tick=tick, end_tick=tick
            )
            if states:
                food = states[0].inventory.get("basic_food", 0.0)
                # Note: This is End-of-Tick state. If they consumed food after buying, it might seem low.
                # But consumption happens BEFORE purchase? No, Decisions -> Actions.
                # Food Consumption happens in 'update_needs' which is BEFORE decisions.
                # So the inventory at End-of-Tick should be (Start - Consumed + Bought).
                # If they bought consumer goods, they verified they had > 5.0 at decision time.
                # If they didn't buy food, end inventory should be > 5.0 (minus consumption?).
                # Consumption is small (approx 1.0).
                # So if end state is < 4.0, it's suspicious.

                if food < 3.0:  # Conservative threshold
                    logger.warning(
                        f"Potential Maslow Violation: Agent {buyer_id} bought goods at tick {tick} but ended with {food:.2f} food."
                    )
                    violations += 1

        if violations == 0:
            logger.info("SUCCESS: No obvious Maslow Constraint violations found.")
        else:
            logger.warning(f"WARNING: {violations} potential Maslow violations.")

    repo.close()


if __name__ == "__main__":
    run_test_plan_b()
