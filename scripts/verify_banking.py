import logging
import argparse
import sys
import os
import matplotlib.pyplot as plt
from typing import Dict, Any

# Ensure the project root is in the path
sys.path.append(os.getcwd())

from main import create_simulation
from config import (
    NUM_HOUSEHOLDS,
    NUM_FIRMS,
    INITIAL_HOUSEHOLD_ASSETS_MEAN,
    INITIAL_FIRM_CAPITAL_MEAN,
    GOLD_STANDARD_MODE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_banking")

def verify_banking_system(num_ticks: int = 200, plot_results: bool = False):
    """
    Runs a simulation to verify the fractional reserve banking system.
    Focuses on Money Multiplier (M2 > M0) and Solvency.
    """
    logger.info("Initializing Banking Verification Simulation...")

    # Override config for banking test
    # We want to encourage lending, so we might give households some liquidity but not too much,
    # and ensure firms need capital.
    overrides = {
        "NUM_HOUSEHOLDS": 50,
        "NUM_FIRMS": 10,
        "INITIAL_HOUSEHOLD_ASSETS_MEAN": 2000.0, # Enough to deposit
        "INITIAL_FIRM_CAPITAL_MEAN": 1000.0,     # Low capital -> Demand for loans
        "GOLD_STANDARD_MODE": False,             # Fractional Reserve Banking
        "GOVERNMENT_STIMULUS_ENABLED": False,    # Isolate banking effects
        "FIRM_MAINTENANCE_FEE": 10.0,            # Lower fee to reduce bankruptcy risk during test
        "SALES_TAX_RATE": 0.0,                   # Disable Taxes to prevent money destruction (Government Sink)
        "INCOME_TAX_RATE": 0.0,
        "CORPORATE_TAX_RATE": 0.0,
        "INITIAL_BANK_ASSETS": 50000.0,          # Reduced reserves to make Multiplier visible
        "INITIAL_FIRM_CAPITAL_MEAN": 100.0,      # Starve firms to force borrowing
        "INFRASTRUCTURE_INVESTMENT_COST": 100.0, # Lower threshold for Gov spending
        "INITIAL_GOVERNMENT_ASSETS": 10000.0,    # Pump priming to prevent M0 collapse
    }

    simulation = create_simulation(overrides)
    # Inject initial government assets manually as config might not handle it in init
    simulation.government.assets = 10000.0

    history_m0 = []
    history_m2 = []
    history_multiplier = []
    history_bank_assets = []
    history_loans = []
    history_deposits = []

    logger.info(f"Running simulation for {num_ticks} ticks...")

    for tick in range(num_ticks):
        simulation.run_tick()

        # --- Metrics Calculation ---
        bank = simulation.bank

        # M0 (Base Money) = Currency in Circulation + Bank Reserves
        # Currency in Circulation = Agent Assets (Cash held by Households + Firms)
        # Bank Reserves = Bank Assets (Cash held by Bank)

        currency_in_circulation = sum(agent.assets for agent in simulation.agents.values() if agent.id != bank.id and agent.id != simulation.government.id)
        bank_reserves = bank.assets
        m0 = currency_in_circulation + bank_reserves

        # M2 (Money Supply) = Currency in Circulation + Deposits
        # Deposits = Sum of all deposit accounts in the bank
        total_deposits = sum(d.amount for d in bank.deposits.values())
        m2 = currency_in_circulation + total_deposits

        money_multiplier = m2 / m0 if m0 > 0 else 0

        total_loans = sum(l.remaining_balance for l in bank.loans.values())

        # Store history
        history_m0.append(m0)
        history_m2.append(m2)
        history_multiplier.append(money_multiplier)
        history_bank_assets.append(bank.assets)
        history_loans.append(total_loans)
        history_deposits.append(total_deposits)

        if tick % 10 == 0:
            logger.info(f"Tick {tick}: M0={m0:.2f}, M2={m2:.2f}, Mult={money_multiplier:.2f}, Loans={total_loans:.2f}, Deposits={total_deposits:.2f}, BankRes={bank_reserves:.2f}")

    # --- Verification Checks ---
    logger.info("--- Verification Results ---")

    # 1. Money Multiplier Verification
    avg_multiplier = sum(history_multiplier[-50:]) / 50 if num_ticks >= 50 else sum(history_multiplier) / len(history_multiplier)
    max_multiplier = max(history_multiplier)

    logger.info(f"Average Money Multiplier (Last 50 ticks): {avg_multiplier:.2f}")
    logger.info(f"Max Money Multiplier: {max_multiplier:.2f}")

    if max_multiplier > 1.0:
        logger.info("✅ SUCCESS: Money Multiplier Effect Observed (M2 > M0).")
    else:
        logger.warning("❌ FAILURE: No Money Creation (M2 <= M0). Check Loan Issuance.")

    # 2. Solvency Check
    initial_bank_assets = history_bank_assets[0]
    final_bank_assets = history_bank_assets[-1]
    logger.info(f"Bank Assets: Start={initial_bank_assets:.2f}, End={final_bank_assets:.2f}")

    if final_bank_assets > 0:
        logger.info("✅ SUCCESS: Bank is Solvent (Positive Assets).")
    else:
        logger.error("❌ FAILURE: Bank Insolvent!")

    # 3. Profitability (Optional but good)
    if final_bank_assets > initial_bank_assets:
        logger.info("✅ SUCCESS: Bank is Profitable.")
    else:
        logger.info("⚠️ WARNING: Bank lost assets (could be due to defaults or initial burn).")

    # Plotting
    if plot_results:
        plt.figure(figsize=(12, 10))

        plt.subplot(3, 1, 1)
        plt.plot(history_m0, label='M0 (Base Money)')
        plt.plot(history_m2, label='M2 (Money Supply)')
        plt.legend()
        plt.title('Money Supply (M0 vs M2)')

        plt.subplot(3, 1, 2)
        plt.plot(history_loans, label='Total Loans')
        plt.plot(history_deposits, label='Total Deposits')
        plt.legend()
        plt.title('Bank Balance Sheet Items')

        plt.subplot(3, 1, 3)
        plt.plot(history_multiplier, label='Money Multiplier', color='green')
        plt.legend()
        plt.title('Money Multiplier (M2 / M0)')

        plt.tight_layout()
        plt.savefig('reports/banking_verification.png')
        logger.info("Saved plot to reports/banking_verification.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Banking System Logic")
    parser.add_argument("--ticks", type=int, default=200, help="Number of ticks to run")
    parser.add_argument("--plot", action="store_true", help="Generate plots")
    args = parser.parse_args()

    os.makedirs("reports", exist_ok=True)
    verify_banking_system(num_ticks=args.ticks, plot_results=args.plot)
