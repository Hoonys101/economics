
import sys
import os
from unittest.mock import MagicMock
# Add project root to sys.path
sys.path.append(os.getcwd())

from simulation.firms import Firm
from modules.simulation.dtos.api import FirmConfigDTO

def test_firm_init():
    config = MagicMock(spec=FirmConfigDTO)
    config.bankruptcy_consecutive_loss_threshold = 20
    config.firm_min_production_target = 10.0
    config.ipo_initial_shares = 1000
    config.dividend_rate = 0.1
    config.profit_history_ticks = 10
    config.brand_resilience_factor = 0.05
    config.initial_firm_liquidity_need = 100.0
    config.automation_cost_per_pct = 1000.0
    config.capital_to_output_ratio = 1.0

    firm = Firm(
        id=1,
        initial_capital=1000.0,
        initial_liquidity_need=100.0,
        specialization="food",
        productivity_factor=1.0,
        decision_engine=MagicMock(),
        value_orientation="PROFIT",
        config_dto=config
    )

    if hasattr(firm, 'is_bankrupt'):
        print(f"Firm.is_bankrupt exists: {firm.is_bankrupt}")
    else:
        print("Firm.is_bankrupt DOES NOT EXIST")

if __name__ == "__main__":
    test_firm_init()
