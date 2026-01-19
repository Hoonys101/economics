import logging
import csv
import os
from typing import List, Dict, Any, TYPE_CHECKING
from simulation.firms import Firm
from modules.finance.domain.corporate_finance import AltmanZScoreCalculator

if TYPE_CHECKING:
    from simulation.firms import Firm

class CrisisMonitor:
    """
    Monitors the financial health of firms and tracks the progression of a crisis.
    Categorizes firms based on Altman Z-Score:
        - Safe: Z > 2.99
        - Gray: 1.81 <= Z <= 2.99
        - Distress: Z < 1.81
    """

    def __init__(self, logger: logging.Logger, run_id: int):
        self.logger = logger
        self.run_id = run_id
        self.log_file = f"reports/crisis_monitor_{self.run_id}.csv"

        # Ensure reports directory exists
        os.makedirs("reports", exist_ok=True)

        # Initialize CSV
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["tick", "safe_count", "gray_count", "distress_count", "total_active_firms", "survival_rate"])

    def monitor(self, tick: int, firms: List['Firm']) -> Dict[str, int]:
        """
        Iterates through active firms, calculates Z-Score, and logs distribution.
        """
        safe_count = 0
        gray_count = 0
        distress_count = 0
        active_firms_count = 0

        for firm in firms:
            if not firm.is_active:
                continue

            active_firms_count += 1
            z_score = self._calculate_z_score_for_firm(firm)

            if z_score > 2.99:
                safe_count += 1
            elif z_score >= 1.81:
                gray_count += 1
            else:
                distress_count += 1

        total_firms = len(firms)
        survival_rate = (active_firms_count / total_firms) if total_firms > 0 else 0.0

        # Log to CSV
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([tick, safe_count, gray_count, distress_count, active_firms_count, survival_rate])

        # Log to console
        self.logger.info(
            f"CRISIS_MONITOR | Tick: {tick} | Safe: {safe_count}, Gray: {gray_count}, Distress: {distress_count} | Active: {active_firms_count}",
            extra={
                "tick": tick,
                "safe_count": safe_count,
                "gray_count": gray_count,
                "distress_count": distress_count,
                "tags": ["crisis_monitor"]
            }
        )

        return {
            "safe": safe_count,
            "gray": gray_count,
            "distress": distress_count,
            "active": active_firms_count
        }

    def _calculate_z_score_for_firm(self, firm: 'Firm') -> float:
        """
        Helper to calculate Z-Score for a firm instance using the domain calculator.
        """
        # Data extraction logic mapped to what AltmanZScoreCalculator.calculate expects

        # 1. Total Assets
        total_assets = firm.assets
        # Note: In some implementations, inventory value is added.
        # But `firm.assets` is usually cash.
        # If firm has `inventory` and `price`, we should add it.
        # Checking `Firm` implementation would be ideal, but for now using standard `assets`.
        # Assuming `assets` includes liquid assets.
        # If we have `inventory` count, we should value it.
        if hasattr(firm, "inventory") and hasattr(firm, "price"):
             # Handle dict inventory (common in this codebase)
             if isinstance(firm.inventory, dict):
                 inventory_qty = sum(firm.inventory.values())
                 total_assets += inventory_qty * firm.price
             else:
                 # Fallback if float/int
                 total_assets += firm.inventory * firm.price

        # 2. Working Capital = Current Assets - Current Liabilities
        current_assets = total_assets # Simplified if no long-term assets

        current_liabilities = 0.0
        if hasattr(firm, "total_debt"):
            current_liabilities = firm.total_debt

        working_capital = current_assets - current_liabilities

        # 3. Retained Earnings
        retained_earnings = 0.0
        if hasattr(firm, "retained_earnings"):
             retained_earnings = firm.retained_earnings
        elif hasattr(firm, "finance") and hasattr(firm.finance, "retained_earnings"):
             retained_earnings = firm.finance.retained_earnings

        # 4. Average Profit (EBIT)
        # We use a moving average if available, else current profit.
        average_profit = firm.current_profit
        if hasattr(firm, "profit_history") and len(firm.profit_history) > 0:
             # Take average of last 10 ticks?
             recent_profits = firm.profit_history[-10:]
             average_profit = sum(recent_profits) / len(recent_profits)

        return AltmanZScoreCalculator.calculate(
            total_assets=total_assets,
            working_capital=working_capital,
            retained_earnings=retained_earnings,
            average_profit=average_profit
        )
