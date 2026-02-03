import logging
import csv
import os
from typing import List, Dict, Any, TYPE_CHECKING
from simulation.firms import Firm
from modules.finance.domain.corporate_finance import AltmanZScoreCalculator
from modules.analysis.api import CrisisDistributionDTO

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
        self._run_id = run_id
        self._log_file_initialized = False
        self._initialize_log_file()

    @property
    def run_id(self):
        return self._run_id

    @run_id.setter
    def run_id(self, value):
        """Update run_id and reinitialize log file if changed."""
        if self._run_id != value:
            self._run_id = value
            self._initialize_log_file()

    @property
    def log_file(self):
        return f"reports/crisis_monitor_{self._run_id}.csv"

    def _initialize_log_file(self):
        """Initialize or reinitialize the CSV log file."""
        # Ensure reports directory exists
        os.makedirs("reports", exist_ok=True)

        # Initialize CSV
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["tick", "safe_count", "gray_count", "distress_count", "total_active_firms", "survival_rate"])
        self._log_file_initialized = True

    def monitor(self, tick: int, firms: List['Firm']) -> CrisisDistributionDTO:
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

        return CrisisDistributionDTO(
            safe=safe_count,
            gray=gray_count,
            distress=distress_count,
            active=active_firms_count
        )

    def _calculate_z_score_for_firm(self, firm: 'Firm') -> float:
        """
        Helper to calculate Z-Score for a firm instance using the domain calculator.
        Uses the standardized financial snapshot from the Firm object.
        """
        snapshot = firm.get_financial_snapshot()

        return AltmanZScoreCalculator.calculate(
            total_assets=snapshot["total_assets"],
            working_capital=snapshot["working_capital"],
            retained_earnings=snapshot["retained_earnings"],
            average_profit=snapshot["average_profit"]
        )
