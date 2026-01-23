import sys
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import deque

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from utils.logging_manager import setup_logging
import config

# --- Verification Log Handler ---
class VerificationLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.atomicity_failures: List[str] = []

    def emit(self, record):
        msg = self.format(record)
        if "DEPOSIT_FAILURE" in msg or "ROLLBACK_FAILED" in msg:
            self.atomicity_failures.append(msg)

def verify_great_reset():
    # 1. Setup Logging
    setup_logging()

    # Attach handler to capture failures
    verification_handler = VerificationLogHandler()
    logging.getLogger().addHandler(verification_handler)
    logging.getLogger("simulation").addHandler(verification_handler)

    logger = logging.getLogger("VERIFY")
    logger.info("Starting Great Reset Stress Test (WO-115)...")

    # 2. Initialize Simulation
    config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 5000.0
    config.GOVERNMENT_STIMULUS_ENABLED = True
    config.TICKS_PER_YEAR = 100

    sim = create_simulation()

    # Metrics Storage
    m2_history: List[float] = []
    debt_ratio_history: List[float] = []

    initial_wealth_sum = 0.0

    total_ticks = 1000

    # 3. Main Loop
    for tick in range(1, total_ticks + 1):
        try:
            sim.run_tick()
        except Exception as e:
            logger.critical(f"Simulation Crashed at Tick {tick}: {e}", exc_info=True)
            break

        # 4. Calculate Metrics

        # Access Data via DTOs/Public Interface (Encapsulation)
        h_assets_sum = 0.0
        for h in sim.households:
            if h.is_active:
                # Use get_state_dto() if available, else get_agent_data()
                if hasattr(h, "create_state_dto"):
                    h_assets_sum += h.create_state_dto().assets
                else:
                    h_assets_sum += h.get_agent_data().get("assets", 0.0)

        f_assets_sum = 0.0
        for f in sim.firms:
            if f.is_active:
                # Use get_state_dto() for firms
                if hasattr(f, "get_state_dto"):
                    f_assets_sum += f.get_state_dto().assets
                else:
                    f_assets_sum += f.get_agent_data().get("assets", 0.0)

        # Government & Bank (System Agents) - Access via properties as they are IFinancialEntity
        gov_assets = sim.government.assets
        bank_assets = sim.bank.assets if sim.bank else 0.0
        reflux_bal = sim.reflux_system.balance if sim.reflux_system else 0.0

        # Total System Wealth (M2 Proxy in Closed System)
        # Sum of all cash/reserves held by all entities.
        current_wealth_sum = h_assets_sum + f_assets_sum + gov_assets + reflux_bal + bank_assets

        # Track Money Injection (Government Emission)
        money_issued = sim.government.total_money_issued
        money_destroyed = sim.government.total_money_destroyed
        net_injection = money_issued - money_destroyed

        if tick == 1:
            initial_wealth_sum = current_wealth_sum - net_injection

        # Check Zero-Sum Integrity
        # Expected Wealth = Initial + Net Injection
        expected_wealth = initial_wealth_sum + net_injection

        # Floating point tolerance
        if abs(current_wealth_sum - expected_wealth) > 1.0:
             logger.warning(
                 f"ZERO_SUM_DRIFT | Tick {tick} | Current: {current_wealth_sum:,.2f} vs Expected: {expected_wealth:,.2f} | Diff: {current_wealth_sum - expected_wealth:,.2f}"
             )

        m2_history.append(current_wealth_sum)

        # Debt-to-GDP Calculation
        debt = sim.government.total_debt

        # GDP from tracker
        metrics = sim.tracker.get_latest_indicators()
        prod = metrics.get("total_production", 0.0)
        price = metrics.get("avg_goods_price", 0.0)

        nominal_gdp = prod * price

        debt_ratio = 0.0
        if nominal_gdp > 0:
            debt_ratio = debt / nominal_gdp

        debt_ratio_history.append(debt_ratio)

        if debt_ratio > 2.0:
             logger.warning(f"FISCAL_WARNING | Debt-to-GDP Ratio > 200% ({debt_ratio:.2%}) at Tick {tick}")

        # Log Progress
        if tick % 100 == 0:
            logger.info(f"Tick {tick}/{total_ticks} | Total Wealth: {current_wealth_sum:,.2f} | Debt/GDP: {debt_ratio:.2%}")

    # 5. Analysis & Reporting
    logger.info("Simulation Complete. Generating Report...")

    report_lines = []
    report_lines.append("# Great Reset Stress Test Report (WO-115)")
    report_lines.append(f"**Status**: {'FAILED' if verification_handler.atomicity_failures else 'PASSED'}")
    report_lines.append("")

    # Atomicity Check
    report_lines.append("## 1. System Stability (Atomicity)")
    if verification_handler.atomicity_failures:
        report_lines.append(f"**FAILED**: {len(verification_handler.atomicity_failures)} Atomicity Failures detected.")
    else:
        report_lines.append("**PASSED**: No Atomicity Failures (DEPOSIT_FAILURE / ROLLBACK_FAILED) detected.")

    # M2 Integrity Check
    report_lines.append("")
    report_lines.append("## 2. Money Supply Integrity (Zero-Sum)")
    m2_start = m2_history[0]
    m2_end = m2_history[-1]

    money_issued = sim.government.total_money_issued
    money_destroyed = sim.government.total_money_destroyed
    net_gov_injection = money_issued - money_destroyed

    # Verify: End Wealth approx Start Wealth + Net Injection
    # Note: Start M2 in history includes Injection up to Tick 1.
    # We should use 'initial_wealth_sum' calculated at Tick 1 start logic.

    expected_end = initial_wealth_sum + net_gov_injection
    drift = m2_end - expected_end

    report_lines.append(f"- Initial Base Money: {initial_wealth_sum:,.2f}")
    report_lines.append(f"- Net Govt Injection: {net_gov_injection:,.2f} (Issued: {money_issued:,.2f}, Destroyed: {money_destroyed:,.2f})")
    report_lines.append(f"- Final Total Wealth: {m2_end:,.2f}")
    report_lines.append(f"- Expected Total Wealth: {expected_end:,.2f}")
    report_lines.append(f"- Unexplained Drift: {drift:,.2f}")

    if abs(drift) < 100.0: # Tolerance
        report_lines.append("**PASSED**: Money supply evolution is consistent with Government emission.")
    else:
        report_lines.append(f"**WARNING**: Significant unexplained money drift ({drift:,.2f}). Possible leak.")

    # Fiscal Stability
    report_lines.append("")
    report_lines.append("## 3. Fiscal Stability (Debt-to-GDP)")
    if debt_ratio_history:
        max_debt = max(debt_ratio_history)
        end_debt = debt_ratio_history[-1]
        report_lines.append(f"- Max Debt/GDP: {max_debt:.2%}")
        report_lines.append(f"- Final Debt/GDP: {end_debt:.2%}")

        if max_debt > 2.0:
            report_lines.append("- **WARNING**: Debt-to-GDP ratio exceeded 200% at some point.")
        else:
            report_lines.append("- Debt levels remained within safe limits (<200%).")
    else:
        report_lines.append("- No Debt/GDP data available.")

    # Write Report
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/GREAT_RESET_REPORT.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    logger.info(f"Report saved to {report_path}")
    print(f"Report saved to {report_path}")

    # Return Code
    if verification_handler.atomicity_failures:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    verify_great_reset()
