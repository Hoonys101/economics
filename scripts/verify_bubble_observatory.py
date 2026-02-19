import sys
import os
import logging
import random
from unittest.mock import MagicMock

sys.path.append(os.getcwd())

from modules.analysis.bubble_observatory import BubbleObservatory
from simulation.engine import Simulation
from simulation.models import Transaction, RealEstateUnit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

def verify_observatory():
    logger.info("--- Starting Bubble Observatory Verification ---")

    # Mock Simulation
    sim_mock = MagicMock()
    state_mock = MagicMock()
    sim_mock.world_state = state_mock
    sim_mock.config_module = MagicMock()

    # State Setup
    state_mock.time = 10
    state_mock.real_estate_units = [
        MagicMock(estimated_value=100000),
        MagicMock(estimated_value=200000)
    ]
    # Avg Price = 150000

    state_mock.calculate_total_money.return_value = 5000000.0

    # Transactions
    # 1. Housing Tx with Mortgage
    tx1 = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_1", quantity=1, price=100000,
        market_id="housing", transaction_type="housing", time=10,
        metadata={"mortgage_id": 123}
    , total_pennies=10000000)
    # 2. Cash Tx
    tx2 = Transaction(
        buyer_id=3, seller_id=4, item_id="unit_2", quantity=1, price=200000,
        market_id="housing", transaction_type="housing", time=10,
        metadata={}
    , total_pennies=20000000)

    state_mock.transactions = [tx1, tx2]

    # Bank Setup for Loan Lookup
    bank_mock = MagicMock()
    # Loan for Tx1
    loan_mock = MagicMock()
    loan_mock.principal = 80000.0 # LTV 0.8
    loan_mock.annual_interest_rate = 0.05

    # Mock Loan Dictionary
    # Observatory looks for f"loan_{mid}"
    bank_mock.loans = {"loan_123": loan_mock}

    state_mock.bank = bank_mock

    # Agent Lookup (for DTI)
    agent_mock = MagicMock()
    agent_mock.current_wage = 1000.0 # Annual 100k
    sim_mock.agents.get.return_value = agent_mock
    sim_mock.config_module.TICKS_PER_YEAR = 100

    # Run Observatory
    observatory = BubbleObservatory(sim_mock)
    metrics = observatory.collect_metrics()

    logger.info(f"Metrics: {metrics}")

    # Assertions
    assert metrics['tick'] == 10
    assert metrics['house_price_index'] == 150000.0
    assert metrics['new_mortgage_volume'] == 80000.0
    assert abs(metrics['average_ltv'] - 0.8) < 0.001
    assert metrics['average_dti'] > 0 # Some value

    # Check Log File
    if os.path.exists("logs/housing_bubble_monitor.csv"):
        logger.info("Log file created.")
        with open("logs/housing_bubble_monitor.csv", "r") as f:
            content = f.read()
            assert "150000.00" in content
            assert "80000.00" in content
    else:
        logger.error("Log file not created.")
        sys.exit(1)

    logger.info("VERIFICATION SUCCESSFUL: Bubble Observatory Verified.")

if __name__ == "__main__":
    verify_observatory()
